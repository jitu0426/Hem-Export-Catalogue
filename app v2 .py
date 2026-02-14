import streamlit as st
import os
import sys
import gc
import hashlib

# --- SAFETY BOOT: CATCH CRASHES & SHOW ON SCREEN ---
try:
    import pandas as pd
    import pdfkit
    import base64
    from pathlib import Path
    from datetime import datetime
    import io
    import json
    import numpy as np
    import time
    import uuid
    import difflib
    from fuzzywuzzy import fuzz
    from PIL import Image
    import platform
    import subprocess
    import cloudinary
    import cloudinary.api
    import cloudinary.uploader
    import requests

    # --- 1. SAFE IMPORT LOGIC ---
    HAS_WEASYPRINT = False
    try:
        from weasyprint import HTML, CSS
        HAS_WEASYPRINT = True
    except Exception as e:
        print(f"WeasyPrint import warning: {e}")
        HAS_WEASYPRINT = False

    # --- 2. CLOUDINARY CONFIG ---
    cloudinary.config(
        cloud_name="dnoepbfbr",
        api_key="393756212248257",
        api_secret="66zA0Je4c0SKqaDcbCglsxPpYGI",
        secure=True
    )

    # --- 3. HELPER FUNCTIONS ---

    def generate_stable_product_id(catalogue, category, item_name, sku_code=""):
        """Generate a deterministic ProductID from stable attributes using MD5 hash.
        This ensures the same product always gets the same ID across reboots."""
        raw = f"{catalogue}|{category}|{item_name}|{sku_code}".strip().lower()
        return f"PID_{hashlib.md5(raw.encode()).hexdigest()[:12]}"

    def clean_key(text):
        if not isinstance(text, str):
            return ""
        text = text.lower().strip()
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff']:
            if text.endswith(ext):
                text = text[:-len(ext)]
        text = text.replace('\u00a0', '').replace(' ', '').replace('_', '').replace('-', '').replace('/', '').replace('\\', '').replace('.', '')
        return text

    def get_image_as_base64_str(url_or_path, resize=None, max_size=None):
        if not url_or_path:
            return ""
        try:
            img = None
            if str(url_or_path).startswith("http"):
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url_or_path, headers=headers, timeout=5)
                if response.status_code != 200:
                    return ""
                img = Image.open(io.BytesIO(response.content))
            else:
                if not os.path.exists(url_or_path):
                    return ""
                img = Image.open(url_or_path)
            if max_size:
                img.thumbnail(max_size)
            elif resize:
                img = img.resize(resize)
            buffered = io.BytesIO()
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buffered, format="JPEG", quality=85)
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            print(f"Error processing image {url_or_path}: {e}")
            return ""

    def create_safe_id(text):
        return "".join(c for c in str(text).replace(' ', '-').lower() if c.isalnum() or c == '-').replace('--', '-')

    def force_light_theme_setup():
        config_dir = ".streamlit"
        config_path = os.path.join(config_dir, "config.toml")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        if not os.path.exists(config_path):
            theme_content = "[theme]\nbase='light'\nprimaryColor='#007bff'\nbackgroundColor='#ffffff'\nsecondaryBackgroundColor='#f0f2f6'\ntextColor='#000000'\nfont='sans serif'"
            with open(config_path, "w") as f:
                f.write(theme_content.strip())

    # --- 4. APP SETUP ---
    force_light_theme_setup()
    st.set_page_config(page_title="HEM PRODUCT CATALOGUE", page_icon="🛍️", layout="wide")

    # --- ENHANCED CSS (App UI only - PDF CSS is separate and unchanged) ---
    st.markdown("""
        <style>
        /* ===== GLOBAL APP STYLES ===== */
        .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
        }

        /* ===== HEADER / TITLE ===== */
        .main-title {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white !important;
            padding: 20px 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 1px;
            border-bottom: 4px solid #ff9800;
        }

        /* ===== TAB NAVIGATION ===== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: #f0f2f6;
            padding: 6px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            color: #555;
            background-color: transparent;
            border: none;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1a1a2e !important;
            color: white !important;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(26,26,46,0.3);
        }

        /* ===== BUTTON STYLES ===== */
        button[kind="primary"] {
            background-color: #ff9800 !important;
            color: white !important;
            border: none;
            font-weight: bold;
            border-radius: 8px;
            transition: all 0.2s ease;
            padding: 8px 16px;
        }
        button[kind="primary"]:hover {
            background-color: #f57c00 !important;
            box-shadow: 0 4px 12px rgba(255,152,0,0.4);
            transform: translateY(-1px);
        }
        button[kind="secondary"] {
            background-color: #007bff !important;
            color: white !important;
            border: none;
            font-weight: bold;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        button[kind="secondary"]:hover {
            background-color: #0056b3 !important;
            box-shadow: 0 4px 12px rgba(0,123,255,0.3);
        }

        /* ===== DATA EDITOR / TABLE ===== */
        div[data-testid="stDataEditor"] {
            background-color: #ffffff !important;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        /* ===== FILTER PANEL ===== */
        .stSelectbox > div > div {
            border-radius: 8px;
        }
        .stMultiSelect > div > div {
            border-radius: 8px;
        }

        /* ===== EXPANDER (Category groups) ===== */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 8px;
            font-weight: 600;
            color: #1a1a2e;
        }
        .streamlit-expanderContent {
            border-left: 3px solid #007bff;
            padding-left: 15px;
        }

        /* ===== SUBCATEGORY HEADER ===== */
        .subcat-header {
            background-color: #e8f4fd;
            padding: 8px 14px;
            margin: 12px 0 6px 0;
            border-left: 4px solid #007bff;
            font-weight: bold;
            color: #1a1a2e;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
        }

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {
            background-color: #1a1a2e;
        }
        section[data-testid="stSidebar"] .stMarkdown {
            color: #e0e0e0;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #ff9800 !important;
        }
        section[data-testid="stSidebar"] button {
            background-color: #ff9800 !important;
            color: #1a1a2e !important;
            font-weight: bold;
            border-radius: 8px;
        }
        section[data-testid="stSidebar"] .stTextInput input {
            background-color: #2a2a4e;
            color: white;
            border-color: #ff9800;
            border-radius: 6px;
        }

        /* ===== PRODUCT STATS BAR ===== */
        .stats-bar {
            background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
            padding: 10px 20px;
            border-radius: 10px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #d0e4f5;
        }
        .stats-bar .stat-item {
            font-size: 14px;
            color: #333;
        }
        .stats-bar .stat-value {
            font-weight: 700;
            color: #1a1a2e;
        }

        /* ===== STATUS BADGES ===== */
        .badge-modified {
            display: inline-block;
            background-color: #fff3cd;
            color: #856404;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 12px;
            border: 1px solid #ffc107;
            margin-left: 6px;
        }
        .badge-custom {
            display: inline-block;
            background-color: #d4edda;
            color: #155724;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 12px;
            border: 1px solid #28a745;
            margin-left: 6px;
        }
        .badge-new {
            display: inline-block;
            background-color: #f8d7da;
            color: #721c24;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 12px;
            border: 1px solid #dc3545;
            margin-left: 6px;
        }

        /* ===== SECTION HEADERS ===== */
        .section-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #2d2d5e 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            margin: 15px 0 10px 0;
            font-size: 18px;
            font-weight: 600;
            border-left: 5px solid #ff9800;
        }

        /* ===== FORM STYLING ===== */
        .stForm {
            background-color: #fafbfc;
            border: 1px solid #e1e4e8;
            border-radius: 12px;
            padding: 20px;
        }

        /* ===== CARD GRID FOR CUSTOM PRODUCTS ===== */
        .custom-product-card {
            background: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 12px 16px;
            margin: 6px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            transition: box-shadow 0.2s;
        }
        .custom-product-card:hover {
            box-shadow: 0 3px 10px rgba(0,0,0,0.12);
        }

        /* ===== INFO BOXES ===== */
        .stAlert {
            border-radius: 10px;
        }

        /* ===== DIVIDERS ===== */
        hr {
            border: none;
            border-top: 2px solid #f0f2f6;
            margin: 15px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 5. PATHS ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
    SAVED_TEMPLATES_FILE = os.path.join(BASE_DIR, "saved_templates.json")
    CUSTOM_ITEMS_FILE = os.path.join(BASE_DIR, "custom_products.json")  # OLD - for migration
    PRODUCTS_DB_FILE = os.path.join(BASE_DIR, "data", "products_db.json")  # NEW persistent DB
    STORY_IMG_1_PATH = os.path.join(BASE_DIR, "image-journey.png")
    COVER_IMG_PATH = os.path.join(BASE_DIR, "assets", "cover page.png")
    WATERMARK_IMG_PATH = os.path.join(BASE_DIR, "assets", "watermark.png")
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/"

    CATALOGUE_PATHS = {
        "HEM Product Catalogue": os.path.join(BASE_DIR, "Hem catalogue.xlsx"),
        "Sacred Elements Catalogue": os.path.join(BASE_DIR, "SacredElement.xlsx"),
        "Pooja Oil Catalogue": os.path.join(BASE_DIR, "Pooja Oil Catalogue.xlsx"),
        "Candle Catalogue": os.path.join(BASE_DIR, "Candle Catalogue.xlsx"),
    }
    CASE_SIZE_PATH = os.path.join(BASE_DIR, "Case Size.xlsx")
    CASE_SIZE_PATH = f"{GITHUB_RAW_BASE}Case%20Size.xlsx"

    GLOBAL_COLUMN_MAPPING = {
        "Category": "Category", "Sub-Category": "Subcategory", "Item Name": "ItemName",
        "ItemName": "ItemName", "Description": "Fragrance", "SKU Code": "SKU Code",
        "New Product ( Indication )": "IsNew"
    }
    NO_SELECTION_PLACEHOLDER = "Select..."

    # =========================================================================
    # --- 6. PERSISTENT JSON DATABASE MODULE ---
    # =========================================================================

    def get_empty_products_db():
        """Return the default empty database structure."""
        return {
            "version": 1,
            "last_updated": "",
            "product_overrides": {},
            "custom_products": [],
            "deleted_products": [],
            "saved_cart": []
        }

    def _download_db_from_cloudinary():
        """Try to download products_db.json from Cloudinary backup."""
        try:
            res = cloudinary.api.resource("app_data/products_db", resource_type="raw")
            url = res.get("secure_url", "")
            if url:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    def _upload_db_to_cloudinary(db):
        """Backup products_db.json to Cloudinary as a raw file."""
        try:
            data_dir = os.path.dirname(PRODUCTS_DB_FILE)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            # Write to temp file first, then upload
            temp_path = PRODUCTS_DB_FILE + ".upload_tmp"
            with open(temp_path, 'w') as f:
                json.dump(db, f, indent=2)
            cloudinary.uploader.upload(
                temp_path,
                resource_type="raw",
                public_id="products_db",
                folder="app_data",
                overwrite=True
            )
            # Clean up temp
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"Cloudinary DB backup error: {e}")

    def _download_templates_from_cloudinary():
        """Try to download saved_templates.json from Cloudinary backup."""
        try:
            res = cloudinary.api.resource("app_data/saved_templates", resource_type="raw")
            url = res.get("secure_url", "")
            if url:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    def _upload_templates_to_cloudinary():
        """Backup saved_templates.json to Cloudinary."""
        try:
            if os.path.exists(SAVED_TEMPLATES_FILE):
                cloudinary.uploader.upload(
                    SAVED_TEMPLATES_FILE,
                    resource_type="raw",
                    public_id="saved_templates",
                    folder="app_data",
                    overwrite=True
                )
        except Exception as e:
            print(f"Cloudinary templates backup error: {e}")

    def load_products_db():
        """Load the products database from JSON file, with Cloudinary fallback."""
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
                return db
            except Exception:
                pass

        # Fallback: try Cloudinary backup
        cloud_db = _download_db_from_cloudinary()
        if cloud_db:
            # Save locally for next time
            data_dir = os.path.dirname(PRODUCTS_DB_FILE)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            with open(PRODUCTS_DB_FILE, 'w') as f:
                json.dump(cloud_db, f, indent=2)
            return cloud_db

        return get_empty_products_db()

    def save_products_db(db):
        """Save the products database to JSON file AND backup to Cloudinary."""
        data_dir = os.path.dirname(PRODUCTS_DB_FILE)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        db["last_updated"] = datetime.now().isoformat()
        try:
            with open(PRODUCTS_DB_FILE, 'w') as f:
                json.dump(db, f, indent=2)
            # Backup to Cloudinary (async-safe)
            _upload_db_to_cloudinary(db)
        except Exception as e:
            st.error(f"Failed to save products database: {e}")

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

    def add_custom_product_to_db(product_data):
        """Add a custom product to the database."""
        db = load_products_db()
        db["custom_products"].append(product_data)
        save_products_db(db)

    def delete_custom_product_from_db(product_id):
        """Remove a custom product from the database."""
        db = load_products_db()
        db["custom_products"] = [p for p in db["custom_products"] if p.get("ProductID") != product_id]
        save_products_db(db)

    def get_custom_products_from_db():
        """Get all custom products from the database."""
        db = load_products_db()
        return db.get("custom_products", [])

    def save_cart_to_db(cart_items):
        """Persist cart to the JSON database."""
        db = load_products_db()
        db["saved_cart"] = cart_items
        save_products_db(db)

    def load_cart_from_db():
        """Load persisted cart from the JSON database."""
        db = load_products_db()
        return db.get("saved_cart", [])

    # --- MIGRATION: Old custom_products.json -> New DB ---
    def migrate_old_custom_items():
        """One-time migration from old custom_products.json to new products_db.json."""
        if not os.path.exists(CUSTOM_ITEMS_FILE):
            return False
        db = load_products_db()
        if db["custom_products"]:
            return False  # Already has data, skip
        try:
            with open(CUSTOM_ITEMS_FILE, 'r') as f:
                old_items = json.load(f)
            if old_items:
                db["custom_products"] = old_items
                save_products_db(db)
                # Rename old file to .bak
                os.rename(CUSTOM_ITEMS_FILE, CUSTOM_ITEMS_FILE + ".migrated.bak")
                return True
        except Exception:
            pass
        return False

    # --- CUSTOM ITEM ADD FUNCTION (Updated for new DB) ---
    def add_custom_item(catalogue, category, subcategory, item_name, fragrance, sku_code, is_new, image_file):
        img_url = ""
        if image_file:
            try:
                res = cloudinary.uploader.upload(image_file, folder="custom_uploads")
                img_url = res.get("secure_url", "")
            except Exception as e:
                print(f"Upload Error: {e}")

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
            "SerialNo": 0
        }
        add_custom_product_to_db(new_item)
        return new_item

    def delete_custom_item(pid):
        delete_custom_product_from_db(pid)

    # --- 7. PDFKIT CONFIG ---
    CONFIG = None
    try:
        if platform.system() == "Windows":
            paths_to_check = [
                r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
                r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
                os.path.join(BASE_DIR, "bin", "wkhtmltopdf.exe")
            ]
            found_path = None
            for path in paths_to_check:
                if os.path.exists(path):
                    found_path = path
                    break
            if found_path:
                CONFIG = pdfkit.configuration(wkhtmltopdf=found_path)
        else:
            try:
                path_wkhtmltopdf = subprocess.check_output(['which', 'wkhtmltopdf']).decode('utf-8').strip()
                CONFIG = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
            except:
                if os.path.exists('/usr/bin/wkhtmltopdf'):
                    CONFIG = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
                else:
                    CONFIG = None
    except Exception as e:
        print(f"PDFKit Config Error: {e}")
        CONFIG = None

    # --- 8. TEMPLATE MANAGEMENT ---
    def load_saved_templates():
        # Try local first
        if os.path.exists(SAVED_TEMPLATES_FILE):
            try:
                with open(SAVED_TEMPLATES_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        # Fallback: Cloudinary
        cloud_templates = _download_templates_from_cloudinary()
        if cloud_templates:
            with open(SAVED_TEMPLATES_FILE, 'w') as f:
                json.dump(cloud_templates, f, indent=4)
            return cloud_templates
        return {}

    def save_template_to_disk(name, cart_items):
        templates = load_saved_templates()
        templates[name] = cart_items
        try:
            with open(SAVED_TEMPLATES_FILE, 'w') as f:
                json.dump(templates, f, indent=4)
            _upload_templates_to_cloudinary()
            st.toast(f"Template '{name}' saved!", icon="💾")
        except Exception as e:
            st.error(f"Failed to save template: {e}")

    # --- 9. DATA LOADING (Merged: Excel + JSON DB + Cloudinary) ---

    @st.cache_data(show_spinner="Syncing Data (Smart Match v5 + Persistent DB)...")
    def load_data_cached(_dummy_timestamp):
        all_data = []
        required_output_cols = ['Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'Catalogue', 'Packaging', 'ImageB64', 'ProductID', 'IsNew']

        # --- A. CLOUDINARY IMAGE INDEXING ---
        cloudinary_map = {}
        filename_map = {}
        debug_log = ["--- SYNC START ---"]

        try:
            cloudinary.api.ping()
            resources = []
            next_cursor = None
            while True:
                res = cloudinary.api.resources(type="upload", max_results=500, next_cursor=next_cursor)
                resources.extend(res.get('resources', []))
                next_cursor = res.get('next_cursor')
                if not next_cursor:
                    break

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
            st.warning(f"⚠️ Cloudinary Warning: {e}")

        # --- B. LOAD PRODUCTS DATABASE ---
        db = load_products_db()
        overrides = db.get("product_overrides", {})
        deleted_pids = set(db.get("deleted_products", []))

        # --- C. EXCEL LOADING & MATCHING ---
        for catalogue_name, excel_path in CATALOGUE_PATHS.items():
            if not os.path.exists(excel_path):
                continue
            try:
                df = pd.read_excel(excel_path, sheet_name=0, dtype=str)
                df = df.fillna("")
                df.columns = [str(c).strip() for c in df.columns]
                df.rename(columns={k.strip(): v for k, v in GLOBAL_COLUMN_MAPPING.items() if k.strip() in df.columns}, inplace=True)

                df['Catalogue'] = catalogue_name
                df['Packaging'] = 'Default Packaging'
                df["ImageB64"] = ""
                df['IsNew'] = pd.to_numeric(df.get('IsNew', 0), errors='coerce').fillna(0).astype(int)

                # DETERMINISTIC ProductID (stable across reboots)
                df["ProductID"] = df.apply(
                    lambda row: generate_stable_product_id(
                        catalogue_name,
                        str(row.get('Category', '')),
                        str(row.get('ItemName', '')),
                        str(row.get('SKU Code', ''))
                    ), axis=1
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

                # CLOUDINARY IMAGE MATCHING (unchanged logic)
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
                            debug_log.append(f"Product: {row.get('ItemName')} | Found: {found_url is not None} | Type: {match_type}")

                        if found_url:
                            optimized_url = found_url.replace("/upload/", "/upload/w_800,q_auto/")
                            df.loc[index, "ImageB64"] = get_image_as_base64_str(optimized_url, max_size=None)

                all_data.append(df[required_output_cols])
            except Exception as e:
                st.error(f"Error reading Excel {catalogue_name}: {e}")

        # --- D. CUSTOM PRODUCTS FROM DATABASE ---
        custom_items = db.get("custom_products", [])
        if custom_items:
            custom_df = pd.DataFrame(custom_items)
            for col in required_output_cols:
                if col not in custom_df.columns:
                    custom_df[col] = '' if col != 'IsNew' else 0

            for idx, row in custom_df.iterrows():
                if str(row['ImageB64']).startswith('http'):
                    custom_df.at[idx, 'ImageB64'] = get_image_as_base64_str(row['ImageB64'])

            all_data.append(custom_df[required_output_cols])

        st.session_state['debug_logs'] = debug_log
        if not all_data:
            return pd.DataFrame(columns=required_output_cols)
        return pd.concat(all_data, ignore_index=True)

    # =========================================================================
    # --- 10. PDF GENERATOR (UNCHANGED - Keeping exactly as user's working version) ---
    # =========================================================================

    def generate_story_html(story_img_1_b64):
        text_block_1 = """HEM Corporation is amongst top global leaders in the manufacturing and export of perfumed agarbattis. For over three decades now we have been parceling out high-quality masala sticks, agarbattis, dhoops, and cones to our customers in more than 70 countries. We are known and established for our superior quality products.<br><br>HEM has been showered with love and accolades all across the globe for its diverse range of products. This makes us the most preferred brand the world over. HEM has been awarded as the 'Top Exporters' brand, for incense sticks by the 'Export Promotion Council for Handicraft' (EPCH) for three consecutive years from 2008 till 2011.<br><br>We have also been awarded "Niryat Shree" (Export) Silver Trophy in the Handicraft category by 'Federation of Indian Export Organization' (FIEO). The award was presented to us by the then Honourable President of India, late Shri Pranab Mukherjee."""
        text_journey_1 = """From a brand that was founded by three brothers in 1983, HEM Fragrances has come a long way. HEM started as a simple incense store offering products like masala agarbatti, thuribles, incense burner and dhoops. However, with time, there was a huge evolution in the world of fragrances much that the customers' needs also started changing. HEM incense can be experienced not only to provide you with rich aromatic experience but also create a perfect ambience for your daily prayers, meditation, and yoga.<br><br>The concept of aromatherapy massage, burning incense sticks and incense herbs for spiritual practices, using aromatherapy diffuser oils to promote healing and relaxation or using palo santo incense to purify and cleanse a space became popular around the world.<br><br>So, while we remained focused on creating our signature line of products, especially the 'HEM Precious' range which is a premium flagship collection, there was a dire need to expand our portfolio to meet increasing customer demands."""

        img_tag = ""
        if story_img_1_b64:
            img_tag = f'<img src="data:image/jpeg;base64,{story_img_1_b64}" style="max-width: 100%; height: auto; border: 1px solid #eee;" alt="Awards Image">'
        else:
            img_tag = '<div style="border: 2px dashed red; padding: 20px; color: red;">JOURNEY IMAGE NOT FOUND</div>'

        html = f"""
        <div class="story-page" style="page-break-after: always; padding: 25px 50px; font-family: sans-serif; overflow: hidden; height: 260mm;">
            <h1 style="text-align: center; color: #333; font-size: 28pt; margin-bottom: 20px;">Our Journey</h1>
            <div style="font-size: 11pt; line-height: 1.6; margin-bottom: 30px; text-align: justify;">{text_block_1}</div>
            <div style="margin-bottom: 30px; overflow: auto; clear: both;">
                <div style="float: left; width: 50%; margin-right: 20px; font-size: 11pt; line-height: 1.6; text-align: justify;">{text_journey_1}</div>
                <div style="float: right; width: 45%; text-align: center;">
                    {img_tag}
                </div>
            </div>
            <h2 style="text-align: center; font-size: 14pt; margin-top: 40px; clear: both;">Innovation, Creativity, Sustainability</h2>
        </div>
        """
        return html

    def generate_table_of_contents_html(df_sorted):
        toc_html = """
        <style>
            .toc-title { text-align: center; font-family: serif; font-size: 32pt; color: #222; margin-bottom: 20px; margin-top: 10px; text-transform: uppercase; letter-spacing: 1px; }
            h3.toc-catalogue-section-header {
                background-color: #333;
                color: #ffffff;
                font-family: sans-serif;
                font-size: 16pt;
                padding: 12px;
                margin: 0 0 15px 0;
                text-align: left;
                border-left: 8px solid #ff9800;
                clear: both;
                page-break-inside: avoid;
            }
            .index-grid-container {
                display: block;
                width: 100%;
                margin: 0 auto;
                font-size: 0;
            }
            a.index-card-link {
                display: inline-block;
                width: 30%;
                margin: 1.5%;
                height: 200px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-decoration: none;
                overflow: hidden;
                border: 1px solid #e0e0e0;
                page-break-inside: avoid;
                vertical-align: top;
            }
            .index-card-image {
                width: 100%;
                height: 160px;
                background-repeat: no-repeat;
                background-position: center center;
                background-size: contain;
                background-color: #f9f9f9;
            }
            .index-card-label {
                height: 40px;
                background-color: #b30000;
                color: white;
                font-family: sans-serif;
                font-size: 9pt;
                font-weight: bold;
                display: block;
                line-height: 40px;
                text-align: center;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                padding: 0 10px;
            }
            .clearfix::after { content: ""; clear: both; display: table; }
        </style>

        <div id="main-index" class="toc-page" style="page-break-after: always; padding: 20px;">
            <h1 class="toc-title">Table of Contents</h1>
        """

        catalogues = df_sorted['Catalogue'].unique()
        is_first_catalogue = True
        for catalogue_name in catalogues:
            page_break_style = 'style="page-break-before: always; padding-top: 20px;"' if not is_first_catalogue else 'style="padding-top: 10px;"'
            toc_html += f'<div {page_break_style}>'
            toc_html += f'<h3 class="toc-catalogue-section-header">{catalogue_name}</h3>'
            toc_html += '<div class="index-grid-container clearfix">'

            cat_df = df_sorted[df_sorted['Catalogue'] == catalogue_name]
            unique_categories = cat_df['Category'].unique()
            for category in unique_categories:
                group = cat_df[cat_df['Category'] == category]
                rep_image = ""
                for _, row in group.iterrows():
                    img_str = row.get('ImageB64', '')
                    if img_str and len(str(img_str)) > 100:
                        rep_image = img_str
                        break
                bg_style = f"background-image: url('data:image/png;base64,{rep_image}');" if rep_image else "background-color: #eee;"
                safe_id = create_safe_id(category)
                toc_html += f"""
                    <a href="#category-{safe_id}" class="index-card-link">
                        <div class="index-card-image" style="{bg_style}"></div>
                        <div class="index-card-label">{category}</div>
                    </a>
                """

            toc_html += '</div><div style="clear: both;"></div></div>'
            is_first_catalogue = False

        toc_html += """</div>"""
        return toc_html

    def generate_pdf_html(df_sorted, customer_name, logo_b64, case_selection_map):
        def load_img_robust(fname, specific_full_path=None, resize=False, max_size=(500, 500)):
            paths_to_check = []
            if specific_full_path:
                paths_to_check.append(specific_full_path)
            paths_to_check.append(os.path.join(BASE_DIR, "assets", fname))
            paths_to_check.append(os.path.join(BASE_DIR, fname))
            found_path = None
            for p in paths_to_check:
                if os.path.exists(p):
                    found_path = p
                    break
            if found_path:
                return get_image_as_base64_str(found_path, resize=resize, max_size=max_size)
            return ""

        cover_url = "https://res.cloudinary.com/dnoepbfbr/image/upload/v1770703751/Cover_Page.jpg"
        cover_bg_b64 = get_image_as_base64_str(cover_url)
        if not cover_bg_b64:
            cover_bg_b64 = load_img_robust("cover page.png", resize=False)

        journey_url = "https://res.cloudinary.com/dnoepbfbr/image/upload/v1770703751/image-journey.jpg"
        story_img_1_b64 = get_image_as_base64_str(journey_url, max_size=(600, 600))
        if not story_img_1_b64:
            story_img_1_b64 = load_img_robust("image-journey.png", specific_full_path=STORY_IMG_1_PATH, resize=True, max_size=(600, 600))

        watermark_b64 = load_img_robust("watermark.png", resize=False)

        CSS_STYLES = f"""
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8">
            <style>
            @page {{ size: A4; margin: 0; }}
            * {{ box-sizing: border-box; }}
            html, body {{
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                background-color: transparent !important;
            }}
            #watermark-layer {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                z-index: -1;
                background-image: url('data:image/png;base64,{watermark_b64}');
                background-repeat: repeat; background-position: center center; background-size: cover;
                background-color: transparent;
            }}
            .cover-page {{ width: 210mm; height: 260mm; display: block; position: relative; margin: 0; padding: 0; overflow: hidden; page-break-after: always; background-color: #ffffff; z-index: 10; }}
            .story-page, .toc-page {{ width: 210mm; display: block; position: relative; margin: 0; background-color: transparent; page-break-after: always; }}
            .catalogue-content {{ padding-left: 10mm; padding-right: 10mm; display: block; padding-bottom: 50px; position: relative; z-index: 1; background-color: transparent; }}
            .catalogue-heading {{ background-color: #333; color: white; font-size: 18pt; padding: 8px 15px; margin-bottom: 5px; font-weight: bold; font-family: sans-serif; text-align: center; page-break-inside: avoid; clear: both; }}
            .category-heading {{ color: #333; font-size: 14pt; padding: 8px 0 4px 0; border-bottom: 2px solid #E5C384; margin-top: 5mm; clear: both; font-family: serif; page-break-inside: avoid; width: 100%; }}
            .subcat-pdf-header {{ color: #007bff; font-size: 11pt; font-weight: bold; margin-top: 10px; margin-bottom: 5px; clear: both; font-family: sans-serif; border-left: 3px solid #007bff; padding-left: 8px; page-break-inside: avoid; width: 100%; }}
            .case-size-info {{ color: #555; font-size: 10pt; font-style: italic; margin-bottom: 5px; clear: both; font-family: sans-serif; }}
            .case-size-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 9pt; margin-bottom: 10px; clear: both; background-color: rgba(255,255,255,0.9); }}
            .case-size-table th {{ border: 1px solid #ddd; background-color: #f2f2f2; padding: 4px; text-align: center; font-weight: bold; font-size: 8pt; color: #333; }}
            .case-size-table td {{ border: 1px solid #ddd; padding: 4px; text-align: center; color: #444; }}
            .cover-image-container {{ position: absolute; top: 0; left: 0; height: 100%; width: 100%; z-index: 1; }}
            .cover-image-container img {{ width: 100%; height: 100%; object-fit: cover; }}
            .clearfix::after {{ content: ""; clear: both; display: table; }}
            .category-block {{
                display: block;
                font-size: 0;
                clear: both;
                page-break-inside: auto;
                margin-bottom: 20px;
                width: 100%;
                page-break-before: always;
            }}
            h1.catalogue-heading + .category-block {{
                page-break-before: avoid !important;
            }}
            .product-card {{
                display: inline-block;
                width: 23%;
                margin: 10px 1%;
                vertical-align: top;
                font-size: 12pt;
                padding: 0;
                box-sizing: border-box;
                background-color: #fcfcfc;
                border: 1px solid #E5C384;
                border-radius: 5px;
                text-align: center;
                position: relative;
                overflow: hidden;
                height: 180px;
                page-break-inside: avoid;
            }}
            .card-image-box {{
                width: 100%;
                height: 115px;
                position: relative;
                background-color: #fff;
                border-bottom: 1px solid #eee;
                overflow: hidden;
            }}
            .card-image-box img {{
                position: absolute;
                top: 0; bottom: 0; left: 0; right: 0;
                margin: auto;
                max-width: 95%;
                max-height: 95%;
                width: auto;
                height: auto;
                display: block;
            }}
            .card-info-box {{
                height: 60px;
                display: block;
                padding: 5px;
            }}
            .card-name {{
                font-family: serif;
                color: #000;
                line-height: 1.2;
                font-weight: bold;
                margin: 0;
                padding-top: 5px;
                display: block;
            }}
            </style></head><body style='margin: 0; padding: 0;'>
            <div id="watermark-layer"></div>
        """

        html_parts = []
        html_parts.append(CSS_STYLES)
        html_parts.append(f"""<div class="cover-page"><div class="cover-image-container"><img src="data:image/png;base64,{cover_bg_b64}"></div></div>""")
        html_parts.append(generate_story_html(story_img_1_b64))
        html_parts.append(generate_table_of_contents_html(df_sorted))
        html_parts.append('<div class="catalogue-content clearfix">')

        def get_val_fuzzy(row_data, keys_list):
            for k in keys_list:
                for data_k in row_data.keys():
                    if k.lower() in data_k.lower():
                        return str(row_data[data_k])
            return "-"

        current_catalogue = None
        current_category = None
        current_subcategory = None
        is_first_item = True
        category_open = False

        for index, row in df_sorted.iterrows():
            if row['Catalogue'] != current_catalogue:
                if category_open:
                    html_parts.append('</div>')
                    category_open = False
                current_catalogue = row['Catalogue']
                current_category = None
                current_subcategory = None
                break_style = 'style="page-break-before: always;"' if not is_first_item else ""
                html_parts.append(f'<div style="clear:both;"></div><h1 class="catalogue-heading" {break_style}>{current_catalogue}</h1>')
                is_first_item = False

            if row['Category'] != current_category:
                if category_open:
                    html_parts.append('</div>')
                current_category = row['Category']
                current_subcategory = None
                safe_category_id = create_safe_id(current_category)

                if current_category in case_selection_map:
                    try:
                        row_data = case_selection_map[current_category]
                    except:
                        row_data = {}
                else:
                    row_data = {}

                html_parts.append('<div class="category-block clearfix">')
                category_open = True
                html_parts.append(f'<h2 class="category-heading" id="category-{safe_category_id}"><a href="#main-index" style="float: right; font-size: 10px; color: #555; text-decoration: none; font-weight: normal; font-family: sans-serif; margin-top: 4px;">BACK TO INDEX &uarr;</a>{current_category}</h2>')

                if row_data:
                    desc = row_data.get('Description', '')
                    if desc:
                        html_parts.append(f'<div class="case-size-info"><strong>Case Size:</strong> {desc}</div>')
                    packing_val = get_val_fuzzy(row_data, ["Packing", "Master Ctn"])
                    gross_wt = get_val_fuzzy(row_data, ["Gross Wt", "Gross Weight"])
                    net_wt = get_val_fuzzy(row_data, ["Net Wt", "Net Weight"])
                    length = get_val_fuzzy(row_data, ["Length"])
                    breadth = get_val_fuzzy(row_data, ["Breadth", "Width"])
                    height = get_val_fuzzy(row_data, ["Height"])
                    cbm_val = get_val_fuzzy(row_data, ["CBM"])
                    html_parts.append(f'''<table class="case-size-table"><tr><th>Packing per Master Ctn<br>(doz/box)</th><th>Gross Wt.<br>(Kg)</th><th>Net Wt.<br>(Kg)</th><th>Length<br>(Cm)</th><th>Breadth<br>(Cm)</th><th>Height<br>(Cm)</th><th>CBM</th></tr><tr><td>{packing_val}</td><td>{gross_wt}</td><td>{net_wt}</td><td>{length}</td><td>{breadth}</td><td>{height}</td><td>{cbm_val}</td></tr></table>''')

            sub_val = str(row.get('Subcategory', '')).strip()
            if sub_val.upper() != 'N/A' and sub_val.lower() != 'nan' and sub_val != '':
                if sub_val != current_subcategory:
                    current_subcategory = sub_val
                    html_parts.append(f'<div class="subcat-pdf-header">{current_subcategory}</div>')

            img_url = row.get("ImageB64", "")
            if not img_url.startswith("http"):
                pass
            else:
                img_b64 = get_image_as_base64_str(img_url)
                row["ImageB64"] = img_b64

            img_b64 = row["ImageB64"]
            mime_type = 'image/png' if (img_b64 and len(img_b64) > 20 and img_b64[:20].lower().find('i') != -1) else 'image/jpeg'
            image_html_content = f'<img src="data:{mime_type};base64,{img_b64}" alt="Img">' if img_b64 else '<div style="padding-top:40px; color:#ccc; font-size:10px;">IMAGE NOT FOUND</div>'
            new_badge_html = """<div style="position: absolute; top: 0; right: 0; background-color: #dc3545; color: white; font-size: 8px; font-weight: bold; padding: 2px 8px; border-radius: 0 0 0 5px; z-index: 10;">NEW</div>""" if row.get('IsNew') == 1 else ""

            item_name_text = row.get('ItemName', 'N/A')
            name_len = len(str(item_name_text))
            if name_len < 30:
                font_size = "9pt"
            elif name_len < 50:
                font_size = "8pt"
            else:
                font_size = "7pt"

            card_html = f"""
            <div class="product-card">
                {new_badge_html}
                <div class="card-image-box">
                    {image_html_content}
                </div>
                <div class="card-info-box">
                    <div class="card-name" style="font-size: {font_size};">
                        <span style="color: #007bff; margin-right: 2px;">{index+1}.</span>{item_name_text}
                    </div>
                </div>
            </div>
            """
            html_parts.append(card_html)

        if category_open:
            html_parts.append('</div>')
        html_parts.append('<div style="clear: both;"></div></div></body></html>')
        return "".join(html_parts)

    def generate_excel_file(df_sorted, customer_name, case_selection_map):
        output = io.BytesIO()
        excel_rows = []
        for idx, row in df_sorted.iterrows():
            cat = row['Category']
            suffix = ""
            cbm = 0.0
            if cat in case_selection_map:
                case_data = case_selection_map[cat]
                for k in case_data.keys():
                    if "suffix" in k.lower():
                        suffix = str(case_data[k]).strip()
                    if "cbm" in k.lower():
                        try:
                            cbm = round(float(case_data[k]), 3)
                        except:
                            cbm = 0.0
                if suffix == 'nan':
                    suffix = ""
            full_name = str(row['ItemName']).strip()
            if suffix:
                full_name = f"{full_name} {suffix}"
            excel_rows.append({
                "Ref No": idx + 1, "Category": cat,
                "Product Name + Carton Name": full_name,
                "Carton per CBM": cbm, "Order Quantity (Cartons)": 0, "Total CBM": 0
            })

        df_excel = pd.DataFrame(excel_rows)
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Order Sheet', startrow=7)
            workbook = writer.book
            worksheet = writer.sheets['Order Sheet']
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            input_fmt = workbook.add_format({'bg_color': '#FFFCB7', 'border': 1, 'locked': False})
            locked_fmt = workbook.add_format({'border': 1, 'locked': True, 'num_format': '0.000'})
            count_fmt = workbook.add_format({'num_format': '0.00', 'bold': True, 'border': 1})
            title_fmt = workbook.add_format({'bold': True, 'font_size': 14})

            worksheet.protect()
            worksheet.freeze_panes(8, 0)
            worksheet.write('B1', f"Order Sheet for: {customer_name}", title_fmt)
            worksheet.write('B2', 'Total CBM:')
            worksheet.write_formula('C2', f'=SUM(F9:F{len(df_excel)+9})', workbook.add_format({'num_format': '0.000'}))
            worksheet.write('B3', 'CONTAINER TYPE', workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1}))
            worksheet.write('C3', 'ESTIMATED CONTAINERS', workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1}))
            worksheet.write('B4', '20 FT (30 CBM)', workbook.add_format({'border': 1}))
            worksheet.write('B5', '40 FT (60 CBM)', workbook.add_format({'border': 1}))
            worksheet.write('B6', '40 FT HC (70 CBM)', workbook.add_format({'border': 1}))
            worksheet.write_formula('C4', '=$C$2/30', count_fmt)
            worksheet.write_formula('C5', '=$C$2/60', count_fmt)
            worksheet.write_formula('C6', '=$C$2/70', count_fmt)
            for col_num, value in enumerate(df_excel.columns):
                worksheet.write(7, col_num, value, header_fmt)
            worksheet.set_column('A:A', 8)
            worksheet.set_column('B:B', 25)
            worksheet.set_column('C:C', 50)
            worksheet.set_column('D:F', 15)
            for i in range(len(df_excel)):
                row_idx = i + 9
                worksheet.write(row_idx - 1, 4, 0, input_fmt)
                worksheet.write_formula(row_idx - 1, 5, f'=D{row_idx}*E{row_idx}', locked_fmt)
        return output.getvalue()

    # --- 11. CART UTILS ---
    def add_to_cart(selected_df):
        current_pids = {item["ProductID"] for item in st.session_state.cart}
        new_items = []
        columns_to_keep = ['SKU Code', 'ItemName', 'Category', 'Subcategory', 'Fragrance', 'Packaging', 'SerialNo', 'ImageB64', 'Catalogue', 'ProductID', 'IsNew']
        if isinstance(selected_df, pd.Series):
            selected_df = pd.DataFrame([selected_df])
        for _, row in selected_df.iterrows():
            if row.get("ProductID") and row["ProductID"] not in current_pids:
                new_items.append({col: row.get(col, '') for col in columns_to_keep})
        if new_items:
            st.session_state.cart.extend(new_items)
            st.session_state.gen_pdf_bytes = None
            st.session_state.gen_excel_bytes = None
            save_cart_to_db(st.session_state.cart)
            st.toast(f"Added {len(new_items)} items to cart!", icon="🛒")

    def remove_from_cart(pids_to_remove):
        if pids_to_remove:
            st.session_state.cart = [i for i in st.session_state.cart if i.get("ProductID") not in pids_to_remove]
        st.session_state.gen_pdf_bytes = None
        st.session_state.gen_excel_bytes = None
        save_cart_to_db(st.session_state.cart)

    def add_selected_visible_to_cart(df_visible):
        pid_map = st.session_state.get('master_pid_map', {})
        visible_pids = set(df_visible['ProductID'].tolist())
        columns_to_keep = ['SKU Code', 'ItemName', 'Category', 'Subcategory', 'Fragrance', 'Packaging', 'SerialNo', 'ImageB64', 'Catalogue', 'ProductID', 'IsNew']
        current_cart_pids = {item["ProductID"] for item in st.session_state.cart if "ProductID" in item}
        added_count = 0
        new_items = []
        for key, is_checked in st.session_state.items():
            if key.startswith("checkbox_") and is_checked:
                pid = key.replace("checkbox_", "")
                if pid not in visible_pids:
                    continue
                product_data = pid_map.get(pid)
                if product_data and pid not in current_cart_pids:
                    row_series = pd.Series(product_data)
                    new_items.append({col: row_series.get(col, '') for col in columns_to_keep})
                    added_count += 1
        if new_items:
            st.session_state.cart.extend(new_items)
            st.session_state.gen_pdf_bytes = None
            st.session_state.gen_excel_bytes = None
            save_cart_to_db(st.session_state.cart)
            st.toast(f"Added {added_count} selected items to cart!", icon="🛒")
        else:
            st.toast("No items selected.", icon="ℹ️")

    def clear_filters_dropdown():
        st.session_state.selected_catalogue_dropdown = NO_SELECTION_PLACEHOLDER
        st.session_state.selected_categories_multi = []
        st.session_state.selected_subcategories_multi = []
        st.session_state.item_search_query = ""
        if "item_search_input" in st.session_state:
            del st.session_state["item_search_input"]
        if "category_multiselect" in st.session_state:
            del st.session_state["category_multiselect"]
        if "subcategory_multiselect" in st.session_state:
            del st.session_state["subcategory_multiselect"]

    def display_product_list(df_to_show, is_global_search=False):
        selected_pids = {item.get("ProductID") for item in st.session_state.cart if "ProductID" in item}
        if df_to_show.empty:
            st.info("No products match filters/search.")
            return

        db = load_products_db()
        overridden_pids = set(db.get("product_overrides", {}).keys())

        grouped_by_category = df_to_show.groupby('Category', sort=False)
        for category, cat_group_df in grouped_by_category:
            cat_count = len(cat_group_df)
            with st.expander(f"{category} ({cat_count})", expanded=is_global_search):
                c1, c2 = st.columns([3, 1])
                with c2:
                    if st.button(f"Add All {cat_count} items", key=f"btn_add_cat_{create_safe_id(category)}"):
                        add_to_cart(cat_group_df)

                for subcategory, subcat_group_df in cat_group_df.groupby('Subcategory', sort=False):
                    subcategory_str = str(subcategory).strip()
                    if subcategory_str.upper() != 'N/A' and subcategory_str.lower() != 'nan':
                        st.markdown(f"<div class='subcat-header'>{subcategory_str} ({len(subcat_group_df)})</div>", unsafe_allow_html=True)

                    col_name, col_check = st.columns([8, 1])
                    col_name.markdown('**Product Name**')
                    col_check.markdown('**Select**')
                    st.markdown("<hr style='margin:0 0 5px 0; border-color:#ddd;'>", unsafe_allow_html=True)

                    for idx, row in subcat_group_df.iterrows():
                        pid = row['ProductID']
                        unique_key = f"checkbox_{pid}"
                        initial_checked = pid in selected_pids
                        name_display = f"**{row['ItemName']}**"
                        if row.get('IsNew') == 1:
                            name_display += " <span class='badge-new'>NEW</span>"
                        if pid in overridden_pids:
                            name_display += " <span class='badge-modified'>EDITED</span>"
                        if str(pid).startswith("CUST_"):
                            name_display += " <span class='badge-custom'>CUSTOM</span>"
                        with col_name:
                            st.markdown(name_display, unsafe_allow_html=True)
                        if col_check.checkbox("Select", value=initial_checked, key=unique_key, label_visibility="hidden"):
                            pass

    # =========================================================================
    # --- 12. MAIN APP LOGIC ---
    # =========================================================================

    if True:
        # --- SESSION STATE INIT ---
        if "cart" not in st.session_state:
            # Restore cart from persistent DB on first load
            st.session_state.cart = load_cart_from_db()
        if "gen_pdf_bytes" not in st.session_state:
            st.session_state.gen_pdf_bytes = None
        if "gen_excel_bytes" not in st.session_state:
            st.session_state.gen_excel_bytes = None
        if 'selected_catalogue_dropdown' not in st.session_state:
            st.session_state.selected_catalogue_dropdown = NO_SELECTION_PLACEHOLDER
        if 'selected_categories_multi' not in st.session_state:
            st.session_state.selected_categories_multi = []
        if 'selected_subcategories_multi' not in st.session_state:
            st.session_state.selected_subcategories_multi = []
        if 'item_search_query' not in st.session_state:
            st.session_state.item_search_query = ""
        if 'master_pid_map' not in st.session_state:
            st.session_state['master_pid_map'] = {}
        if 'data_timestamp' not in st.session_state:
            st.session_state.data_timestamp = time.time()

        # --- ONE-TIME MIGRATION ---
        migrate_old_custom_items()

        # --- LOAD DATA ---
        products_df = load_data_cached(st.session_state.data_timestamp)
        st.session_state['master_pid_map'] = {row['ProductID']: row.to_dict() for _, row in products_df.iterrows()}

        # --- SIDEBAR ---
        with st.sidebar:
            st.header("📂 Manage Templates")
            with st.expander("Save Current Cart"):
                new_template_name = st.text_input("Template Name")
                if st.button("Save Template", use_container_width=True):
                    if new_template_name:
                        save_template_to_disk(new_template_name, st.session_state.cart)

            saved_templates = load_saved_templates()
            if saved_templates:
                with st.expander("Load Template"):
                    sel_temp = st.selectbox("Select Template", list(saved_templates.keys()))
                    if st.button("Load", use_container_width=True):
                        st.session_state.cart = saved_templates[sel_temp]
                        save_cart_to_db(st.session_state.cart)
                        st.toast(f"Template '{sel_temp}' loaded!", icon="✅")
                        st.rerun()

            with st.expander("🛠️ Image Sync Debugger", expanded=False):
                if 'debug_logs' in st.session_state:
                    for line in st.session_state['debug_logs']:
                        st.text(line)

            st.markdown("---")
            st.markdown("### 🔄 Data Sync")
            if st.button("Refresh Cloudinary & Excel", help="Click if you uploaded new images or changed the Excel file.", use_container_width=True):
                st.session_state.data_timestamp = time.time()
                st.cache_data.clear()
                st.rerun()

            st.markdown("---")
            st.markdown("### 📊 Database Info")
            db_info = load_products_db()
            st.caption(f"Overrides: {len(db_info.get('product_overrides', {}))}")
            st.caption(f"Custom Products: {len(db_info.get('custom_products', []))}")
            st.caption(f"Hidden Products: {len(db_info.get('deleted_products', []))}")
            st.caption(f"Cart Items: {len(db_info.get('saved_cart', []))}")
            if db_info.get('last_updated'):
                st.caption(f"Last Updated: {db_info['last_updated'][:19]}")

        # --- TITLE ---
        st.markdown('<div class="main-title">HEM PRODUCT CATALOGUE</div>', unsafe_allow_html=True)

        # --- TABS ---
        cart_count = len(st.session_state.cart)
        cart_label = f"2. Review & Edit ({cart_count})" if cart_count > 0 else "2. Review & Edit"
        tab1, tab2, tab3, tab4 = st.tabs(["1. Filter Products", cart_label, "3. Export", "4. Add Product"])

        # ====================== TAB 1: FILTER ======================
        with tab1:
            if products_df.empty:
                st.error("No Data. Please check Excel file paths or run Admin Sync.")
            else:
                final_df = products_df.copy()

                def update_search():
                    st.session_state.item_search_query = st.session_state["item_search_input"]

                search_term = st.text_input("🔍 Global Search (Products, Fragrance, SKU)", value=st.session_state.item_search_query, key="item_search_input", on_change=update_search).lower()

                if search_term:
                    final_df = products_df[
                        products_df['ItemName'].str.lower().str.contains(search_term, na=False) |
                        products_df['Fragrance'].str.lower().str.contains(search_term, na=False) |
                        products_df['SKU Code'].str.lower().str.contains(search_term, na=False)
                    ]
                    st.markdown(f"""<div class="stats-bar">
                        <span class="stat-item">Found <span class="stat-value">{len(final_df)}</span> items matching '{search_term}'</span>
                        <span class="stat-item">Cart: <span class="stat-value">{len(st.session_state.cart)}</span> items</span>
                    </div>""", unsafe_allow_html=True)
                    display_product_list(final_df, is_global_search=True)
                else:
                    col_filter, col_btns = st.columns([3, 1])
                    with col_filter:
                        st.markdown("#### Filters")
                        catalogue_options = [NO_SELECTION_PLACEHOLDER] + products_df['Catalogue'].unique().tolist()
                        try:
                            default_index_cat = catalogue_options.index(st.session_state.selected_catalogue_dropdown)
                        except ValueError:
                            default_index_cat = 0
                        sel_cat = st.selectbox("Catalogue", catalogue_options, key="selected_catalogue_dropdown", index=default_index_cat)

                        if sel_cat != NO_SELECTION_PLACEHOLDER:
                            catalog_subset_df = products_df[products_df['Catalogue'] == sel_cat]
                            category_options = catalog_subset_df['Category'].unique().tolist()

                            valid_defaults_cat = [c for c in st.session_state.selected_categories_multi if c in category_options]
                            if valid_defaults_cat != st.session_state.selected_categories_multi:
                                st.session_state.selected_categories_multi = valid_defaults_cat
                            sel_cats_multi = st.multiselect("Category", category_options, default=st.session_state.selected_categories_multi, key="category_multiselect")
                            st.session_state.selected_categories_multi = sel_cats_multi

                            if sel_cats_multi:
                                filtered_dfs = []
                                st.markdown("---")
                                st.markdown("**Sub-Category Options:**")
                                for category in sel_cats_multi:
                                    cat_data = catalog_subset_df[catalog_subset_df['Category'] == category]
                                    raw_subs = cat_data['Subcategory'].unique().tolist()
                                    clean_subs = [s for s in raw_subs if str(s).strip().upper() != 'N/A' and str(s).strip().lower() != 'nan' and str(s).strip() != '']

                                    if clean_subs:
                                        safe_cat_key = create_safe_id(category)
                                        sel_subs = st.multiselect(f"Select for **{category}**", clean_subs, default=clean_subs, key=f"sub_select_{safe_cat_key}")
                                        cat_data_filtered = cat_data[cat_data['Subcategory'].isin(sel_subs) | cat_data['Subcategory'].isin(['N/A', 'nan', '']) | cat_data['Subcategory'].isna()]
                                        filtered_dfs.append(cat_data_filtered)
                                    else:
                                        filtered_dfs.append(cat_data)
                                if filtered_dfs:
                                    final_df = pd.concat(filtered_dfs)
                                else:
                                    final_df = pd.DataFrame(columns=products_df.columns)
                            else:
                                final_df = catalog_subset_df

                    with col_btns:
                        st.markdown("#### Actions")
                        if st.button("ADD SELECTED", use_container_width=True, type="primary"):
                            add_selected_visible_to_cart(final_df)
                        if st.button("ADD FILTERED", use_container_width=True, type="secondary"):
                            add_to_cart(final_df)
                        st.button("Clear Filters", use_container_width=True, on_click=clear_filters_dropdown)

                    st.markdown("---")

                    if sel_cat != NO_SELECTION_PLACEHOLDER:
                        # Stats bar
                        st.markdown(f"""<div class="stats-bar">
                            <span class="stat-item">Showing <span class="stat-value">{len(final_df)}</span> products</span>
                            <span class="stat-item">Cart: <span class="stat-value">{len(st.session_state.cart)}</span> items</span>
                        </div>""", unsafe_allow_html=True)

                        if not final_df.empty:
                            display_product_list(final_df)
                        else:
                            st.info("👆 Please select one or more **Categories**.")
                    else:
                        st.info("👈 Please select a **Catalogue** to begin.")

        # ====================== TAB 2: REVIEW & EDIT ======================
        with tab2:
            st.markdown('<div class="section-header">Review & Edit Cart Items</div>', unsafe_allow_html=True)

            if st.session_state.cart:
                cart_df = pd.DataFrame(st.session_state.cart)
                cart_search = st.text_input("🔍 Find in Cart...", placeholder="Type name...").lower()
                if cart_search:
                    cart_df = cart_df[cart_df['ItemName'].str.lower().str.contains(cart_search, na=False)]

                # Load DB to show override indicators
                db = load_products_db()
                overridden_pids = set(db.get("product_overrides", {}).keys())

                # Add status column
                def get_status(pid):
                    parts = []
                    if pid in overridden_pids:
                        parts.append("Edited")
                    if str(pid).startswith("CUST_"):
                        parts.append("Custom")
                    return ", ".join(parts) if parts else ""

                cart_df['Status'] = cart_df['ProductID'].apply(get_status)
                cart_df['Remove'] = False

                # Ensure all editable columns exist
                editable_display_cols = ['Catalogue', 'Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'Status', 'Remove']
                for col in editable_display_cols:
                    if col not in cart_df.columns:
                        cart_df[col] = ''

                st.markdown(f"""<div class="stats-bar">
                    <span class="stat-item">Total Items: <span class="stat-value">{len(cart_df)}</span></span>
                    <span class="stat-item">Edited: <span class="stat-value">{len([p for p in cart_df['ProductID'] if p in overridden_pids])}</span></span>
                    <span class="stat-item">Custom: <span class="stat-value">{len([p for p in cart_df['ProductID'] if str(p).startswith('CUST_')])}</span></span>
                </div>""", unsafe_allow_html=True)

                # Store original values for change detection
                original_values = cart_df[['ProductID', 'Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code']].copy()

                edited_df = st.data_editor(
                    cart_df[editable_display_cols],
                    column_config={
                        "Remove": st.column_config.CheckboxColumn("Remove?", default=False, width="small"),
                        "Catalogue": st.column_config.TextColumn("Catalogue", width="medium"),
                        "Category": st.column_config.TextColumn("Category", width="medium"),
                        "Subcategory": st.column_config.TextColumn("Sub-Category", width="medium"),
                        "ItemName": st.column_config.TextColumn("Product Name", width="large"),
                        "Fragrance": st.column_config.TextColumn("Fragrance", width="medium"),
                        "SKU Code": st.column_config.TextColumn("SKU Code", width="medium"),
                        "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                    },
                    hide_index=True,
                    key="cart_data_editor_v2",
                    use_container_width=True,
                    num_rows="fixed"
                )

                # --- DETECT CHANGES ---
                editable_fields = ['Catalogue', 'Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code']
                changes_detected = {}

                for idx in range(min(len(cart_df), len(edited_df))):
                    pid = cart_df.iloc[idx]['ProductID']
                    field_changes = {}
                    for field in editable_fields:
                        original_val = str(cart_df.iloc[idx].get(field, '')).strip()
                        edited_val = str(edited_df.iloc[idx].get(field, '')).strip()
                        if original_val != edited_val:
                            field_changes[field] = edited_val
                    if field_changes:
                        changes_detected[pid] = field_changes

                # --- ACTION BUTTONS ---
                col_save, col_remove, col_clear = st.columns([1, 1, 1])

                with col_save:
                    save_disabled = len(changes_detected) == 0
                    if st.button(
                        f"💾 Save {len(changes_detected)} Edit(s)" if changes_detected else "💾 No Changes",
                        disabled=save_disabled,
                        use_container_width=True,
                        type="primary"
                    ):
                        for pid, field_changes in changes_detected.items():
                            save_product_override(pid, field_changes)
                            # Also update cart in session state
                            for item in st.session_state.cart:
                                if item.get("ProductID") == pid:
                                    item.update(field_changes)
                        save_cart_to_db(st.session_state.cart)
                        st.session_state.data_timestamp = time.time()
                        st.cache_data.clear()
                        st.toast(f"Saved {len(changes_detected)} product edit(s)!", icon="✅")
                        st.rerun()

                with col_remove:
                    indices_to_remove = edited_df[edited_df['Remove'] == True].index.tolist()
                    pids_to_remove = cart_df.loc[indices_to_remove, 'ProductID'].tolist() if indices_to_remove else []
                    if st.button(f"🗑️ Remove {len(pids_to_remove)} Selected", disabled=not pids_to_remove, use_container_width=True):
                        remove_from_cart(pids_to_remove)
                        st.rerun()

                with col_clear:
                    if st.button("🗑️ Clear Cart", use_container_width=True):
                        st.session_state.cart = []
                        st.session_state.gen_pdf_bytes = None
                        st.session_state.gen_excel_bytes = None
                        save_cart_to_db([])
                        st.rerun()

                # --- SHOW CHANGE PREVIEW ---
                if changes_detected:
                    with st.expander(f"📝 Preview {len(changes_detected)} Pending Edit(s)", expanded=True):
                        for pid, changes in changes_detected.items():
                            # Find original name
                            orig_row = cart_df[cart_df['ProductID'] == pid]
                            orig_name = orig_row.iloc[0]['ItemName'] if not orig_row.empty else pid
                            change_text = ", ".join([f"**{k}**: '{v}'" for k, v in changes.items()])
                            st.markdown(f"- **{orig_name}** → {change_text}")
                        st.info("Click **Save Edit(s)** above to persist these changes permanently.")

            else:
                st.info("Cart is empty. Go to **Tab 1** to add products.")

        # ====================== TAB 3: EXPORT ======================
        with tab3:
            st.markdown('<div class="section-header">Export Catalogue</div>', unsafe_allow_html=True)

            if not st.session_state.cart:
                st.info("Cart is empty.")
            else:
                st.markdown("### 1. Select Case Sizes per Category")
                cart_categories = sorted(list(set(
                    [item['Category'] for item in st.session_state.cart]
                )))
                full_case_size_df = pd.DataFrame()
                DB_PATH = os.path.join(BASE_DIR, "data", "database.json")
                if os.path.exists(DB_PATH):
                    try:
                        with open(DB_PATH, 'r') as f:
                            db_data = json.load(f)
                        if db_data.get("case_sizes"):
                            full_case_size_df = pd.DataFrame(db_data["case_sizes"])
                    except Exception:
                        pass
                if full_case_size_df.empty:
                    try:
                        full_case_size_df = pd.read_excel(CASE_SIZE_PATH, dtype=str)
                        full_case_size_df.columns = [c.strip() for c in full_case_size_df.columns]
                    except Exception:
                        st.error("Error loading Case Size data.")

                selection_map = {}
                if not full_case_size_df.empty:
                    suffix_col = next((c for c in full_case_size_df.columns if "suffix" in c.lower()), None)
                    cbm_col = next((c for c in full_case_size_df.columns if "cbm" in c.lower()), "CBM")
                    if not suffix_col:
                        st.error(f"Could not find 'Carton Suffix' column. Found: {full_case_size_df.columns.tolist()}")
                    else:
                        for cat in cart_categories:
                            options = full_case_size_df[full_case_size_df['Category'] == cat].copy()
                            if not options.empty:
                                options['DisplayLabel'] = options.apply(
                                    lambda x: f"{x.get(suffix_col, '')} (CBM: {x.get(cbm_col, '')})", axis=1
                                )
                                label_list = options['DisplayLabel'].tolist()
                                selected_label = st.selectbox(f"Select Case Size for **{cat}**", label_list, key=f"select_case_{cat}")
                                selected_row = options[options['DisplayLabel'] == selected_label].iloc[0]
                                selection_map[cat] = selected_row.to_dict()
                            else:
                                st.warning(f"No Case Size options found for category: {cat}")

                st.markdown("---")
                name = st.text_input("Client Name", "Valued Client")
                if st.button("Generate Catalogue & Order Sheet", use_container_width=True):
                    cart_data = st.session_state.cart
                    schema_cols = ['Catalogue', 'Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'ImageB64', 'Packaging', 'IsNew']
                    df_final = pd.DataFrame(cart_data)
                    for col in schema_cols:
                        if col not in df_final.columns:
                            df_final[col] = ''

                    products_df_fresh = load_data_cached(st.session_state.data_timestamp)
                    pid_to_index = {row['ProductID']: i for i, row in products_df_fresh.iterrows()}
                    if 'ProductID' in df_final.columns:
                        df_final['excel_sort_order'] = df_final['ProductID'].map(pid_to_index)
                        max_idx = len(products_df_fresh)
                        df_final['excel_sort_order'] = df_final['excel_sort_order'].fillna(max_idx)
                        df_final = df_final.sort_values('excel_sort_order')
                        df_final = df_final.drop(columns=['excel_sort_order'])
                    df_final['SerialNo'] = range(1, len(df_final) + 1)
                    st.toast("Generating files...", icon="⏳")

                    st.session_state.gen_excel_bytes = generate_excel_file(df_final, name, selection_map)

                    try:
                        logo = get_image_as_base64_str(LOGO_PATH, resize=True, max_size=(200, 100))
                        html = generate_pdf_html(df_final, name, logo, selection_map)
                        if CONFIG:
                            options = {
                                'page-size': 'A4', 'margin-top': '0mm', 'margin-right': '0mm',
                                'margin-bottom': '0mm', 'margin-left': '0mm', 'encoding': "UTF-8",
                                'no-outline': None, 'enable-local-file-access': None,
                                'disable-smart-shrinking': None, 'print-media-type': None
                            }
                            st.session_state.gen_pdf_bytes = pdfkit.from_string(html, False, configuration=CONFIG, options=options)
                            st.toast("PDF generated via PDFKit (Local)!", icon="🎉")
                        elif HAS_WEASYPRINT:
                            st.toast("Using Cloud Engine (WeasyPrint)...", icon="☁️")
                            st.session_state.gen_pdf_bytes = HTML(string=html, base_url=BASE_DIR).write_pdf()
                            st.toast("PDF generated via WeasyPrint (Cloud)!", icon="🎉")
                        else:
                            st.error("No PDF engine found! Install 'wkhtmltopdf' locally or 'weasyprint' on server.")
                            st.session_state.gen_pdf_bytes = None
                        gc.collect()
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")
                        st.session_state.gen_pdf_bytes = None

                c_pdf, c_excel = st.columns(2)
                with c_pdf:
                    if st.session_state.gen_pdf_bytes:
                        st.download_button("Download PDF Catalogue", st.session_state.gen_pdf_bytes, f"{name.replace(' ', '_')}_catalogue.pdf", type="primary", use_container_width=True)
                with c_excel:
                    if st.session_state.gen_excel_bytes:
                        st.download_button("Download Excel Order Sheet", st.session_state.gen_excel_bytes, f"{name.replace(' ', '_')}_order.xlsx", type="secondary", use_container_width=True)

        # ====================== TAB 4: ADD NEW PRODUCT ======================
        with tab4:
            st.markdown('<div class="section-header">Add New Product</div>', unsafe_allow_html=True)
            st.markdown("Add a custom product to any catalogue. It will be tagged as **NEW** and included in the product list.")

            with st.form("add_product_form", clear_on_submit=True):
                st.markdown("### Product Details")
                col_a, col_b = st.columns(2)
                with col_a:
                    existing_catalogues = list(CATALOGUE_PATHS.keys()) + ["Custom Items"]
                    new_catalogue = st.selectbox("Catalogue *", existing_catalogues, help="Select which catalogue this product belongs to.")
                    if not products_df.empty:
                        existing_cats = products_df[products_df['Catalogue'] == new_catalogue]['Category'].unique().tolist()
                    else:
                        existing_cats = []
                    cat_input_mode = st.radio("Category Input", ["Select Existing", "Type New"], horizontal=True)
                    if cat_input_mode == "Select Existing" and existing_cats:
                        new_category = st.selectbox("Category *", existing_cats)
                    else:
                        new_category = st.text_input("Category Name *", placeholder="e.g. Hexa Incense Sticks")
                    new_subcategory = st.text_input("Sub-Category", placeholder="e.g. Premium Range (leave blank for N/A)")

                with col_b:
                    new_item_name = st.text_input("Item Name *", placeholder="e.g. Lavender Hexa")
                    new_fragrance = st.text_input("Fragrance / Description", placeholder="e.g. Lavender")
                    new_sku = st.text_input("SKU Code", placeholder="e.g. HEM-LAV-HEX-001")
                    new_is_new = st.checkbox("Mark as NEW product", value=True)

                st.markdown("### Product Image")
                new_image = st.file_uploader("Upload product image (optional)", type=["jpg", "jpeg", "png", "webp"], help="Image will be uploaded to Cloudinary automatically.")
                if new_image:
                    st.image(new_image, caption="Preview", width=200)

                submitted = st.form_submit_button("Add Product", use_container_width=True, type="primary")
                if submitted:
                    errors = []
                    if not new_catalogue:
                        errors.append("Catalogue is required.")
                    if not new_category:
                        errors.append("Category is required.")
                    if not new_item_name:
                        errors.append("Item Name is required.")
                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        with st.spinner("Adding product..."):
                            added = add_custom_item(
                                catalogue=new_catalogue, category=new_category,
                                subcategory=new_subcategory, item_name=new_item_name,
                                fragrance=new_fragrance, sku_code=new_sku,
                                is_new=new_is_new, image_file=new_image
                            )
                        st.success(f"Product '{new_item_name}' added successfully! (ID: {added['ProductID']})")
                        st.info("Click **Refresh Cloudinary & Excel** in the sidebar to see it in the product list.")

            # --- MANAGE EXISTING CUSTOM ITEMS ---
            st.markdown("---")
            st.markdown('<div class="section-header">Manage Custom Products</div>', unsafe_allow_html=True)
            custom_items = get_custom_products_from_db()
            if custom_items:
                st.markdown(f"**{len(custom_items)} custom product(s) added.**")
                for i, item in enumerate(custom_items):
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        new_tag = " <span class='badge-new'>NEW</span>" if item.get('IsNew', 0) == 1 else ""
                        st.markdown(
                            f"**{i+1}.** {item['ItemName']}{new_tag} | {item['Catalogue']} > {item['Category']}",
                            unsafe_allow_html=True
                        )
                    with col_del:
                        if st.button("Delete", key=f"del_custom_{item['ProductID']}"):
                            delete_custom_item(item['ProductID'])
                            st.session_state.data_timestamp = time.time()
                            st.cache_data.clear()
                            st.toast(f"Deleted '{item['ItemName']}'", icon="🗑️")
                            st.rerun()
            else:
                st.info("No custom products added yet.")

            # --- MANAGE PRODUCT OVERRIDES ---
            st.markdown("---")
            st.markdown('<div class="section-header">Manage Product Edits</div>', unsafe_allow_html=True)
            db_for_overrides = load_products_db()
            overrides = db_for_overrides.get("product_overrides", {})
            if overrides:
                st.markdown(f"**{len(overrides)} product(s) have been edited.**")
                for pid, changes in overrides.items():
                    change_text = ", ".join([f"{k}: '{v}'" for k, v in changes.items()])
                    col_ov_info, col_ov_reset = st.columns([5, 1])
                    with col_ov_info:
                        st.markdown(f"**{pid}** → {change_text}")
                    with col_ov_reset:
                        if st.button("Reset", key=f"reset_override_{pid}"):
                            remove_product_override(pid)
                            st.session_state.data_timestamp = time.time()
                            st.cache_data.clear()
                            st.toast(f"Reset edits for {pid}", icon="↩️")
                            st.rerun()
            else:
                st.info("No product edits have been made.")

            # --- MANAGE HIDDEN PRODUCTS ---
            st.markdown("---")
            deleted_pids = db_for_overrides.get("deleted_products", [])
            if deleted_pids:
                st.markdown(f"**{len(deleted_pids)} product(s) hidden.**")
                for pid in deleted_pids:
                    col_del_info, col_del_restore = st.columns([5, 1])
                    with col_del_info:
                        st.markdown(f"Hidden: **{pid}**")
                    with col_del_restore:
                        if st.button("Restore", key=f"restore_{pid}"):
                            unmark_product_deleted(pid)
                            st.session_state.data_timestamp = time.time()
                            st.cache_data.clear()
                            st.toast(f"Restored {pid}", icon="✅")
                            st.rerun()

# --- SAFETY BOOT CATCH-ALL ---
except Exception as e:
    st.error("CRITICAL APP CRASH")
    st.error(f"Error Details: {e}")
    st.info("Check your 'packages.txt', 'requirements.txt', and Render Start Command.")
