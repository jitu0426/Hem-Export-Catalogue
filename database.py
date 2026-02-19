"""
HEM Product Catalogue - Database Module
Persistent JSON database with session-state caching.
Eliminates redundant disk reads (15+ per render -> 1).
"""
import os
import json
import uuid
import logging
from datetime import datetime

import streamlit as st

from config import PRODUCTS_DB_FILE, CUSTOM_ITEMS_FILE, SAVED_TEMPLATES_FILE
from cloudinary_client import (
    download_db_from_cloudinary, upload_db_to_cloudinary,
    download_templates_from_cloudinary, upload_templates_to_cloudinary,
    upload_custom_image,
)

logger = logging.getLogger(__name__)

# =========================================================================
# Database Schema
# =========================================================================

def get_empty_products_db():
    """Return the default empty database structure."""
    return {
        "version": 1,
        "last_updated": "",
        "product_overrides": {},
        "custom_products": [],
        "deleted_products": [],
        "saved_cart": [],
    }


# =========================================================================
# Core Load / Save with Session-State Caching
# =========================================================================

_DB_CACHE_KEY = "_products_db_cache"


def _load_from_disk_or_cloud():
    """Load DB from disk, falling back to Cloudinary, then empty default."""
    # Try local file first
    if os.path.exists(PRODUCTS_DB_FILE):
        try:
            with open(PRODUCTS_DB_FILE, 'r') as f:
                db = json.load(f)
            # Schema migration: ensure all keys exist
            default = get_empty_products_db()
            for key in default:
                if key not in db:
                    db[key] = default[key]
            logger.info("Database loaded from local file")
            return db
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load local DB: {e}")

    # Fallback: try Cloudinary backup
    cloud_db = download_db_from_cloudinary()
    if cloud_db:
        _write_to_disk(cloud_db)
        logger.info("Database restored from Cloudinary backup")
        return cloud_db

    logger.info("Starting with empty database")
    return get_empty_products_db()


