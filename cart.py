"""
HEM Product Catalogue - Cart Module
Shopping cart operations with duplicate detection.
"""
import logging

import pandas as pd
import streamlit as st

from config import CART_COLUMNS, NO_SELECTION_PLACEHOLDER
from database import save_cart_to_db

logger = logging.getLogger(__name__)


def add_to_cart(selected_df):
    """Add products to cart from a DataFrame. Skips duplicates with a toast."""
    current_pids = {item["ProductID"] for item in st.session_state.cart}
    new_items = []
    duplicate_count = 0

    if isinstance(selected_df, pd.Series):
        selected_df = pd.DataFrame([selected_df])

    for _, row in selected_df.iterrows():
        pid = row.get("ProductID")
        if pid and pid not in current_pids:
            new_items.append({col: row.get(col, '') for col in CART_COLUMNS})
            current_pids.add(pid)  # Prevent duplicates within same batch
        elif pid in current_pids:
            duplicate_count += 1

    if new_items:
        st.session_state.cart.extend(new_items)
        st.session_state.gen_pdf_bytes = None
        st.session_state.gen_excel_bytes = None
        save_cart_to_db(st.session_state.cart)
        st.toast(f"Added {len(new_items)} items to cart!", icon="\U0001f6d2")

    if duplicate_count > 0:
        st.toast(
            f"{duplicate_count} item(s) already in cart, skipped.",
            icon="\u2139\ufe0f",
        )


def remove_from_cart(pids_to_remove):
    """Remove products from cart by ProductID set."""
    if pids_to_remove:
        pids_set = set(pids_to_remove) if not isinstance(pids_to_remove, set) else pids_to_remove
        st.session_state.cart = [
            i for i in st.session_state.cart
            if i.get("ProductID") not in pids_set
        ]
    st.session_state.gen_pdf_bytes = None
    st.session_state.gen_excel_bytes = None
    save_cart_to_db(st.session_state.cart)


def clear_cart():
    """Remove all items from cart."""
    st.session_state.cart = []
    st.session_state.gen_pdf_bytes = None
    st.session_state.gen_excel_bytes = None
    save_cart_to_db([])


def add_selected_visible_to_cart(df_visible):
    """Add only the checkbox-selected products that are currently visible."""
    pid_map = st.session_state.get('master_pid_map', {})
    visible_pids = set(df_visible['ProductID'].tolist())
    current_cart_pids = {
        item["ProductID"] for item in st.session_state.cart if "ProductID" in item
    }

    new_items = []
    duplicate_count = 0

    for key, is_checked in st.session_state.items():
        if key.startswith("checkbox_") and is_checked:
            pid = key.replace("checkbox_", "")
            if pid not in visible_pids:
                continue
            if pid in current_cart_pids:
                duplicate_count += 1
                continue
            product_data = pid_map.get(pid)
            if product_data:
                row_series = pd.Series(product_data)
                new_items.append(
                    {col: row_series.get(col, '') for col in CART_COLUMNS}
                )

    if new_items:
        st.session_state.cart.extend(new_items)
        st.session_state.gen_pdf_bytes = None
        st.session_state.gen_excel_bytes = None
        save_cart_to_db(st.session_state.cart)
        st.toast(f"Added {len(new_items)} selected items to cart!", icon="\U0001f6d2")
    else:
        st.toast("No new items selected.", icon="\u2139\ufe0f")

    if duplicate_count > 0:
        st.toast(
            f"{duplicate_count} item(s) already in cart, skipped.",
            icon="\u2139\ufe0f",
        )


def clear_filters_dropdown():
    """Reset all filter-related session state."""
    st.session_state.selected_catalogue_dropdown = NO_SELECTION_PLACEHOLDER
    st.session_state.selected_categories_multi = []
    st.session_state.selected_subcategories_multi = []
    st.session_state.item_search_query = ""
    for key in ["item_search_input", "category_multiselect", "subcategory_multiselect"]:
        if key in st.session_state:
            del st.session_state[key]
