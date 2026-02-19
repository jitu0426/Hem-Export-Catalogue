"""
HEM Product Catalogue v3 — Tab 3: Export
PDF catalogue + Excel order sheet generation with case-size selection.
"""
import os
import json
import logging

import pandas as pd
import streamlit as st

from config import BASE_DIR, LOGO_PATH, CASE_SIZE_PATH
from cloudinary_client import get_image_as_base64_str
from data_loader import load_data_cached
from pdf_generator import generate_pdf_html, generate_excel_file, render_pdf
from ui.components import section_header, gold_divider, empty_state

logger = logging.getLogger(__name__)


def render_export_tab(products_df: pd.DataFrame) -> None:
    """Render Tab 3 — Export Catalogue."""
    section_header("Export Catalogue", icon="📄")

    if not st.session_state.cart:
        empty_state("📄", "Cart is empty. Add products in <strong>Filter Products</strong> first.")
        return

    # ── 1. Case size selection per category ───────────────────────────────
    st.markdown(
        '<div style="font-size:13px;color:#a0a0c0;margin-bottom:12px;">'
        '◆ Select the carton/case size for each product category in your cart.'
        '</div>',
        unsafe_allow_html=True,
    )

    cart_categories = sorted({item["Category"] for item in st.session_state.cart})

    # Load case-size data (from local DB first, then GitHub Excel)
    full_case_df = pd.DataFrame()
    local_db     = os.path.join(BASE_DIR, "data", "database.json")
    if os.path.exists(local_db):
        try:
            with open(local_db) as f:
                raw = json.load(f)
            if raw.get("case_sizes"):
                full_case_df = pd.DataFrame(raw["case_sizes"])
        except Exception:
            pass

    if full_case_df.empty:
        try:
            full_case_df = pd.read_excel(CASE_SIZE_PATH, dtype=str)
            full_case_df.columns = [c.strip() for c in full_case_df.columns]
        except Exception as e:
            st.error(f"Could not load Case Size data: {e}")

    selection_map: dict = {}

    if not full_case_df.empty:
        suffix_col = next(
            (c for c in full_case_df.columns if "suffix" in c.lower()), None
        )
        cbm_col = next(
            (c for c in full_case_df.columns if "cbm" in c.lower()), "CBM"
        )

        if not suffix_col:
            st.error(
                f"Cannot find 'Carton Suffix' column in Case Size file. "
                f"Available columns: {full_case_df.columns.tolist()}"
            )
        else:
            cols_per_row = 2
            cat_chunks   = [
                cart_categories[i:i+cols_per_row]
                for i in range(0, len(cart_categories), cols_per_row)
            ]
            for chunk in cat_chunks:
                cols = st.columns(len(chunk))
                for col, cat in zip(cols, chunk):
                    with col:
                        options = full_case_df[
                            full_case_df["Category"] == cat
                        ].copy()
                        if not options.empty:
                            options["_label"] = options.apply(
                                lambda x: (
                                    f"{x.get(suffix_col, '').strip()} "
                                    f"(CBM: {x.get(cbm_col, '')})"
                                ),
                                axis=1,
                            )
                            chosen = st.selectbox(
                                f"📦 **{cat}**",
                                options["_label"].tolist(),
                                key=f"case_{cat}",
                            )
                            selection_map[cat] = options[
                                options["_label"] == chosen
                            ].iloc[0].to_dict()
                        else:
                            st.warning(f"No case sizes for: {cat}")

    gold_divider()

    # ── 2. Client name ────────────────────────────────────────────────────
    client_name = st.text_input(
        "👤 Client Name",
        value="Valued Client",
        key="export_client_name",
    )

    # ── 3. Generate button ────────────────────────────────────────────────
    if st.button(
        "🚀 Generate Catalogue & Order Sheet",
        use_container_width=True,
        type="primary",
    ):
        _generate_files(products_df, client_name, selection_map)

    gold_divider()

    # ── 4. Download buttons ───────────────────────────────────────────────
    if st.session_state.gen_pdf_bytes or st.session_state.gen_excel_bytes:
        st.markdown(
            '<div style="font-size:13px;color:#c9a84c;margin-bottom:10px;'
            'letter-spacing:1px;text-transform:uppercase;">◆ Ready to Download</div>',
            unsafe_allow_html=True,
        )
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            if st.session_state.gen_pdf_bytes:
                safe_name = client_name.replace(" ", "_")
                st.download_button(
                    "⬇️ Download PDF Catalogue",
                    data=st.session_state.gen_pdf_bytes,
                    file_name=f"{safe_name}_catalogue.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        with dl_col2:
            if st.session_state.gen_excel_bytes:
                safe_name = client_name.replace(" ", "_")
                st.download_button(
                    "⬇️ Download Excel Order Sheet",
                    data=st.session_state.gen_excel_bytes,
                    file_name=f"{safe_name}_order.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )


def _generate_files(products_df, client_name, selection_map):
    """Internal helper: build and store PDF + Excel in session state."""
    cart_data   = st.session_state.cart
    schema_cols = [
        "Catalogue", "Category", "Subcategory", "ItemName",
        "Fragrance", "SKU Code", "ImageB64", "Packaging", "IsNew",
    ]
    df = pd.DataFrame(cart_data)
    for col in schema_cols:
        if col not in df.columns:
            df[col] = ""

    # Sort products in the same order as original Excel catalogues
    fresh_df     = load_data_cached(st.session_state.data_timestamp)
    pid_to_order = {row["ProductID"]: i for i, row in fresh_df.iterrows()}
    if "ProductID" in df.columns:
        df["_order"] = df["ProductID"].map(pid_to_order).fillna(len(fresh_df))
        df = df.sort_values("_order").drop(columns=["_order"])

    df["SerialNo"] = range(1, len(df) + 1)

    progress = st.progress(0, text="Starting…")

    # Generate Excel
    progress.progress(20, text="Building Excel order sheet…")
    try:
        st.session_state.gen_excel_bytes = generate_excel_file(df, client_name, selection_map)
    except Exception as e:
        st.error(f"Excel generation failed: {e}")
        st.session_state.gen_excel_bytes = None

    # Generate PDF
    progress.progress(50, text="Rendering PDF (this may take 30–60 seconds)…")
    try:
        logo_b64 = get_image_as_base64_str(LOGO_PATH, resize=True, max_size=(200, 100))
        html     = generate_pdf_html(df, client_name, logo_b64, selection_map)
        progress.progress(80, text="Finalising PDF…")
        pdf_bytes, engine_or_err = render_pdf(html)
        if pdf_bytes:
            st.session_state.gen_pdf_bytes = pdf_bytes
            progress.progress(100, text="Done!")
            st.toast(f"✅ PDF ready ({engine_or_err})", icon="🎉")
        else:
            st.session_state.gen_pdf_bytes = None
            progress.empty()
            st.error(f"PDF generation failed:\n\n{engine_or_err}")
    except Exception as e:
        logger.error(f"PDF exception: {e}")
        st.session_state.gen_pdf_bytes = None
        progress.empty()
        st.error(f"PDF error: {e}")