def _write_to_disk(db):
    """Write DB to local disk."""
    data_dir = os.path.dirname(PRODUCTS_DB_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    with open(PRODUCTS_DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)


def load_products_db():
    """Load the products database using session-state cache.
    Only reads from disk on the first call per session."""
    if _DB_CACHE_KEY not in st.session_state:
        st.session_state[_DB_CACHE_KEY] = _load_from_disk_or_cloud()
    return st.session_state[_DB_CACHE_KEY]


def save_products_db(db):
    """Save the products database to disk + Cloudinary, update cache."""
    db["last_updated"] = datetime.now().isoformat()
    try:
        _write_to_disk(db)
        upload_db_to_cloudinary(db)
        # Update the in-memory cache
        st.session_state[_DB_CACHE_KEY] = db
    except Exception as e:
        logger.error(f"Failed to save products database: {e}")
        st.error(f"Failed to save products database: {e}")


def invalidate_db_cache():
    """Force reload from disk on next access."""
    if _DB_CACHE_KEY in st.session_state:
        del st.session_state[_DB_CACHE_KEY]


# =========================================================================
# Product Override Operations
# =========================================================================

def save_product_override(product_id, field_changes):
    """Save field-level overrides for a product."""
    db = load_products_db()
    if product_id not in db["product_overrides"]:
        db["product_overrides"][product_id] = {}
    db["product_overrides"][product_id].update(field_changes)
    save_products_db(db)


def remove_product_override(product_id, field_name=None):
    """Remove override for a product (or a specific field)."""
    db = load_products_db()
    if product_id in db["product_overrides"]:
        if field_name:
            db["product_overrides"][product_id].pop(field_name, None)
            if not db["product_overrides"][product_id]:
                del db["product_overrides"][product_id]
        else:
            del db["product_overrides"][product_id]
    save_products_db(db)


# =========================================================================
# Product Delete / Hide Operations
# =========================================================================

def mark_product_deleted(product_id):
    """Mark an Excel product as hidden/deleted."""
    db = load_products_db()
    if product_id not in db["deleted_products"]:
        db["deleted_products"].append(product_id)
    save_products_db(db)


def unmark_product_deleted(product_id):
    """Restore a previously hidden product."""
    db = load_products_db()
    db["deleted_products"] = [pid for pid in db["deleted_products"] if pid != product_id]
    save_products_db(db)


# =========================================================================
# Custom Products
# =========================================================================

def add_custom_product_to_db(product_data):
    """Add a custom product to the database."""
    db = load_products_db()
    db["custom_products"].append(product_data)
    save_products_db(db)


def delete_custom_product_from_db(product_id):
    """Remove a custom product from the database."""
    db = load_products_db()
    db["custom_products"] = [
        p for p in db["custom_products"] if p.get("ProductID") != product_id
    ]
    save_products_db(db)


def get_custom_products_from_db():
    """Get all custom products from the database."""
    db = load_products_db()
    return db.get("custom_products", [])


def add_custom_item(catalogue, category, subcategory, item_name,
                    fragrance, sku_code, is_new, image_file):
    """Create and persist a new custom product."""
    img_url = ""
    if image_file:
        img_url = upload_custom_image(image_file)

    new_item = {
        "ProductID": f"CUST_{uuid.uuid4().hex[:8]}",
        "Catalogue": catalogue,
        "Category": category,
        "Subcategory": subcategory if subcategory else "N/A",
        "ItemName": item_name,
        "Fragrance": fragrance,
        "SKU Code": sku_code,
        "IsNew": 1 if is_new else 0,
        "ImageB64": img_url,
        "Packaging": "Default",
        "SerialNo": 0,
    }
    add_custom_product_to_db(new_item)
    return new_item


def delete_custom_item(pid):
    """Delete a custom product by ProductID."""
    delete_custom_product_from_db(pid)


# =========================================================================
# Cart Persistence
# =========================================================================

def save_cart_to_db(cart_items):
    """Persist cart to the JSON database."""
    db = load_products_db()
    db["saved_cart"] = cart_items
    save_products_db(db)


def load_cart_from_db():
    """Load persisted cart from the JSON database."""
    db = load_products_db()
    return db.get("saved_cart", [])


# =========================================================================
# Template Management
# =========================================================================

def load_saved_templates():
    """Load saved cart templates from disk or Cloudinary."""
    if os.path.exists(SAVED_TEMPLATES_FILE):
        try:
            with open(SAVED_TEMPLATES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load local templates: {e}")

    cloud_templates = download_templates_from_cloudinary()
    if cloud_templates:
        try:
            with open(SAVED_TEMPLATES_FILE, 'w') as f:
                json.dump(cloud_templates, f, indent=4)
        except OSError:
            pass
        return cloud_templates
    return {}


def save_template_to_disk(name, cart_items):
    """Save a named template and backup to Cloudinary."""
    templates = load_saved_templates()
    templates[name] = cart_items
    try:
        with open(SAVED_TEMPLATES_FILE, 'w') as f:
            json.dump(templates, f, indent=4)
        upload_templates_to_cloudinary()
        st.toast(f"Template '{name}' saved!", icon="\U0001f4be")
    except Exception as e:
        logger.error(f"Failed to save template: {e}")
        st.error(f"Failed to save template: {e}")


def delete_template(name):
    """Delete a saved template by name."""
    templates = load_saved_templates()
    if name in templates:
        del templates[name]
        try:
            with open(SAVED_TEMPLATES_FILE, 'w') as f:
                json.dump(templates, f, indent=4)
            upload_templates_to_cloudinary()
            st.toast(f"Template '{name}' deleted!", icon="\U0001f5d1\ufe0f")
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")


# =========================================================================
# Migration
# =========================================================================

def migrate_old_custom_items():
    """One-time migration from old custom_products.json to new products_db.json."""
    if not os.path.exists(CUSTOM_ITEMS_FILE):
        return False
    db = load_products_db()
    if db["custom_products"]:
        return False
    try:
        with open(CUSTOM_ITEMS_FILE, 'r') as f:
            old_items = json.load(f)
        if old_items:
            db["custom_products"] = old_items
            save_products_db(db)
            os.rename(CUSTOM_ITEMS_FILE, CUSTOM_ITEMS_FILE + ".migrated.bak")
            logger.info(f"Migrated {len(old_items)} custom items from legacy file")
            return True
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Migration failed: {e}")
    return False
