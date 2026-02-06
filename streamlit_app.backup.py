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
                response = requests.get(url_or_path, headers=headers, timeout=10)
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

    def normalize_key(text):
        """
        Simple, safe normalization.
        Removes spaces, casing, and extensions.
        Does NOT remove words like 'catalogue' or 'product'.
        """
        if not isinstance(text, str): return ""
        text = text.lower().strip()
        # Remove extensions
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            if text.endswith(ext): text = text[:-len(ext)]
        
        # Remove only separators, keep the words intact
        text = text.replace(' ', '').replace('_', '').replace('-', '')
        return text

    def force_light_theme_setup():
        config_dir = ".streamlit"
        config_path = os.path.join(config_dir, "config.toml")
        if not os.path.exists(config_dir): os.makedirs(config_dir)
        if not os.path.exists(config_path):
            theme_content = "[theme]\nbase='light'\nprimaryColor='#007bff'\nbackgroundColor='#ffffff'\nsecondaryBackgroundColor='#f0f2f6'\ntextColor='#000000'\nfont='sans serif'"
            with open(config_path, "w") as f: f.write(theme_content.strip())

    # --- 4. APP SETUP ---
    force_light_theme_setup()
    st.set_page_config(page_title="HEM PRODUCT CATALOGUE", page_icon="🛍️", layout="wide")

    st.markdown("""
        <style>
            .stApp { background-color: #ffffff !important; color: #000000 !important; }
            div[data-testid="stDataEditor"] { background-color: #ffffff !important; border: 1px solid #ced4da; }
            button[kind="primary"] { background-color: #ff9800 !important; color: white !important; border: none; font-weight: bold; }
            button[kind="secondary"] { background-color: #007bff !important; color: white !important; border: none; font-weight: bold; }
            .subcat-header { background-color: #f8f9fa; padding: 5px 10px; margin: 10px 0 5px 0; border-left: 4px solid #007bff; font-weight: bold; color: #333; }
        </style>
    """, unsafe_allow_html=True)

    # --- 5. PATHS ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates") 
    SAVED_TEMPLATES_FILE = os.path.join(BASE_DIR, "saved_templates.json")
    STORY_IMG_1_PATH = os.path.join(BASE_DIR, "image-journey.png") 
    COVER_IMG_PATH = os.path.join(BASE_DIR, "assets", "cover page.png")
    WATERMARK_IMG_PATH = os.path.join(BASE_DIR, "assets", "watermark.png") 

    CATALOGUE_PATHS = {
        "HEM Product Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/Hem%20catalogue.xlsx",
        "Sacred Elements Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/SacredElement.xlsx",
        "Pooja Oil Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/Pooja%20Oil%20Catalogue.xlsx",
        "Candle Catalogue": "https://raw.githubusercontent.com/jitu0426/Hem-Export-Catalogue/main/Candle%20Catalogue.xlsx",
    }
    CASE_SIZE_PATH = os.path.join(BASE_DIR, "Case Size.xlsx")

    GLOBAL_COLUMN_MAPPING = {
        "Category": "Category", "Sub-Category": "Subcategory", "Item Name": "ItemName",
        "ItemName": "ItemName", "Description": "Fragrance", "SKU Code": "SKU Code",
        "New Product ( Indication )": "IsNew"
    }
    NO_SELECTION_PLACEHOLDER = "Select..."

    # --- 6. PDFKIT CONFIG ---
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
            if found_path: CONFIG = pdfkit.configuration(wkhtmltopdf=found_path)
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

    # --- 7. TEMPLATE MANAGEMENT ---
    def load_saved_templates():
        if not os.path.exists(SAVED_TEMPLATES_FILE): return {}
        try: 
            with open(SAVED_TEMPLATES_FILE, 'r') as f: return json.load(f)
        except: return {}

    def save_template_to_disk(name, cart_items):
        templates = load_saved_templates()
        templates[name] = cart_items
        try:
            with open(SAVED_TEMPLATES_FILE, 'w') as f: json.dump(templates, f, indent=4)
            st.toast(f"Template '{name}' saved!", icon="💾")
        except Exception as e:
            st.error(f"Failed to save template: {e}")

    @st.cache_data(show_spinner="Syncing Data from GitHub & Cloudinary...")
    def load_data_cached(_dummy_timestamp):
        all_data = []
        required_output_cols = ['Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'Catalogue', 'Packaging', 'ImageB64', 'ProductID', 'IsNew']
        
        # --- A. Updated Cloudinary Setup (Folder-Aware Mapping) ---
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
                # Keep the full path: "Catalogue/Category/Item"
                full_path = res['public_id'].lower().strip()
                # Store it in the map
                cloudinary_map[full_path] = res['secure_url']
                
                # Also store just the item name as a backup
                item_only = full_path.split('/')[-1]
                cloudinary_map[f"backup_{clean_key(item_only)}"] = res['secure_url']
                
        except Exception as e:
            st.warning(f"⚠️ Cloudinary Warning: {e}")
            cloudinary_map = {} 

        # B. Check Admin Database (Keep exact same)
        DB_PATH = os.path.join(BASE_DIR, "data", "database.json")
        IMAGE_DIR = os.path.join(BASE_DIR, "images")
        data_loaded_from_db = False

        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, 'r') as f: db_data = json.load(f)
                if db_data.get("products"):
                    df = pd.DataFrame(db_data["products"])
                    df.rename(columns={"SKUCode": "SKU Code"}, inplace=True)
                    for col in required_output_cols:
                        if col not in df.columns: df[col] = '' if col != 'IsNew' else 0
                    
                    df['Packaging'] = 'Default Packaging'
                    df["ImageB64"] = "" 
                    df["ProductID"] = [f"PID_{str(uuid.uuid4())[:8]}" for _ in range(len(df))]
                    
                    for index, row in df.iterrows():
                        sku = str(row.get('SKU Code', '')).strip()
                        local_img_path = os.path.join(IMAGE_DIR, f"{sku}.jpg")
                        if os.path.exists(local_img_path):
                            df.loc[index, "ImageB64"] = get_image_as_base64_str(local_img_path, resize=True, max_size=(800, 800))
                        else:
                            # MATCHING LOGIC FOR DB SECTION
                            cat_path = f"{str(row['Catalogue']).lower().strip()}/{str(row['Category']).lower().strip()}/{str(row['ItemName']).lower().strip()}"
                            if cat_path in cloudinary_map:
                                url = cloudinary_map[cat_path]
                                df.loc[index, "ImageB64"] = get_image_as_base64_str(url.replace("/upload/", "/upload/w_800,q_auto/"), max_size=None)
                    
                    return df[required_output_cols]
            except Exception as e:
                print(f"Admin DB Load Failed: {e}. Falling back to Excel.")
                data_loaded_from_db = False

        # C. Excel/GitHub Fallback (UPDATED MATCHING)
        if not data_loaded_from_db:
            for catalogue_name, path_ref in CATALOGUE_PATHS.items():
                target_path = path_ref
                if str(path_ref).startswith("http"):
                    target_path = f"{path_ref}?v={_dummy_timestamp}"
                elif not os.path.exists(path_ref):
                    continue 

                try:
                    df = pd.read_excel(target_path, sheet_name=0, dtype=str, engine="openpyxl")
                    df = df.fillna("") 
                    df.columns = [str(c).strip() for c in df.columns]
                    df.rename(columns={k.strip(): v for k, v in GLOBAL_COLUMN_MAPPING.items() if k.strip() in df.columns}, inplace=True)
                    df['Catalogue'] = catalogue_name; df['Packaging'] = 'Default Packaging'; df["ImageB64"] = ""; df["ProductID"] = [f"PID_{str(uuid.uuid4())[:8]}" for _ in range(len(df))]; df['IsNew'] = pd.to_numeric(df.get('IsNew', 0), errors='coerce').fillna(0).astype(int)
                    for col in required_output_cols:
                        if col not in df.columns: df[col] = '' if col != 'IsNew' else 0

                    if cloudinary_map:
                        for index, row in df.iterrows():
                            # --- CONSTRUCT FOLDER PATH ---
                            # Structure: catalogue name / category name / item name
                            full_target_path = f"{str(row['Catalogue']).lower().strip()}/{str(row['Category']).lower().strip()}/{str(row['ItemName']).lower().strip()}"
                            
                            found_url = None
                            # 1. Try exact folder path match
                            if full_target_path in cloudinary_map:
                                found_url = cloudinary_map[full_target_path]
                            
                            # 2. Try Item Name match (backup)
                            if not found_url:
                                item_key = f"backup_{clean_key(row['ItemName'])}"
                                if item_key in cloudinary_map:
                                    found_url = cloudinary_map[item_key]

                            # 3. Fuzzy match (last resort)
                            if not found_url:
                                best_score = 0
                                row_item_name = str(row['ItemName']).lower().strip()
                                for cloud_path, url in cloudinary_map.items():
                                    cloud_item_name = cloud_path.split('/')[-1]
                                    score = fuzz.token_sort_ratio(row_item_name, cloud_item_name)
                                    if score > best_score and score > 80:
                                        best_score = score
                                        found_url = url

                            if found_url:
                                optimized_url = found_url.replace("/upload/", "/upload/w_800,q_auto/")
                                df.loc[index, "ImageB64"] = get_image_as_base64_str(optimized_url, max_size=None)
                    
                    all_data.append(df[required_output_cols])
                except Exception as e: st.error(f"Error reading {catalogue_name}: {e}")

            if not all_data: return pd.DataFrame(columns=required_output_cols)
            full_df = pd.concat(all_data, ignore_index=True)
            return full_df

    # --- 10. PDF GENERATOR ---
    PRODUCT_CARD_TEMPLATE = """
    <div class="product-card" style="width: 23%; float: left; margin: 10px 1%; padding: 8px; box-sizing: border-box; page-break-inside: avoid; background-color: #fcfcfc; border: 1px solid #E5C384; border-radius: 5px; text-align: center; height: 230px; overflow: hidden; display: flex; flex-direction: column;">
        <div style="font-family: sans-serif; font-size: 7pt; color: #888; text-transform: uppercase; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 0 0 auto;">
            {category_name}
        </div>
        
        <div style="height: 150px; width: 100%; background-color: white; position: relative; display: flex; align-items: center; justify-content: center; margin-bottom: 5px; flex: 0 0 auto;">
            {new_badge_html}
            {image_html}
        </div>
        
        <div style="flex: 1 1 auto; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 2px 0;">
            <h4 style="margin: 0; font-size: {font_size}; color: #000; line-height: 1.1; font-weight: bold; font-family: serif; word-wrap: break-word;">
                <span style="color: #007bff; margin-right: 4px;">{ref_no}.</span>{item_name}
            </h4>
        </div>
    </div>
    """
    
    def generate_story_html(story_img_1_b64):
        text_block_1 = """The universe of incense and smudging is extremely sensory and spiritual one. Whether it's cleansing a revered space with smoky white sage, relieving stress in the haze of palo santo or experiencing occult with our esoteric products, we make your aromatic journey more positive and magical with our widest range of ethically sourced perfumed products."""
        text_journey_1 = """HEM as a brand was founded in 1983 and is known globally for its most comprehensive variety of innovative fragrances. It also has the distinction of being the largest exporter of perfumed incense from India to over 70+ countries across the globe. Our strong belief in the spirit of innovation and creativity has helped us rank as the best incense manufacturing company in India and across the world"""
        
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
        </div>
        """
        return html

    def generate_table_of_contents_html(df_sorted):
        toc_html = """
        <style>
            /* Reset for Index Pages */
            .index-page-container {
                page-break-before: always;
                padding: 15mm 10mm;
                font-family: sans-serif;
                background-color: #ffffff;
                min-height: 270mm;
            }

            /* Main Header matching the screenshot style */
            .index-main-header {
                background-color: #333;
                color: #ffffff;
                text-align: center;
                padding: 15px 0;
                font-size: 24pt;
                font-weight: bold;
                text-transform: uppercase;
                margin-bottom: 30px;
                letter-spacing: 1px;
            }

            .index-grid {
                display: block;
                width: 100%;
                clear: both;
            }

            /* 4-Column Grid for professional spacing */
            a.index-card {
                display: inline-block;
                width: 22%;
                margin: 1%;
                height: 220px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                text-decoration: none;
                vertical-align: top;
                overflow: hidden;
                background-color: #fff;
                transition: transform 0.2s;
            }

            .index-card-img-box {
                width: 100%;
                height: 160px;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #ffffff;
                padding: 10px;
                box-sizing: border-box;
            }

            .index-card-img-box img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }

            .index-no-img {
                color: #ccc;
                font-size: 10pt;
                font-weight: bold;
                text-transform: uppercase;
            }

            /* Bottom label matching the theme */
            .index-card-title {
                height: 60px;
                background-color: #b30000;
                color: #ffffff;
                font-size: 9pt;
                font-weight: bold;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 5px;
                text-transform: uppercase;
                line-height: 1.2;
            }

            .clearfix::after {
                content: "";
                clear: both;
                display: table;
            }
        </style>
        <div id="main-index">
        """

        catalogues = df_sorted['Catalogue'].unique()

        for catalogue_name in catalogues:
            # Each catalogue starts on a fresh page with the black header
            toc_html += f'<div class="index-page-container">'
            toc_html += f'<div class="index-main-header">{catalogue_name}</div>'
            toc_html += '<div class="index-grid clearfix">'
            
            cat_df = df_sorted[df_sorted['Catalogue'] == catalogue_name]
            unique_categories = cat_df['Category'].unique()

            for category in unique_categories:
                # Find the first valid image in this category
                group = cat_df[cat_df['Category'] == category]
                rep_image = "" 
                for _, row in group.iterrows():
                    img_str = row.get('ImageB64', '')
                    if img_str and len(str(img_str)) > 100: 
                        rep_image = img_str
                        break 

                safe_id = create_safe_id(category)
                
                # Use real <img> tag instead of background-image for better PDF rendering
                image_html = f'<img src="data:image/jpeg;base64,{rep_image}">' if rep_image else '<span class="index-no-img">No Image</span>'
                
                toc_html += f"""
                    <a href="#category-{safe_id}" class="index-card">
                        <div class="index-card-img-box">
                            {image_html}
                        </div>
                        <div class="index-card-title">{category}</div>
                    </a>
                """
            
            toc_html += '</div></div>' # Close index-grid and index-page-container

        toc_html += "</div>"
        return toc_html
    def generate_pdf_html(df_sorted, customer_name, logo_b64, case_selection_map):
        def load_img_robust(fname, specific_full_path=None, resize=False, max_size=(500,500)):
            paths_to_check = []
            if specific_full_path: paths_to_check.append(specific_full_path)
            paths_to_check.append(os.path.join(BASE_DIR, "assets", fname))
            paths_to_check.append(os.path.join(BASE_DIR, fname))
            found_path = None
            for p in paths_to_check:
                if os.path.exists(p):
                    found_path = p
                    break
            if found_path: return get_image_as_base64_str(found_path, resize=resize, max_size=max_size)
            return "" 

        cover_url = "https://res.cloudinary.com/dnoepbfbr/image/upload/v1769517106/Cover_Page.jpg"
        cover_bg_b64 = get_image_as_base64_str(cover_url)
        if not cover_bg_b64: cover_bg_b64 = load_img_robust("cover page.png", resize=False)

        journey_url = "https://res.cloudinary.com/dnoepbfbr/image/upload/v1769517106/image-journey.jpg" 
        story_img_1_b64 = get_image_as_base64_str(journey_url, max_size=(600,600))
        if not story_img_1_b64: story_img_1_b64 = load_img_robust("image-journey.png", specific_full_path=STORY_IMG_1_PATH, resize=True, max_size=(600,600))

        watermark_b64 = load_img_robust("watermark.png", resize=False)

        CSS_STYLES = f"""
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8">
            <style>
            @page {{ size: A4; margin: 0; }}
            * {{ box-sizing: border-box; }} 
            html, body {{ margin: 0 !important; padding: 0 !important; width: 100% !important; background-color: transparent !important; }}
            #watermark-layer {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; background-image: url('data:image/png;base64,{watermark_b64}'); background-repeat: repeat; background-position: center center; background-size: cover; background-color: transparent; }}
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
            .category-block {{ display: block; font-size: 0; clear: both; page-break-inside: auto; margin-bottom: 20px; width: 100%; page-break-before: always; }}
            h1.catalogue-heading + .category-block {{ page-break-before: avoid !important; }}
            .product-card {{ display: inline-block; width: 23%; margin: 10px 1%; vertical-align: top; font-size: 12pt; padding: 5px; box-sizing: border-box; background-color: #fcfcfc; border: 1px solid #E5C384; border-radius: 5px; text-align: center; position: relative; overflow: hidden; height: 180px; page-break-inside: avoid; }}
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
                    if k.lower() in data_k.lower(): return str(row_data[data_k])
            return "-"

        current_catalogue = None; current_category = None; current_subcategory = None
        is_first_item = True; category_open = False

        for index, row in df_sorted.iterrows():
            if row['Catalogue'] != current_catalogue:
                if category_open: html_parts.append('</div>'); category_open = False 
                current_catalogue = row['Catalogue']
                current_category = None; current_subcategory = None
                break_style = 'style="page-break-before: always;"' if not is_first_item else ""
                html_parts.append(f'<div style="clear:both;"></div><h1 class="catalogue-heading" {break_style}>{current_catalogue}</h1>')
                is_first_item = False

            if row['Category'] != current_category:
                if category_open: html_parts.append('</div>') 
                current_category = row['Category']
                current_subcategory = None
                safe_category_id = create_safe_id(current_category)
                row_data = case_selection_map.get(current_category, {})

                html_parts.append('<div class="category-block clearfix">') 
                category_open = True
                html_parts.append(f'<h2 class="category-heading" id="category-{safe_category_id}"><a href="#main-index" style="float: right; font-size: 10px; color: #555; text-decoration: none; font-weight: normal; font-family: sans-serif; margin-top: 4px;">BACK TO INDEX &uarr;</a>{current_category}</h2>')
                
                if row_data:
                    desc = row_data.get('Description', '')
                    if desc: html_parts.append(f'<div class="case-size-info"><strong>Case Size:</strong> {desc}</div>')
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

            img_b64 = row.get("ImageB64", "")
            mime_type = 'image/png' if (img_b64 and len(img_b64) > 20 and img_b64[:20].lower().find('i') != -1) else 'image/jpeg'
            image_html_content = f'''<img src="data:{mime_type};base64,{img_b64}" style="max-height: 145px; max-width: 95%; width: auto; height: auto; object-fit: contain;" alt="{row.get("ItemName", "")}">''' if img_b64 else '<div style="color:#ccc; font-size:10px; padding-top: 60px;">NO IMAGE</div>'
            
            packaging_text = row.get('Packaging', '').replace('Default Packaging', '')
            sku_info = f"SKU: {row.get('SKU Code', 'N/A')}"
            fragrance_list = [f.strip() for f in row.get('Fragrance', '').split(',') if f.strip() and f.strip().upper() != 'N/A']
            fragrance_output = f"Fragrance: {', '.join(fragrance_list)}" if fragrance_list else "No fragrance info listed"
            new_badge_html = """<div style="position: absolute; top: 0; right: 0; background-color: #dc3545; color: white; font-size: 8px; font-weight: bold; padding: 2px 8px; border-radius: 0 0 0 5px; z-index: 10;">NEW</div>""" if row.get('IsNew') == 1 else ""

            item_name_text = row.get('ItemName', 'N/A')
            name_len = len(str(item_name_text))
            font_size = "9pt" if name_len < 35 else ("8pt" if name_len < 55 else "7pt")

            if PRODUCT_CARD_TEMPLATE:
                card_output = PRODUCT_CARD_TEMPLATE.format(
                    new_badge_html=new_badge_html,
                    image_html=image_html_content,
                    item_name=item_name_text,
                    category_name=row['Category'],
                    ref_no=index+1,
                    packaging=packaging_text,
                    sku_info=sku_info,
                    fragrance=fragrance_output,
                    font_size=font_size
                )
                html_parts.append(card_output)
        
        if category_open: html_parts.append('</div>')
        html_parts.append('<div style="clear: both;"></div></div></body></html>')
        return "".join(html_parts)

    def generate_excel_file(df_sorted, customer_name, case_selection_map):
        output = io.BytesIO()
        excel_rows = []
        for idx, row in df_sorted.iterrows():
            cat = row['Category']
            suffix = ""; cbm = 0.0
            if cat in case_selection_map:
                case_data = case_selection_map[cat]
                for k in case_data.keys():
                    if "suffix" in k.lower(): suffix = str(case_data[k]).strip()
                    if "cbm" in k.lower(): 
                        try: cbm = round(float(case_data[k]), 3)
                        except: cbm = 0.0
                if suffix == 'nan': suffix = ""
            full_name = str(row['ItemName']).strip()
            if suffix: full_name = f"{full_name} {suffix}"
            excel_rows.append({ "Ref No": idx + 1, "Category": cat, "Product Name + Carton Name": full_name, "Carton per CBM": cbm, "Order Quantity (Cartons)": 0, "Total CBM": 0 })
            
        df_excel = pd.DataFrame(excel_rows)
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Order Sheet', startrow=7) 
            workbook = writer.book; worksheet = writer.sheets['Order Sheet']
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
            worksheet.write('B3', 'CONTAINER TYPE', header_fmt)
            worksheet.write('C3', 'ESTIMATED CONTAINERS', header_fmt)
            worksheet.write('B4', '20 FT (30 CBM)', workbook.add_format({'border': 1}))
            worksheet.write('B5', '40 FT (60 CBM)', workbook.add_format({'border': 1}))
            worksheet.write('B6', '40 FT HC (70 CBM)', workbook.add_format({'border': 1}))
            worksheet.write_formula('C4', '=$C$2/30', count_fmt)
            worksheet.write_formula('C5', '=$C$2/60', count_fmt)
            worksheet.write_formula('C6', '=$C$2/70', count_fmt)

            for col_num, value in enumerate(df_excel.columns): worksheet.write(7, col_num, value, header_fmt)
            worksheet.set_column('A:A', 8); worksheet.set_column('B:B', 25); worksheet.set_column('C:C', 50); worksheet.set_column('D:F', 15) 
            for i in range(len(df_excel)):
                row_idx = i + 9 
                worksheet.write(row_idx-1, 4, 0, input_fmt) 
                worksheet.write_formula(row_idx-1, 5, f'=D{row_idx}*E{row_idx}', locked_fmt)
        return output.getvalue()

    # --- 11. CART UTILS ---
    def add_to_cart(selected_df):
        current_pids = {item["ProductID"] for item in st.session_state.cart}
        new_items = []
        columns_to_keep = ['SKU Code', 'ItemName', 'Category', 'Subcategory', 'Fragrance', 'Packaging', 'SerialNo', 'ImageB64', 'Catalogue', 'ProductID', 'IsNew']
        if isinstance(selected_df, pd.Series): selected_df = pd.DataFrame([selected_df])
        for _, row in selected_df.iterrows():
            if row.get("ProductID") and row["ProductID"] not in current_pids:
                new_items.append({col: row.get(col, '') for col in columns_to_keep})
        if new_items:
            st.session_state.cart.extend(new_items)
            st.session_state.gen_pdf_bytes = None
            st.session_state.gen_excel_bytes = None
            st.toast(f"Added {len(new_items)} items to cart!", icon="🛒")

    def remove_from_cart(pids_to_remove):
        if pids_to_remove: st.session_state.cart = [i for i in st.session_state.cart if i.get("ProductID") not in pids_to_remove]
        st.session_state.gen_pdf_bytes = None; st.session_state.gen_excel_bytes = None

    def add_selected_visible_to_cart(df_visible):
        pid_map = st.session_state.get('master_pid_map', {})
        visible_pids = set(df_visible['ProductID'].tolist())
        columns_to_keep = ['SKU Code', 'ItemName', 'Category', 'Subcategory', 'Fragrance', 'Packaging', 'SerialNo', 'ImageB64', 'Catalogue', 'ProductID', 'IsNew']
        current_cart_pids = {item["ProductID"] for item in st.session_state.cart if "ProductID" in item}
        new_items = []
        for key, is_checked in st.session_state.items():
            if key.startswith("checkbox_") and is_checked:
                pid = key.replace("checkbox_", "")
                if pid in visible_pids and pid not in current_cart_pids:
                    product_data = pid_map.get(pid)
                    if product_data:
                        new_items.append({col: pd.Series(product_data).get(col, '') for col in columns_to_keep})
        if new_items:
            st.session_state.cart.extend(new_items)
            st.session_state.gen_pdf_bytes = None; st.session_state.gen_excel_bytes = None
            st.toast(f"Added {len(new_items)} selected items!", icon="🛒")
        else: st.toast("No items selected.", icon="ℹ️")

    def clear_filters_dropdown():
        st.session_state.selected_catalogue_dropdown = NO_SELECTION_PLACEHOLDER
        st.session_state.selected_categories_multi = []
        st.session_state.selected_subcategories_multi = []
        st.session_state.item_search_query = ""
        for key in ["item_search_input", "category_multiselect", "subcategory_multiselect"]:
            if key in st.session_state: del st.session_state[key]

    def display_product_list(df_to_show, is_global_search=False):
        selected_pids = {item.get("ProductID") for item in st.session_state.cart if "ProductID" in item}
        if df_to_show.empty: st.info("No products match filters/search."); return
        grouped_by_category = df_to_show.groupby('Category')
        for category, cat_group_df in grouped_by_category:
            cat_count = len(cat_group_df)
            with st.expander(f"{category} ({cat_count})", expanded=is_global_search):
                c1, c2 = st.columns([3,1])
                with c2:
                    if st.button(f"Add All {cat_count}", key=f"btn_add_cat_{create_safe_id(category)}"):
                        add_to_cart(cat_group_df)
                for subcategory, subcat_group_df in cat_group_df.groupby('Subcategory'):
                    sub_str = str(subcategory).strip()
                    if sub_str.upper() != 'N/A' and sub_str.lower() != 'nan': 
                        st.markdown(f"<div class='subcat-header'>{sub_str} ({len(subcat_group_df)})</div>", unsafe_allow_html=True)
                    col_name, col_check = st.columns([8, 1])
                    for idx, row in subcat_group_df.iterrows():
                        pid = row['ProductID']; unique_key = f"checkbox_{pid}"
                        name_display = f"**{row['ItemName']}**"
                        if row.get('IsNew') == 1: name_display += " <span style='color:red; font-size:10px; border:1px solid red; padding:1px 3px; border-radius:3px;'>NEW</span>"
                        col_name.markdown(name_display, unsafe_allow_html=True)
                        col_check.checkbox("Select", value=pid in selected_pids, key=unique_key, label_visibility="hidden")

    # --- 12. MAIN APP LOGIC ---
    if True: 
        for key in ["cart", "gen_pdf_bytes", "gen_excel_bytes", "selected_categories_multi", "selected_subcategories_multi"]:
            if key not in st.session_state: st.session_state[key] = [] if "multi" in key or key=="cart" else None
        if 'selected_catalogue_dropdown' not in st.session_state: st.session_state.selected_catalogue_dropdown = NO_SELECTION_PLACEHOLDER
        if 'item_search_query' not in st.session_state: st.session_state.item_search_query = ""
        if 'data_timestamp' not in st.session_state: st.session_state.data_timestamp = time.time()

        products_df = load_data_cached(st.session_state.data_timestamp)
        st.session_state['master_pid_map'] = {row['ProductID']: row.to_dict() for _, row in products_df.iterrows()}

        with st.sidebar:
            st.header("📂 Manage Templates")
            with st.expander("Save Current Cart"):
                new_temp_name = st.text_input("Template Name")
                if st.button("Save Template"):
                    if new_temp_name: save_template_to_disk(new_temp_name, st.session_state.cart)
            saved_temps = load_saved_templates()
            if saved_temps:
                with st.expander("Load Template"):
                    sel_temp = st.selectbox("Select", list(saved_temps.keys()))
                    if st.button("Load"):
                        st.session_state.cart = saved_temps[sel_temp]
                        st.rerun()
            st.markdown("---")
            if st.button("Refresh Cloudinary & Excel"):
                st.session_state.data_timestamp = time.time()
                st.cache_data.clear()
                st.rerun()

        st.title("HEM PRODUCT CATALOGUE")
        tab1, tab2, tab3 = st.tabs(["1. Filter", "2. Review", "3. Export"])
        
        with tab1:
            if products_df.empty: st.error("No Data available. Check GitHub paths or Admin Sync.")
            else:
                final_df = products_df.copy()
                search_term = st.text_input("🔍 Global Search (Name or SKU)", value=st.session_state.item_search_query, key="item_search_input").lower()
                st.session_state.item_search_query = search_term
                if search_term:
                    final_df = products_df[products_df['ItemName'].str.lower().str.contains(search_term) | products_df['SKU Code'].str.lower().str.contains(search_term)]
                    display_product_list(final_df, is_global_search=True)
                else:
                    c_f, c_b = st.columns([3, 1])
                    with c_f:
                        cat_opts = [NO_SELECTION_PLACEHOLDER] + products_df['Catalogue'].unique().tolist()
                        sel_cat = st.selectbox("Catalogue", cat_opts, key="selected_catalogue_dropdown")
                        if sel_cat != NO_SELECTION_PLACEHOLDER:
                            cat_subset = products_df[products_df['Catalogue'] == sel_cat]
                            category_options = cat_subset['Category'].unique().tolist()
                            sel_cats = st.multiselect("Category", category_options, key="category_multiselect")
                            if sel_cats:
                                filtered_dfs = []
                                for c in sel_cats:
                                    cat_data = cat_subset[cat_subset['Category'] == c]
                                    clean_subs = [s for s in cat_data['Subcategory'].unique() if str(s).strip().upper() not in ['N/A', 'NAN', '']]
                                    if clean_subs:
                                        sel_subs = st.multiselect(f"Sub-Category for {c}", clean_subs, default=clean_subs, key=f"sub_{create_safe_id(c)}")
                                        filtered_dfs.append(cat_data[cat_data['Subcategory'].isin(sel_subs) | cat_data['Subcategory'].isin(['', 'N/A', 'nan'])])
                                    else: filtered_dfs.append(cat_data)
                                final_df = pd.concat(filtered_dfs) if filtered_dfs else cat_subset
                            else: final_df = cat_subset
                    with c_b:
                        if st.button("ADD SELECTED", type="primary"): add_selected_visible_to_cart(final_df)
                        if st.button("ADD FILTERED", type="secondary"): add_to_cart(final_df)
                        st.button("Clear", on_click=clear_filters_dropdown)
                    if sel_cat != NO_SELECTION_PLACEHOLDER: display_product_list(final_df)

        with tab2:
            if st.session_state.cart:
                cart_df = pd.DataFrame(st.session_state.cart)
                cart_df['Remove'] = False
                edited = st.data_editor(cart_df[['Catalogue', 'Category', 'ItemName', 'Remove']], hide_index=True, use_container_width=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Remove Selected Items"):
                        pids_to_rem = cart_df.loc[edited[edited['Remove']].index, 'ProductID'].tolist()
                        remove_from_cart(pids_to_rem)
                        st.rerun()
                with c2:
                    if st.button("Empty Entire Cart", type="primary"):
                        st.session_state.cart = []
                        st.session_state.gen_pdf_bytes = None
                        st.session_state.gen_excel_bytes = None
                        st.rerun()
            else: st.info("Cart Empty")

        with tab3:
            if not st.session_state.cart: st.info("Cart is empty.")
            else:
                st.markdown("### 1. Configure Order")
                
                # Load Case Sizes (Try Admin DB then Excel)
                full_case_size_df = pd.DataFrame()
                if os.path.exists(os.path.join(BASE_DIR, "data", "database.json")):
                    try: 
                        with open(os.path.join(BASE_DIR, "data", "database.json")) as f: 
                            full_case_size_df = pd.DataFrame(json.load(f).get("case_sizes", []))
                    except: pass
                
                if full_case_size_df.empty and os.path.exists(CASE_SIZE_PATH):
                    try: full_case_size_df = pd.read_excel(CASE_SIZE_PATH, dtype=str)
                    except: pass

                # Map Cart Categories to Case Sizes
                selection_map = {}
                cart_categories = sorted(list(set([item['Category'] for item in st.session_state.cart])))
                
                if not full_case_size_df.empty:
                    # Clean columns
                    full_case_size_df.columns = [c.strip() for c in full_case_size_df.columns]
                    suffix_col = next((c for c in full_case_size_df.columns if "suffix" in c.lower()), None)
                    cbm_col = next((c for c in full_case_size_df.columns if "cbm" in c.lower()), "CBM")
                    
                    if suffix_col:
                        for cat in cart_categories:
                            options = full_case_size_df[full_case_size_df['Category'] == cat].copy()
                            if not options.empty:
                                options['DisplayLabel'] = options.apply(lambda x: f"{x.get(suffix_col, '')} (CBM: {x.get(cbm_col, '')})", axis=1)
                                label_list = options['DisplayLabel'].tolist()
                                selected_label = st.selectbox(f"Select Case Size for **{cat}**", label_list, key=f"select_case_{create_safe_id(cat)}")
                                selected_row = options[options['DisplayLabel'] == selected_label].iloc[0]
                                selection_map[cat] = selected_row.to_dict()
                            else: st.warning(f"No Case Size options found for: {cat}")
                    else: st.error("Case Size file missing 'Carton Suffix' column.")

                st.markdown("---")
                name = st.text_input("Client Name", "Valued Client")
                
                if st.button("Generate Files", type="primary", use_container_width=True):
                    df_final = pd.DataFrame(st.session_state.cart)
                    # Ensure schema
                    for col in ['Catalogue', 'Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'ImageB64', 'Packaging', 'IsNew']:
                        if col not in df_final.columns: df_final[col] = ''
                    
                    df_final['SerialNo'] = range(1, len(df_final)+1)
                    
                    st.toast("Generating Excel...", icon="📊")
                    st.session_state.gen_excel_bytes = generate_excel_file(df_final, name, selection_map)
                    
                    st.toast("Generating PDF...", icon="📄")
                    try:
                        logo = get_image_as_base64_str(LOGO_PATH, resize=True, max_size=(200,100)) 
                        html = generate_pdf_html(df_final, name, logo, selection_map)
                        
                        if CONFIG:
                            options = { 'page-size': 'A4', 'margin-top': '0mm', 'margin-right': '0mm', 'margin-bottom': '0mm', 'margin-left': '0mm', 'encoding': "UTF-8", 'no-outline': None, 'enable-local-file-access': None, 'disable-smart-shrinking': None, 'print-media-type': None }
                            st.session_state.gen_pdf_bytes = pdfkit.from_string(html, False, configuration=CONFIG, options=options)
                        elif HAS_WEASYPRINT:
                            st.session_state.gen_pdf_bytes = HTML(string=html, base_url=BASE_DIR).write_pdf()
                        else:
                            st.error("No PDF engine found.")
                    except Exception as e:
                        st.error(f"PDF Error: {e}")

                if st.session_state.gen_pdf_bytes: 
                    st.download_button("⬇️ Download PDF Catalogue", st.session_state.gen_pdf_bytes, f"{name}_catalogue.pdf", type="primary", use_container_width=True)
                if st.session_state.gen_excel_bytes: 
                    st.download_button("⬇️ Download Excel Order Sheet", st.session_state.gen_excel_bytes, f"{name}_order.xlsx", type="secondary", use_container_width=True)

except Exception as e:
    st.error(f"🚨 CRITICAL ERROR: {e}")


