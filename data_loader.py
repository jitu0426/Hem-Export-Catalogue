"""
HEM Product Catalogue - Data Loader Module
Excel loading, Cloudinary image matching, and cached data pipeline.
"""
import hashlib
import logging

import pandas as pd
import streamlit as st

from config import (
    CATALOGUE_PATHS, GLOBAL_COLUMN_MAPPING, REQUIRED_OUTPUT_COLS,
)
from cloudinary_client import (
    get_image_as_base64_str, fetch_all_cloudinary_resources,
)
from database import load_products_db

logger = logging.getLogger(__name__)


# =========================================================================
# Helper Functions
# =========================================================================

def generate_stable_product_id(catalogue, category, item_name, sku_code=""):
    """Generate a deterministic ProductID from stable attributes using MD5 hash.
    This ensures the same product always gets the same ID across reboots."""
    raw = f"{catalogue}|{category}|{item_name}|{sku_code}".strip().lower()
    return f"PID_{hashlib.md5(raw.encode()).hexdigest()[:12]}"


def clean_key(text):
    """Normalize text for fuzzy image key matching.
    Removes extensions, spaces, special chars, lowercases."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']:
        if text.endswith(ext):
            text = text[:-len(ext)]
    text = (text
            .replace('\u00a0', '')
            .replace(' ', '')
            .replace('_', '')
            .replace('-', '')
            .replace('/', '')
            .replace('\\', '')
            .replace('.', ''))
    return text


def create_safe_id(text):
    """Create a URL/HTML-safe ID from text."""
    return "".join(
        c for c in str(text).replace(' ', '-').lower()
        if c.isalnum() or c == '-'
    ).replace('--', '-')


# =========================================================================
# Main Data Loading Pipeline
# =========================================================================

@st.cache_data(show_spinner="Syncing Data (Smart Match v5 + Persistent DB)...")
def load_data_cached(_dummy_timestamp):
    """Load all product data from Excel files, Cloudinary images, and custom products.

    Uses Streamlit cache; pass a changing timestamp to bust the cache.
    The underscore prefix on _dummy_timestamp tells Streamlit not to hash it.
    """
    all_data = []
    required_output_cols = REQUIRED_OUTPUT_COLS

    # --- A. CLOUDINARY IMAGE INDEXING ---
    cloudinary_map = {}
    filename_map = {}
    debug_log = ["--- SYNC START ---"]

    try:
        resources = fetch_all_cloudinary_resources()
        for res in resources:
            public_id = res['public_id']
            url = res['secure_url']
            full_key = clean_key(public_id)
            cloudinary_map[full_key] = url
            f_name = public_id.split('/')[-1]
            file_key = clean_key(f_name)
            if file_key not in filename_map:
                filename_map[file_key] = url
    except Exception as e:
        st.warning(f"Cloudinary Warning: {e}")

    # --- B. LOAD PRODUCTS DATABASE ---
    db = load_products_db()
    overrides = db.get("product_overrides", {})
    deleted_pids = set(db.get("deleted_products", []))

    # --- C. EXCEL LOADING & MATCHING ---
    for catalogue_name, excel_path in CATALOGUE_PATHS.items():
        import os
        if not os.path.exists(excel_path):
            continue
        try:
            df = pd.read_excel(excel_path, sheet_name=0, dtype=str)
            df = df.fillna("")
            df.columns = [str(c).strip() for c in df.columns]
            df.rename(
                columns={
                    k.strip(): v
                    for k, v in GLOBAL_COLUMN_MAPPING.items()
                    if k.strip() in df.columns
                },
                inplace=True,
            )

            df['Catalogue'] = catalogue_name
            df['Packaging'] = 'Default Packaging'
            df["ImageB64"] = ""
            df['IsNew'] = (
                pd.to_numeric(df.get('IsNew', 0), errors='coerce')
                .fillna(0)
                .astype(int)
            )

            # DETERMINISTIC ProductID (stable across reboots)
            df["ProductID"] = df.apply(
                lambda row: generate_stable_product_id(
                    catalogue_name,
                    str(row.get('Category', '')),
                    str(row.get('ItemName', '')),
                    str(row.get('SKU Code', '')),
                ),
                axis=1,
            )

            for col in required_output_cols:
                if col not in df.columns:
                    df[col] = '' if col != 'IsNew' else 0

            # REMOVE DELETED PRODUCTS
            if deleted_pids:
                df = df[~df['ProductID'].isin(deleted_pids)]

            # APPLY PRODUCT OVERRIDES (sparse merge)
            if overrides:
                for pid, changes in overrides.items():
                    mask = df['ProductID'] == pid
                    if mask.any():
                        for field, value in changes.items():
                            if field in df.columns:
                                df.loc[mask, field] = value

            # CLOUDINARY IMAGE MATCHING
            if cloudinary_map:
                for index, row in df.iterrows():
                    cat = clean_key(str(row.get('Catalogue', '')))
                    category = clean_key(str(row.get('Category', '')))
                    item = clean_key(str(row.get('ItemName', '')))

                    found_url = None
                    match_type = "None"

                    key_1 = cat + category + item
                    key_2 = category + item
                    key_3 = item

                    if key_1 in cloudinary_map:
                        found_url = cloudinary_map[key_1]
                        match_type = "Exact Path"
                    elif key_2 in cloudinary_map:
                        found_url = cloudinary_map[key_2]
                        match_type = "Category Path"
                    elif key_3 in filename_map:
                        found_url = filename_map[key_3]
                        match_type = "Exact Filename"

                    if not found_url:
                        for c_key, c_url in filename_map.items():
                            if len(c_key) < 4:
                                continue
                            if item.startswith(c_key):
                                found_url = c_url
                                match_type = f"Partial: Item starts with '{c_key}'"
                                break
                            if c_key.startswith(item):
                                found_url = c_url
                                match_type = f"Partial: File starts with '{item}'"
                                break

                    if "soham" in item or "bayleaf" in item:
                        debug_log.append(
                            f"Product: {row.get('ItemName')} | "
                            f"Found: {found_url is not None} | Type: {match_type}"
                        )

                    if found_url:
                        optimized_url = found_url.replace(
                            "/upload/", "/upload/w_800,q_auto/"
                        )
                        df.loc[index, "ImageB64"] = get_image_as_base64_str(
                            optimized_url, max_size=None
                        )

            all_data.append(df[required_output_cols])
        except Exception as e:
            st.error(f"Error reading Excel {catalogue_name}: {e}")
            logger.error(f"Error reading Excel {catalogue_name}: {e}")

    # --- D. CUSTOM PRODUCTS FROM DATABASE ---
    custom_items = db.get("custom_products", [])
    if custom_items:
        custom_df = pd.DataFrame(custom_items)
        for col in required_output_cols:
            if col not in custom_df.columns:
                custom_df[col] = '' if col != 'IsNew' else 0

        for idx, row in custom_df.iterrows():
            if str(row['ImageB64']).startswith('http'):
                custom_df.at[idx, 'ImageB64'] = get_image_as_base64_str(
                    row['ImageB64']
                )

        all_data.append(custom_df[required_output_cols])

    st.session_state['debug_logs'] = debug_log
    if not all_data:
        return pd.DataFrame(columns=required_output_cols)
    return pd.concat(all_data, ignore_index=True)
