"""
HEM Product Catalogue v3 — Tab 2: Review & Edit Cart
Inline editing, change detection, per-row removal, and cart clear.
"""
import time
import pandas as pd
import streamlit as st

from database import load_products_db, save_product_override, save_cart_to_db
from cart import remove_from_cart, clear_cart
from ui.components import section_header, stats_bar, confirm_action, empty_state, gold_divider


def render_review_tab() -> None:
    """Render Tab 2 — Review & Edit Cart."""
    section_header("Review & Edit Cart", icon="✏️")

    if not st.session_state.cart:
        empty_state("🛒", "Your cart is empty. Go to <strong>Filter Products</strong> to add items.")
        return

    cart_df = pd.DataFrame(st.session_state.cart)

    # ── In-cart search ────────────────────────────────────────────────────
    search = st.text_input(
        "🔍 Find in cart…",
        placeholder="Type product name",
        key="cart_search_input",
    ).strip().lower()
    if search:
        cart_df = cart_df[
            cart_df["ItemName"].str.lower().str.contains(search, na=False)
        ]

    # ── Load DB for status badges ─────────────────────────────────────────
    db              = load_products_db()
    overridden_pids = set(db.get("product_overrides", {}).keys())

    def _status(pid):
        parts = []
        if pid in overridden_pids:
            parts.append("Edited")
        if str(pid).startswith("CUST_"):
            parts.append("Custom")
        return ", ".join(parts)

    cart_df["Status"] = cart_df["ProductID"].apply(_status)
    cart_df["Remove"] = False

    # ── Stats bar ─────────────────────────────────────────────────────────
    edited_count = sum(1 for p in cart_df["ProductID"] if p in overridden_pids)
    custom_count = sum(1 for p in cart_df["ProductID"] if str(p).startswith("CUST_"))
    stats_bar([
        ("Total Items",  str(len(cart_df))),
        ("Edited",       str(edited_count)),
        ("Custom",       str(custom_count)),
    ])

    # ── Editable data table ───────────────────────────────────────────────
    display_cols = [
        "Catalogue", "Category", "Subcategory", "ItemName",
        "Fragrance", "SKU Code", "Status", "Remove",
    ]
    for col in display_cols:
        if col not in cart_df.columns:
            cart_df[col] = ""

    edited_df = st.data_editor(
        cart_df[display_cols],
        column_config={
            "Remove":     st.column_config.CheckboxColumn("Remove?",      default=False, width="small"),
            "Catalogue":  st.column_config.TextColumn("Catalogue",        width="medium"),
            "Category":   st.column_config.TextColumn("Category",         width="medium"),
            "Subcategory":st.column_config.TextColumn("Sub-Category",     width="medium"),
            "ItemName":   st.column_config.TextColumn("Product Name",     width="large"),
            "Fragrance":  st.column_config.TextColumn("Fragrance",        width="medium"),
            "SKU Code":   st.column_config.TextColumn("SKU Code",         width="medium"),
            "Status":     st.column_config.TextColumn("Status",           width="small", disabled=True),
        },
        hide_index=True,
        key="cart_editor_v3",
        use_container_width=True,
        num_rows="fixed",
    )

    # ── Detect field changes ──────────────────────────────────────────────
    editable_fields = ["Catalogue", "Category", "Subcategory", "ItemName", "Fragrance", "SKU Code"]
    changes: dict = {}
    for i in range(min(len(cart_df), len(edited_df))):
        pid          = cart_df.iloc[i]["ProductID"]
        field_delta  = {}
        for f in editable_fields:
            orig = str(cart_df.iloc[i].get(f, "")).strip()
            edit = str(edited_df.iloc[i].get(f, "")).strip()
            if orig != edit:
                field_delta[f] = edit
        if field_delta:
            changes[pid] = field_delta

    gold_divider()

    # ── Action buttons ────────────────────────────────────────────────────
    col_save, col_remove, col_clear = st.columns(3)

    with col_save:
        btn_lbl   = f"💾 Save {len(changes)} Edit(s)" if changes else "No Changes"
        if st.button(btn_lbl, disabled=not changes,
                     use_container_width=True, type="primary"):
            for pid, delta in changes.items():
                save_product_override(pid, delta)
                for item in st.session_state.cart:
                    if item.get("ProductID") == pid:
                        item.update(delta)
            save_cart_to_db(st.session_state.cart)
            st.session_state.data_timestamp = time.time()
            st.cache_data.clear()
            st.toast(f"Saved {len(changes)} edit(s)!", icon="✅")
            st.rerun()

    with col_remove:
        to_remove_idx  = edited_df[edited_df["Remove"] == True].index.tolist()
        pids_to_remove = (
            cart_df.loc[to_remove_idx, "ProductID"].tolist()
            if to_remove_idx else []
        )
        if st.button(
            f"🗑 Remove {len(pids_to_remove)} Selected",
            disabled=not pids_to_remove,
            use_container_width=True,
        ):
            remove_from_cart(pids_to_remove)
            st.rerun()

    with col_clear:
        if confirm_action(
            "clear_cart_v3",
            "🗑 Clear All Cart",
            "Remove ALL items from the cart? This cannot be undone.",
            danger=True,
        ):
            clear_cart()
            st.rerun()

    # ── Change preview panel ──────────────────────────────────────────────
    if changes:
        gold_divider()
        with st.expander(f"👁 Preview {len(changes)} Pending Edit(s)", expanded=True):
            for pid, delta in changes.items():
                orig_row  = cart_df[cart_df["ProductID"] == pid]
                orig_name = orig_row.iloc[0]["ItemName"] if not orig_row.empty else pid
                change_str = " · ".join(
                    f"**{k}** → `{v}`" for k, v in delta.items()
                )
                st.markdown(f"▸ **{orig_name}** — {change_str}")
            st.info("Click **Save Edit(s)** above to permanently save these changes.")
