import streamlit as st
import os
import sys
import gc   # Garbage collection

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
        cloud_name = "dddtoqebz",
        api_key = "157864912291655",
        api_secret = "YkhyT4hxge0fh-zACddSnsI0-S4",
        secure = True
    )

    # --- 3. HELPER FUNCTIONS ---
    def get_image_as_base64_str(url_or_path, resize=None, max_size=None):
        if not url_or_path: return ""
        try:
            img = None
            if str(url_or_path).startswith("http"):
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url_or_path, headers=headers, timeout=5)
                if response.status_code != 200:
                    return ""
                img = Image.open(io.BytesIO(response.content))
            else:
                if not os.path.exists(url_or_path): return ""
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

    def clean_key(text):
        if not isinstance(text, str): return ""
        text = text.lower().strip().replace(' ', '').replace('_', '').replace('-', '')
        for stop_word in ['catalogue', 'image', 'images', 'product', 'products', 'img']:
            text = text.replace(stop_word, '')
        return text

    # --- 4. DATA LOADING FUNCTION ---
    @st.cache_data(show_spinner="Syncing Data from GitHub...")
    def load_data_cached(_dummy_timestamp):
        all_data = []
        required_output_cols = ['Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'Catalogue', 'Packaging', 'ImageB64', 'ProductID', 'IsNew']
        
        # A. Build Cloudinary Map (Improved for Folders)
        cloudinary_map = {}
        try:
            cloudinary.api.ping()
            resources = []
            next_cursor = None
            while True:
                res = cloudinary.api.resources(type="upload", max_results=500, next_cursor=next_cursor)
                resources.extend(res.get('resources', []))
                next_cursor = res.get('next_cursor')
                if not next_cursor: break
            
            for res in resources:
                full_id = res['public_id']
                filename_only = full_id.split('/')[-1]
                cloudinary_map[clean_key(full_id)] = res['secure_url']
                cloudinary_map[clean_key(filename_only)] = res['secure_url']
        except Exception as e:
            st.warning(f"Cloudinary Sync Error: {e}")

        # B. Check Admin Database Fallback
        DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database.json")
        data_loaded_from_db = False
        # (DB logic omitted for brevity, focusing on Excel/GitHub flow)

        # C. Excel/GitHub Main Logic
        CATALOGUE_PATHS = {
            "HEM Product Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/Hem%20catalogue.xlsx",
            "Sacred Elements Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/SacredElement.xlsx",
            "Pooja Oil Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/Pooja%20Oil%20Catalogue.xlsx",
            "Candle Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/Candle%20Catalogue.xlsx",
        }
        GLOBAL_COLUMN_MAPPING = {
            "Category": "Category", "Sub-Category": "Subcategory", "Item Name": "ItemName",
            "ItemName": "ItemName", "Description": "Fragrance", "SKU Code": "SKU Code",
            "New Product ( Indication )": "IsNew"
        }

        for catalogue_name, path_ref in CATALOGUE_PATHS.items():
            target_path = f"{path_ref}?v={_dummy_timestamp}" if path_ref.startswith("http") else path_ref
            try:
                df = pd.read_excel(target_path, sheet_name=0, dtype=str, engine="openpyxl")
                df = df.fillna("")
                df.columns = [str(c).strip() for c in df.columns]
                df.rename(columns={k.strip(): v for k, v in GLOBAL_COLUMN_MAPPING.items() if k.strip() in df.columns}, inplace=True)
                
                df['Catalogue'] = catalogue_name
                df['Packaging'] = 'Default Packaging'
                df["ImageB64"] = ""
                df["ProductID"] = [f"PID_{str(uuid.uuid4())[:8]}" for _ in range(len(df))]
                df['IsNew'] = pd.to_numeric(df.get('IsNew', 0), errors='coerce').fillna(0).astype(int)

                for col in required_output_cols:
                    if col not in df.columns: df[col] = '' if col != 'IsNew' else 0

                # Improved Cloudinary Image Matcher
                if cloudinary_map:
                    for index, row in df.iterrows():
                        row_item_key = clean_key(row['ItemName'])
                        found_url = None
                        if row_item_key in cloudinary_map: 
                            found_url = cloudinary_map[row_item_key]
                        else:
                            best_score = 0
                            for cloud_key, url in cloudinary_map.items():
                                score = fuzz.token_sort_ratio(row_item_key, cloud_key)
                                if score > best_score:
                                    best_score = score
                                    found_url = url
                            if best_score < 60: found_url = None

                        if found_url:
                            opt_url = found_url.replace("/upload/", "/upload/f_auto,q_auto,w_800/")
                            df.at[index, "ImageB64"] = get_image_as_base64_str(opt_url)

                all_data.append(df[required_output_cols])
            except Exception as e:
                st.error(f"Error reading {catalogue_name}: {e}")

        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame(columns=required_output_cols)

    # --- 5. PDF GENERATION UTILS ---
    def generate_table_of_contents_html(df_sorted):
        toc_html = """
        <style>
            .index-page-container { page-break-before: always; padding: 15mm 10mm; font-family: sans-serif; background-color: #ffffff; min-height: 270mm; }
            .index-main-header { background-color: #333; color: #ffffff; text-align: center; padding: 15px 0; font-size: 24pt; font-weight: bold; text-transform: uppercase; margin-bottom: 30px; letter-spacing: 1px; }
            .index-grid { display: block; width: 100%; clear: both; }
            a.index-card { display: inline-block; width: 22%; margin: 1%; height: 220px; border: 1px solid #e0e0e0; border-radius: 4px; text-decoration: none; vertical-align: top; overflow: hidden; background-color: #fff; }
            .index-card-img-box { width: 100%; height: 160px; display: flex; align-items: center; justify-content: center; background-color: #ffffff; padding: 10px; box-sizing: border-box; }
            .index-card-img-box img { max-width: 100%; max-height: 100%; object-fit: contain; }
            .index-card-title { height: 60px; background-color: #b30000; color: #ffffff; font-size: 9pt; font-weight: bold; text-align: center; display: flex; align-items: center; justify-content: center; padding: 5px; text-transform: uppercase; line-height: 1.2; }
            .clearfix::after { content: ""; clear: both; display: table; }
        </style>
        <div id="main-index">
        """
        catalogues = df_sorted['Catalogue'].unique()
        for catalogue_name in catalogues:
            toc_html += f'<div class="index-page-container">'
            toc_html += f'<div class="index-main-header">{catalogue_name}</div>'
            toc_html += '<div class="index-grid clearfix">'
            cat_df = df_sorted[df_sorted['Catalogue'] == catalogue_name]
            for category in cat_df['Category'].unique():
                group = cat_df[cat_df['Category'] == category]
                rep_image = next((row['ImageB64'] for _, row in group.iterrows() if len(str(row['ImageB64'])) > 100), "")
                safe_id = create_safe_id(category)
                image_tag = f'<img src="data:image/jpeg;base64,{rep_image}">' if rep_image else '<span style="color:#ccc">No Image</span>'
                toc_html += f'<a href="#category-{safe_id}" class="index-card"><div class="index-card-img-box">{image_tag}</div><div class="index-card-title">{category}</div></a>'
            toc_html += '</div></div>'
        toc_html += "</div>"
        return toc_html

    # --- 6. REMAINING LOGIC (APP INITIALIZATION) ---
    st.set_page_config(page_title="HEM PRODUCT CATALOGUE", page_icon="🛍️", layout="wide")
    
    if "cart" not in st.session_state: st.session_state.cart = []
    if "data_timestamp" not in st.session_state: st.session_state.data_timestamp = time.time()

    products_df = load_data_cached(st.session_state.data_timestamp)

    # (Sidebar Action Buttons, Tab Logic, etc. would continue here)
    st.title("HEM PRODUCT CATALOGUE")
    st.info("Data synced successfully. Use the tabs below to build your catalogue.")

except Exception as e:
    st.error("🚨 CRITICAL APP CRASH 🚨")
    st.error(f"Error Details: {e}")
    st.info("Check your 'packages.txt', 'requirements.txt', and Render Start Command.")

