
import streamlit as st
import pandas as pd
import pdfkit
import base64
from pathlib import Path
from datetime import datetime
import io
import os
import json
import numpy as np
import time
import uuid
import difflib
from fuzzywuzzy import fuzz
from PIL import Image
import platform
import subprocess
import os
import cloudinary
import cloudinary.api
from PIL import Image
import io
import requests
import base64
import os

def get_image_as_base64_str(url_or_path, resize=None, max_size=None):
    """
    Converts an image (URL or local path) to Base64, handling resizing options.
    
    Args:
        url_or_path (str): URL or file path to the image.
        resize (tuple): Force dimensions (width, height). May stretch image.
        max_size (tuple): Max dimensions (width, height). Maintains aspect ratio.
    """
    if not url_or_path: 
        return ""
    
    try:
        # A. LOAD IMAGE (Handle both URL and Local File)
        if str(url_or_path).startswith("http"):
            response = requests.get(url_or_path, timeout=5)
            if response.status_code != 200: return ""
            img = Image.open(io.BytesIO(response.content))
        else:
            # Handle local file paths
            if not os.path.exists(url_or_path): return ""
            img = Image.open(url_or_path)
            
        # B. RESIZE LOGIC
        # Priority 1: max_size (Best for catalogues, keeps aspect ratio)
        if max_size:
            img.thumbnail(max_size)
        # Priority 2: resize (Forces strict dimensions, might stretch)
        elif resize:
            img = img.resize(resize) 
            
        # C. CONVERT TO BASE64
        buffered = io.BytesIO()
        # Convert to RGB to ensure compatibility (e.g. if saving PNG as JPEG)
        if img.mode in ("RGBA", "P"): 
            img = img.convert("RGB")
            
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode()
        
    except Exception as e:
        print(f"Error processing image {url_or_path}: {e}")
        return ""
    
# Configure
cloudinary.config(
    cloud_name = "dddtoqebz",
    api_key = "923925294516228",
    api_secret = "-vc8Kem3uM4LgH-LXSu998r-5L8",
    secure = True
)

# Test
try:
    print("Testing connection to 'dddtoqebz'...")
    cloudinary.api.ping()
    print("✅ SUCCESS! Your API keys are working perfectly.")
except Exception as e:
    print(f"❌ ERROR: {e}")

# --- 0. AUTO-FIX FOR LIGHT THEME ---
def force_light_theme_setup():
    config_dir = ".streamlit"
    config_path = os.path.join(config_dir, "config.toml")
    if not os.path.exists(config_dir): os.makedirs(config_dir)
    if not os.path.exists(config_path):
        theme_content = "[theme]\nbase='light'\nprimaryColor='#007bff'\nbackgroundColor='#ffffff'\nsecondaryBackgroundColor='#f0f2f6'\ntextColor='#000000'\nfont='sans serif'"
        with open(config_path, "w") as f: f.write(theme_content.strip())

force_light_theme_setup()

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="HEM PRODUCT CATALOGUE", page_icon="🛍️", layout="wide")

# --- 2. GLOBAL STYLES ---
st.markdown("""
    <style>
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        div[data-testid="stDataEditor"] { background-color: #ffffff !important; border: 1px solid #ced4da; }
        
        /* Button Styles */
        button[kind="primary"] {
            background-color: #ff9800 !important; color: white !important; border: none; font-weight: bold;
        }
        button[kind="secondary"] {
            background-color: #007bff !important; color: white !important; border: none; font-weight: bold;
        }

        /* Subcategory Header */
        .subcat-header {
            background-color: #f8f9fa;
            padding: 5px 10px;
            margin: 10px 0 5px 0;
            border-left: 4px solid #007bff; 
            font-weight: bold;
            color: #333;
        }
    </style>
""", unsafe_allow_html=True)

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates") 
SAVED_TEMPLATES_FILE = os.path.join(BASE_DIR, "saved_templates.json")

# --- IMAGES ---
STORY_IMG_1_PATH = os.path.join(BASE_DIR, "image-journey.png") 
COVER_IMG_PATH = os.path.join(BASE_DIR, "assets", "cover page.png")
WATERMARK_IMG_PATH = os.path.join(BASE_DIR, "assets", "watermark.png") 
IMAGE_DIR = os.path.join(BASE_DIR, "images") 

CATALOGUE_PATHS = {
    "HEM Product Catalogue": os.path.join(BASE_DIR, "Hem catalogue.xlsx"),
    "Sacred Elements Catalogue": os.path.join(BASE_DIR, "SacredElement.xlsx"),
    "Pooja Oil Catalogue": os.path.join(BASE_DIR, "Pooja Oil Catalogue.xlsx"),
    "Candle Catalogue": os.path.join(BASE_DIR, "Candle Catalogue.xlsx"),
}

CASE_SIZE_PATH = os.path.join(BASE_DIR, "Case Size.xlsx")

GLOBAL_COLUMN_MAPPING = {
    "Category": "Category", "Sub-Category": "Subcategory", "Item Name": "ItemName",
    "ItemName": "ItemName", "Description": "Fragrance", "SKU Code": "SKU Code",
    "New Product ( Indication )": "IsNew"
}

NO_SELECTION_PLACEHOLDER = "Select..." 

# --- HELPER FUNCTIONS ---
def create_safe_id(text):
    return "".join(c for c in text.replace(' ', '-').lower() if c.isalnum() or c == '-').replace('--', '-')
@st.cache_data(show_spinner="Loading Catalogues & Syncing Images...")
def load_data():
    all_data = []
    required_output_cols = ['Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'Catalogue', 'Packaging', 'ImageURL', 'ProductID', 'IsNew']
    
    # --- 1. OPTIMIZED CLOUDINARY FETCH (WITH PAGINATION) ---
    cloudinary_map = {}
    try:
        # Check connection
        cloudinary.api.ping()
        
        # Fetch ALL images using pagination
        next_cursor = None
        while True:
            resources = cloudinary.api.resources(
                type="upload", 
                max_results=500, 
                next_cursor=next_cursor
            )
            for res in resources.get('resources', []):
                public_id = res['public_id'].split('/')[-1]
                c_key = clean_key(public_id)
                cloudinary_map[c_key] = res['secure_url']
            
            if 'next_cursor' in resources:
                next_cursor = resources['next_cursor']
            else:
                break # No more images
                
        print(f"✅ Indexed {len(cloudinary_map)} images from Cloudinary.")
        
    except Exception as e:
        st.warning(f"⚠️ Cloudinary Error: {e} - Proceeding with text only.")
        cloudinary_map = {}

    # --- 2. EXCEL PROCESSING ---
    for catalogue_name, excel_path in CATALOGUE_PATHS.items():
        if not os.path.exists(excel_path): continue
            
        try:
            df = pd.read_excel(excel_path, sheet_name=0, dtype=str)
            
            # Clean Columns
            df.columns = [str(c).strip() for c in df.columns]
            df.rename(columns={k.strip(): v for k, v in GLOBAL_COLUMN_MAPPING.items() if k.strip() in df.columns}, inplace=True)
            
            # Add Defaults
            df['Catalogue'] = catalogue_name
            df['Packaging'] = 'Default Packaging'
            df["ImageURL"] = "" # Storing URL instead of Base64 for speed
            df["ProductID"] = [f"PID_{str(uuid.uuid4())[:8]}" for _ in range(len(df))]
            df['IsNew'] = pd.to_numeric(df.get('IsNew', 0), errors='coerce').fillna(0).astype(int)

            # Ensure columns exist
            for col in required_output_cols:
                if col not in df.columns: df[col] = '' if col != 'IsNew' else 0

            # --- 3. OPTIMIZED MATCHING LOGIC ---
            if cloudinary_map:
                # Pre-calculate clean keys for the dataframe to avoid re-cleaning in loops
                df['clean_key'] = df['ItemName'].apply(clean_key)
                
                for index, row in df.iterrows():
                    row_key = row['clean_key']
                    if not row_key: continue

                    found_url = None
                    
                    # A. FAST LOOKUP (O(1)) - Direct Match
                    if row_key in cloudinary_map:
                        found_url = cloudinary_map[row_key]
                    
                    # B. SLOW LOOKUP (O(N)) - Fuzzy Match (Only if exact match fails)
                    else:
                        # Extract keys to list for faster processing or use library
                        # We limit fuzzy matching to prevent timeouts
                        best_score = 0
                        # Optimization: Only compare against keys that share the first letter to reduce search space
                        # (Optional, but helps speed)
                        
                        for cloud_key, url in cloudinary_map.items():
                            # Quick logic: if length difference is huge, skip
                            if abs(len(row_key) - len(cloud_key)) > 5: continue
                            
                            score = fuzz.token_sort_ratio(row_key, cloud_key)
                            if score > 85: # Strict threshold
                                if score > best_score:
                                    best_score = score
                                    found_url = url
                        
                    if found_url:
                        # CRITICAL: We save the URL, not the Base64 image.
                        # We will convert to Base64 ONLY when generating the PDF.
                        df.at[index, "ImageURL"] = found_url

            all_data.append(df[required_output_cols])

        except Exception as e:
            st.error(f"Error reading {catalogue_name}: {e}")

    if not all_data: return pd.DataFrame(columns=required_output_cols)
    
    full_df = pd.concat(all_data, ignore_index=True)
    # Create master map for session state
    st.session_state['master_pid_map'] = {row['ProductID']: row.to_dict() for _, row in full_df.iterrows()}
    
    return full_df

def clean_key(text):
    if not isinstance(text, str): return ""
    text = text.lower().strip().replace(' ', '').replace('_', '').replace('-', '')
    for stop_word in ['catalogue', 'image', 'images', 'product', 'products', 'img']:
        text = text.replace(stop_word, '')
    return text

# --- PDFKIT CONFIG ---
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
        path_wkhtmltopdf = subprocess.check_output(['which', 'wkhtmltopdf']).decode('utf-8').strip()
        CONFIG = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
except Exception as e: print(f"PDFKit Config Error: {e}") 

# --- TEMPLATE FUNCTIONS ---
def load_saved_templates():
    if not os.path.exists(SAVED_TEMPLATES_FILE): return {}
    try: 
        with open(SAVED_TEMPLATES_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_template_to_disk(name, cart_items):
    templates = load_saved_templates()
    templates[name] = cart_items
    with open(SAVED_TEMPLATES_FILE, 'w') as f: json.dump(templates, f, indent=4)
    st.toast(f"Template '{name}' saved!", icon="💾")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    all_data = []
    required_output_cols = ['Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'Catalogue', 'Packaging', 'ImageB64', 'ProductID', 'IsNew']
    
    # --- DIAGNOSIS STEP 1: CLOUDINARY FETCH (FAIL-SAFE) ---
    cloudinary_map = {}
    try:
        # We try to ping. If this fails, we catch it and continue anyway.
        cloudinary.api.ping()
        
        resources = cloudinary.api.resources(type="upload", max_results=500)
        for res in resources.get('resources', []):
            public_id = res['public_id'].split('/')[-1] 
            c_key = clean_key(public_id)
            cloudinary_map[c_key] = res['secure_url']
            
    except Exception as e:
        # THIS FIXES THE "NO DATA" ERROR:
        # Instead of stopping, we just warn the user and keep going.
        st.warning(f"⚠️ Cloudinary Warning: Could not fetch images. ({e}) - Loading text data only.")
        cloudinary_map = {} # Continue with empty map

    # --- DIAGNOSIS STEP 2: EXCEL LOADING (ALWAYS RUNS) ---
    for catalogue_name, excel_path in CATALOGUE_PATHS.items():
        if not os.path.exists(excel_path): 
            st.error(f"File not found: {excel_path}")
            continue
            
        try:
            df = pd.read_excel(excel_path, sheet_name=0, dtype=str)
            df.columns = [str(c).strip() for c in df.columns]
            df.rename(columns={k.strip(): v for k, v in GLOBAL_COLUMN_MAPPING.items() if k.strip() in df.columns}, inplace=True)
            
            # Setup Defaults
            df['Catalogue'] = catalogue_name
            df['Packaging'] = 'Default Packaging'
            df["ImageB64"] = "" 
            df["ProductID"] = [f"PID_{str(uuid.uuid4())[:8]}" for _ in range(len(df))]
            df['IsNew'] = pd.to_numeric(df.get('IsNew', 0), errors='coerce').fillna(0).astype(int)

            # Ensure columns exist
            for col in required_output_cols:
                if col not in df.columns:
                    df[col] = '' if col != 'IsNew' else 0

            # --- IMAGE MATCHING (Only runs if Step 1 succeeded) ---
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
                        if best_score < 75: found_url = None

                    if found_url:
                        df.loc[index, "ImageB64"] = get_image_as_base64_str(found_url)
            
            all_data.append(df[required_output_cols])

        except Exception as e:
            st.error(f"Error reading Excel {catalogue_name}: {e}")

    # Final Check
    if not all_data: 
        return pd.DataFrame(columns=required_output_cols)
        
    full_df = pd.concat(all_data, ignore_index=True)
    st.session_state['master_pid_map'] = {row['ProductID']: row.to_dict() for _, row in full_df.iterrows()}
    return full_df

# --- CART UTILS ---
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
    added_count = 0; new_items = []
    for key, is_checked in st.session_state.items():
        if key.startswith("checkbox_") and is_checked:
            pid = key.replace("checkbox_", "")
            if pid not in visible_pids: continue
            product_data = pid_map.get(pid)
            if product_data and pid not in current_cart_pids:
                row_series = pd.Series(product_data) 
                new_items.append({col: row_series.get(col, '') for col in columns_to_keep})
                added_count += 1
    if new_items:
        st.session_state.cart.extend(new_items)
        st.session_state.gen_pdf_bytes = None; st.session_state.gen_excel_bytes = None
        st.toast(f"Added {added_count} selected items to cart!", icon="🛒")
    else: st.toast("No items selected.", icon="ℹ️")

def clear_filters_dropdown():
    st.session_state.selected_catalogue_dropdown = NO_SELECTION_PLACEHOLDER
    st.session_state.selected_categories_multi = []
    st.session_state.selected_subcategories_multi = []
    st.session_state.item_search_query = ""
    st.session_state['category_multiselect_prev'] = [] 
    
    # Safe deletion of keys
    if "item_search_input" in st.session_state: del st.session_state["item_search_input"] 
    if "category_multiselect" in st.session_state: del st.session_state["category_multiselect"]
    if "subcategory_multiselect" in st.session_state: del st.session_state["subcategory_multiselect"]
    
    # Note: st.rerun() is removed here because on_click handles the rerun automatically

def display_product_list(df_to_show, is_global_search=False):
    selected_pids = {item.get("ProductID") for item in st.session_state.cart if "ProductID" in item}
    if df_to_show.empty: st.info("No products match filters/search."); return

    grouped_by_category = df_to_show.groupby('Category')
    
    for category, cat_group_df in grouped_by_category:
        cat_count = len(cat_group_df)
        with st.expander(f"{category} ({cat_count})", expanded=is_global_search):
            c1, c2 = st.columns([3,1])
            with c2:
                if st.button(f"Add All {cat_count} items", key=f"btn_add_cat_{create_safe_id(category)}"):
                    add_to_cart(cat_group_df)

            for subcategory, subcat_group_df in cat_group_df.groupby('Subcategory'):
                if subcategory.strip().upper() != 'N/A' and subcategory.strip().lower() != 'nan': 
                    st.markdown(f"<div class='subcat-header'>{subcategory} ({len(subcat_group_df)})</div>", unsafe_allow_html=True)
                
                col_name, col_check = st.columns([8, 1])
                col_name.markdown('**Product Name**'); col_check.markdown('**Select**')
                st.markdown("<hr style='margin:0 0 5px 0; border-color:#ddd;'>", unsafe_allow_html=True) 
                
                for idx, row in subcat_group_df.iterrows():
                    pid = row['ProductID']; unique_key = f"checkbox_{pid}"; initial_checked = pid in selected_pids
                    name_display = f"**{row['ItemName']}**"
                    if row.get('IsNew') == 1: name_display += " <span style='color:red; font-size:10px; border:1px solid red; padding:1px 3px; border-radius:3px;'>NEW</span>"
                    with col_name: st.markdown(name_display, unsafe_allow_html=True)
                    if col_check.checkbox("Select", value=initial_checked, key=unique_key, label_visibility="hidden"):
                        pass

# --- PDF GENERATOR HELPERS ---
PRODUCT_CARD_TEMPLATE = """
<div class="product-card" style="width: 23%; float: left; margin: 10px 1%; padding: 5px; box-sizing: border-box; page-break-inside: avoid; background-color: #fcfcfc; border: 1px solid #E5C384; border-radius: 5px; text-align: center; position: relative; overflow: hidden; height: 180px;">
    <div style="font-family: sans-serif; font-size: 8pt; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 2px;">
        {category_name}
    </div>
    <div style="height: 110px; display: flex; align-items: center; justify-content: center; overflow: hidden; margin-bottom: 5px; background-color: white; padding: 2px; position: relative;">
        {new_badge_html}
        {image_html}
    </div>
    <div style="text-align: center; padding: 2px 0; height: 40px; overflow: hidden;">
        <h4 style="margin: 0; font-size: 9pt; color: #000; line-height: 1.2; font-weight: bold; font-family: serif;">
            <span style="color: #007bff; margin-right: 4px;">{ref_no}.</span>{item_name}
        </h4>
    </div>
</div>
"""

def generate_story_html(story_img_1_b64):
    text_block_1 = """HEM Corporation is amongst top global leaders in the manufacturing and export of perfumed agarbattis. For over three decades now we have been parceling out high-quality masala sticks, agarbattis, dhoops, and cones to our customers in more than 70 countries. We are known and established for our superior quality products.<br><br>HEM has been showered with love and accolades all across the globe for its diverse range of products. This makes us the most preferred brand the world over. HEM has been awarded as the ‘Top Exporters’ brand, for incense sticks by the ‘Export Promotion Council for Handicraft’ (EPCH) for three consecutive years from 2008 till 2011.<br><br>We have also been awarded “Niryat Shree” (Export) Silver Trophy in the Handicraft category by ‘Federation of Indian Export Organization’ (FIEO). The award was presented to us by the then Honourable President of India, late Shri Pranab Mukherjee."""
    text_journey_1 = """From a brand that was founded by three brothers in 1983, HEM Fragrances has come a long way. HEM started as a simple incense store offering products like masala agarbatti, thuribles, incense burner and dhoops. However, with time, there was a huge evolution in the world of fragrances much that the customers' needs also started changing. HEM incense can be experienced not only to provide you with rich aromatic experience but also create a perfect ambience for your daily prayers, meditation, and yoga.<br><br>The concept of aromatherapy massage, burning incense sticks and incense herbs for spiritual practices, using aromatherapy diffuser oils to promote healing and relaxation or using palo santo incense to purify and cleanse a space became popular around the world.<br><br>So, while we remained focused on creating our signature line of products, especially the ‘HEM Precious’ range which is a premium flagship collection, there was a dire need to expand our portfolio to meet increasing customer demands."""
    
    img_tag = ""
    if story_img_1_b64:
        img_tag = f'<img src="data:image/jpeg;base64,{story_img_1_b64}" style="max-width: 100%; height: auto; border: 1px solid #eee;" alt="Awards Image">'
    else:
        img_tag = '<div style="border: 2px dashed red; padding: 20px; color: red;">JOURNEY IMAGE NOT FOUND. Please ensure "image-journey.png" exists in the folder.</div>'

    # <--- FIXED: Height reduced to 260mm to allow space for padding within A4 (297mm) limits --->
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

# --- RESTORED TOC LOGIC FROM OLD CODE ---
def generate_table_of_contents_html(df_sorted):
    # --- 1. PREPARE DATA ---
    categories_data = []
    seen_categories = set()
    unique_categories = []
    
    for cat in df_sorted['Category'].unique():
        if cat not in seen_categories:
            unique_categories.append(cat)
            seen_categories.add(cat)

    for category in unique_categories:
        group = df_sorted[df_sorted['Category'] == category]
        rep_image = "" 
        for _, row in group.iterrows():
            img_str = row.get('ImageB64', '')
            if img_str and len(str(img_str)) > 100: 
                rep_image = img_str
                break 
        
        categories_data.append({
            "name": category,
            "image": rep_image,
            "safe_id": create_safe_id(category)
        })

    # --- 2. CSS STYLING ---
    toc_html = """
    <style>
        .toc-title {
            text-align: center;
            font-family: serif;
            font-size: 32pt;
            color: #222;
            margin-bottom: 30px;
            margin-top: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .index-grid-container {
            width: 100%;
            margin: 0 auto;
        }

        .index-card {
            display: block;
            float: left;
            width: 30%;         
            margin: 1.5%;       
            height: 200px;      
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.15);
            text-decoration: none;
            overflow: hidden;
            border: 1px solid #e0e0e0;
            page-break-inside: avoid; /* Prevents card from splitting */
        }

        .index-card-image {
            width: 100%;
            height: 160px; 
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover; 
            background-color: #f9f9f9;
        }

        .index-card-label {
            height: 40px;
            background-color: #b30000; 
            color: white;
            font-family: sans-serif;
            font-size: 10pt;
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

        .clearfix::after {
            content: "";
            clear: both;
            display: table;
        }
    </style>

    <div id="main-index" class="toc-page" style="page-break-after: always; padding: 20px;">
        <h1 class="toc-title">Our Products</h1>
        <div class="index-grid-container clearfix">
    """

    # --- 3. GENERATE CARDS ---
    for cat in categories_data:
        bg_style = ""
        if cat['image']:
            bg_style = f"background-image: url('data:image/png;base64,{cat['image']}');"
        else:
            bg_style = "background-color: #eee;" 

        card_html = f"""
            <a href="#category-{cat['safe_id']}" class="index-card">
                <div class="index-card-image" style="{bg_style}">
                    </div>
                <div class="index-card-label">
                    {cat['name']}
                </div>
            </a>
        """
        toc_html += card_html

    toc_html += """
        </div>
        <div style="clear: both;"></div>
    </div>
    """
    return toc_html

def generate_pdf_html(df_sorted, customer_name, logo_b64, case_selection_map):
    # --- 1. DEFINE PATHS ---
    USER_SPECIFIED_PATH = r"C:\Users\maa00\OneDrive\Desktop\hem-catalogue-app_final-1\hem-catalogue-app-1\assets\watermark.png"
    
    # --- 2. ROBUST IMAGE LOADING ---
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
            
            if found_path:
                return get_image_as_base64_str(found_path, resize=resize, max_size=max_size)
            return "" 

    # Load images
   # --- UPDATED: Load static assets from Cloudinary ---
    
    # 1. COVER PAGE
    cover_url = "https://res.cloudinary.com/dddtoqebz/image/upload/v1768288172/Cover_Page.jpg"
    cover_bg_b64 = get_image_as_base64_str(cover_url)
    # Fallback: Use local file if cloud fails
    if not cover_bg_b64:
        cover_bg_b64 = load_img_robust("cover page.png", resize=False)

    # 2. JOURNEY PAGE
    # 🔴 ACTION REQUIRED: Paste your Journey Image URL inside the quotes below if you have one.
    # If you don't have a URL yet, leave it empty "" and the fallback below will pick the local file.
    journey_url = "https://res.cloudinary.com/dddtoqebz/image/upload/v1768288173/image-journey.jpg" 
    
    story_img_1_b64 = get_image_as_base64_str(journey_url, max_size=(600,600))
    # Fallback: This will run if journey_url is empty OR if the download fails
    if not story_img_1_b64:
        story_img_1_b64 = load_img_robust("image-journey.png", specific_full_path=STORY_IMG_1_PATH, resize=True, max_size=(600,600))

    # 3. WATERMARK
    watermark_b64 = load_img_robust("watermark.png", specific_full_path=USER_SPECIFIED_PATH, resize=False)

    # --- 3. CSS STYLING ---
    # <--- FIXED: Added box-sizing: border-box globally to prevent padding overflow issues --->
    CSS_STYLES = f"""
# --- 3. CSS STYLING (CLOUD COMPATIBLE) ---
    CSS_STYLES = f"""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8">
        <style>
        /* 1. RESET EVERYTHING TO ZERO */
        @page {{ size: A4; margin: 0mm; }}
        html, body {{ 
            width: 210mm;
            height: 297mm;
            margin: 0 !important; 
            padding: 0 !important; 
            background-color: #ffffff;
            -webkit-print-color-adjust: exact; 
        }}
        
        /* 2. ABSOLUTE FULL PAGE WRAPPER */
        /* This forces the element to ignore page margins and snap to physical edges */
        .full-page-wrapper {{
            position: relative;
            width: 210mm;
            height: 297mm;
            overflow: hidden;
            page-break-after: always;
            margin: 0;
            padding: 0;
            left: 0;
            top: 0;
        }}
        
        /* 3. IMAGE STRETCHING */
        .full-page-img {{
            width: 100%;
            height: 100%;
            object-fit: fill; /* Forces image to stretch to cover specific gaps */
            display: block;
        }}

        /* CATALOGUE CONTENT STYLES */
        /* CATALOGUE CONTENT STYLES */
        .catalogue-content { padding: 10mm; display: block; position: relative; z-index: 10; }
        .catalogue-heading {{ background-color: #333; color: white; font-size: 18pt; padding: 8px 15px; margin-bottom: 5px; font-weight: bold; font-family: sans-serif; text-align: center; page-break-inside: avoid; }} 
        .category-heading {{ color: #333; font-size: 14pt; padding: 8px 0 4px 0; border-bottom: 2px solid #E5C384; margin-top: 5mm; clear: both; font-family: serif; page-break-inside: avoid; }} 
        .case-size-info {{ color: #555; font-size: 10pt; font-style: italic; margin-bottom: 5px; clear: both; font-family: sans-serif; }}
        .case-size-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 9pt; margin-bottom: 10px; clear: both; background-color: rgba(255,255,255,0.9); }}
        .case-size-table th {{ border: 1px solid #ddd; background-color: #f2f2f2; padding: 4px; text-align: center; font-weight: bold; font-size: 8pt; color: #333; }}
        .case-size-table td {{ border: 1px solid #ddd; padding: 4px; text-align: center; color: #444; }}
        .clearfix::after {{ content: ""; clear: both; display: table; }}
        .category-wrapper {{ display: block; clear: both; page-break-before: always; }}
        .no-break {{ page-break-before: avoid !important; }}
        </style></head><body style='margin: 0; padding: 0;'>
    """
    
    html_parts = []
    html_parts.append(CSS_STYLES)
    
    # 1. COVER PAGE
    html_parts.append(f"""
    <div class="full-page-wrapper">
        <img class="full-page-img" src="data:image/png;base64,{cover_bg_b64}">
    </div>
    """)
    
    # 2. STORY PAGE
    if story_img_1_b64:
        html_parts.append(f"""
        <div class="full-page-wrapper">
            <img class="full-page-img" src="data:image/png;base64,{story_img_1_b64}">
        </div>
        """)

        .toc-page {{ 
            width: 210mm; 
            min-height: 200mm; 
            display: block; position: relative; margin: 0; 
            background-color: transparent; 
            page-break-after: always;
        }}

        /* CATALOGUE CONTENT STYLES */
        .catalogue-content { 
            padding: 10mm; 
            display: block; 
            position: relative; 
            z-index: 9999; /* Force it to be on top of everything */
            background-color: transparent; 
        }
        
        .catalogue-heading {{ background-color: #333; color: white; font-size: 18pt; padding: 8px 15px; margin-bottom: 5px; font-weight: bold; font-family: sans-serif; text-align: center; page-break-inside: avoid; }} 
        .category-heading {{ color: #333; font-size: 14pt; padding: 8px 0 4px 0; border-bottom: 2px solid #E5C384; margin-top: 5mm; clear: both; font-family: serif; page-break-inside: avoid; }} 
        
        .case-size-info {{ color: #555; font-size: 10pt; font-style: italic; margin-bottom: 5px; clear: both; font-family: sans-serif; }}
        .case-size-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 9pt; margin-bottom: 10px; clear: both; background-color: rgba(255,255,255,0.9); }}
        .case-size-table th {{ border: 1px solid #ddd; background-color: #f2f2f2; padding: 4px; text-align: center; font-weight: bold; font-size: 8pt; color: #333; }}
        .case-size-table td {{ border: 1px solid #ddd; padding: 4px; text-align: center; color: #444; }}
        
        .cover-image-container {{ position: absolute; top: 0; left: 0; height: 100%; width: 100%; z-index: 1; }}
        .cover-image-container img {{ width: 100%; height: 100%; object-fit: cover; }}
        .clearfix::after {{ content: ""; clear: both; display: table; }}
        .category-wrapper {{ display: block; clear: both; page-break-before: always; }}
        .no-break {{ page-break-before: avoid !important; }}
        </style></head><body style='margin: 0; padding: 0;'>
        
        <div id="watermark-layer"></div>
    """
    
    html_parts = []
    html_parts.append(CSS_STYLES)
    
    # 1. Cover
    html_parts.append(f"""<div class="cover-page"><div class="cover-image-container"><img src="data:image/png;base64,{cover_bg_b64}"></div></div>""")
    
    # 2. Journey
    html_parts.append(generate_story_html(story_img_1_b64))
    
    # 3. Index
    html_parts.append(generate_table_of_contents_html(df_sorted))
    
    # 4. Products
    html_parts.append('<div class="catalogue-content clearfix">')

    def get_val_fuzzy(row_data, keys_list):
        for k in keys_list:
            for data_k in row_data.keys():
                if k.lower() in data_k.lower(): return str(row_data[data_k])
        return "-"

    current_catalogue = None; current_category = None; is_first_item = True; just_started_catalogue = False 

    for index, row in df_sorted.iterrows():
        if row['Catalogue'] != current_catalogue:
            current_catalogue = row['Catalogue']; current_category = None
            break_style = 'style="page-break-before: always;"' if not is_first_item else ""
            html_parts.append(f'<div style="clear:both;"></div><h1 class="catalogue-heading" {break_style}>{current_catalogue}</h1>')
            is_first_item = False; just_started_catalogue = True 

        if row['Category'] != current_category:
            current_category = row['Category']
            safe_category_id = create_safe_id(current_category)
            wrapper_class = "no-break" if just_started_catalogue else "category-wrapper"
            just_started_catalogue = False 
            
            html_parts.append(f'<div class="{wrapper_class}">') 
            html_parts.append(f'''
            <h2 class="category-heading" id="category-{safe_category_id}">
                <a href="#main-index" style="float: right; font-size: 10px; color: #555; text-decoration: none; font-weight: normal; font-family: sans-serif; margin-top: 4px;">BACK TO INDEX &uarr;</a>
                {current_category}
            </h2>
            ''')
            
            if current_category in case_selection_map:
                row_data = case_selection_map[current_category]
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
            html_parts.append('</div>')

        img_b64 = row["ImageB64"] 
        mime_type = 'image/png' if (img_b64 and len(img_b64) > 20 and img_b64[:20].lower().find('i') != -1) else 'image/jpeg'
        image_html_content = f'<img src="data:{mime_type};base64,{img_b64}" style="max-height: 100%; max-width: 100%;" alt="{row.get("ItemName", "")}">' if img_b64 else '<div class="image-placeholder" style="color:#ccc; font-size:10px;">IMAGE NOT FOUND</div>'
        
        packaging_text = row.get('Packaging', '').replace('Default Packaging', '')
        sku_info = f"SKU: {row.get('SKU Code', 'N/A')}"
        fragrance_list = [f.strip() for f in row.get('Fragrance', '').split(',') if f.strip() and f.strip().upper() != 'N/A']
        fragrance_output = f"Fragrance: {', '.join(fragrance_list)}" if fragrance_list else "No fragrance info listed"
        
        new_badge_html = ""
        if row.get('IsNew') == 1:
            new_badge_html = """<div style="position: absolute; top: 0; right: 0; background-color: #dc3545; color: white; font-size: 8px; font-weight: bold; padding: 2px 8px; border-radius: 0 0 0 5px; z-index: 10;">NEW</div>"""

        if PRODUCT_CARD_TEMPLATE:
            card_output = PRODUCT_CARD_TEMPLATE.format(
                new_badge_html=new_badge_html,
                image_html=image_html_content, 
                item_name=row.get('ItemName', 'N/A'), 
                category_name=row['Category'],
                ref_no=index+1,
                packaging=packaging_text, 
                sku_info=sku_info, 
                fragrance=fragrance_output
            )
            html_parts.append(card_output)
    
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
                    try: 
                        cbm = round(float(case_data[k]), 3)
                    except: cbm = 0.0
            if suffix == 'nan': suffix = ""
        
        full_name = str(row['ItemName']).strip()
        if suffix: full_name = f"{full_name} {suffix}"
            
        excel_rows.append({
            "Ref No": idx + 1,
            "Category": cat,
            "Product Name + Carton Name": full_name,
            "Carton per CBM": cbm,
            "Order Quantity (Cartons)": 0, 
            "Total CBM": 0 
        })
        
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
        
        # --- HEADS UP DISPLAY ---
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
            worksheet.write(row_idx-1, 4, 0, input_fmt) 
            worksheet.write_formula(row_idx-1, 5, f'=D{row_idx}*E{row_idx}', locked_fmt)

    return output.getvalue()

# --- MAIN APP ---
if True: 
    if "cart" not in st.session_state: st.session_state.cart = []
    if "gen_pdf_bytes" not in st.session_state: st.session_state.gen_pdf_bytes = None
    if "gen_excel_bytes" not in st.session_state: st.session_state.gen_excel_bytes = None
    if 'selected_catalogue_dropdown' not in st.session_state: st.session_state.selected_catalogue_dropdown = NO_SELECTION_PLACEHOLDER
    if 'selected_categories_multi' not in st.session_state: st.session_state.selected_categories_multi = []
    if 'selected_subcategories_multi' not in st.session_state: st.session_state.selected_subcategories_multi = []
    if 'item_search_query' not in st.session_state: st.session_state.item_search_query = ""
    if 'category_multiselect_prev' not in st.session_state: st.session_state['category_multiselect_prev'] = []
    if 'master_pid_map' not in st.session_state: st.session_state['master_pid_map'] = {}

    products_df = load_data()
    
    with st.sidebar:
        st.header("📂 Manage Templates")
        with st.expander("Save Current Cart"):
            new_template_name = st.text_input("Template Name")
            if st.button("Save Template"):
                if new_template_name: save_template_to_disk(new_template_name, st.session_state.cart)
        saved_templates = load_saved_templates()
        if saved_templates:
            with st.expander("Load Template"):
                sel_temp = st.selectbox("Select Template", list(saved_templates.keys()))
                if st.button("Load"):
                    st.session_state.cart = saved_templates[sel_temp]
                    st.toast(f"Template '{sel_temp}' loaded!", icon="✅")
                    st.rerun()
        
        st.markdown("---")

    st.title("HEM PRODUCT CATALOGUE")
    tab1, tab2, tab3 = st.tabs(["1. Filter", "2. Review", "3. Export"])
    
    with tab1:
        if products_df.empty: st.error("No Data. Please check Excel file paths.")
        else:
            final_df = products_df.copy()
            
            def update_search(): st.session_state.item_search_query = st.session_state["item_search_input"]
            search_term = st.text_input("🔍 Global Search (Products, Fragrance, SKU)", value=st.session_state.item_search_query, key="item_search_input", on_change=update_search).lower()
            
            if search_term:
                final_df = products_df[
                    products_df['ItemName'].str.lower().str.contains(search_term, na=False) |
                    products_df['Fragrance'].str.lower().str.contains(search_term, na=False) |
                    products_df['SKU Code'].str.lower().str.contains(search_term, na=False)
                ]
                st.info(f"Found {len(final_df)} items matching '{search_term}'")
                display_product_list(final_df, is_global_search=True)
            else:
                col_filter, col_btns = st.columns([3, 1])
                with col_filter:
                    st.markdown("#### Filters")
                    catalogue_options = [NO_SELECTION_PLACEHOLDER] + sorted(products_df['Catalogue'].unique())
                    try: default_index_cat = catalogue_options.index(st.session_state.selected_catalogue_dropdown)
                    except ValueError: default_index_cat = 0 
                    sel_cat = st.selectbox("Catalogue", catalogue_options, key="selected_catalogue_dropdown", index=default_index_cat) 
                    
                    if sel_cat != NO_SELECTION_PLACEHOLDER: 
                        catalog_subset_df = products_df[products_df['Catalogue'] == sel_cat]
                        category_options = sorted(catalog_subset_df['Category'].unique())
                        
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
                                raw_subs = sorted(cat_data['Subcategory'].unique())
                                clean_subs = [s for s in raw_subs if s.strip().upper() != 'N/A' and s.strip().lower() != 'nan' and s.strip() != '']
                                
                                if clean_subs:
                                    safe_cat_key = create_safe_id(category)
                                    sel_subs = st.multiselect(
                                        f"Select for **{category}**", 
                                        clean_subs, 
                                        default=clean_subs, 
                                        key=f"sub_select_{safe_cat_key}"
                                    )
                                    cat_data_filtered = cat_data[
                                        cat_data['Subcategory'].isin(sel_subs) | 
                                        cat_data['Subcategory'].isin(['N/A', 'nan', '']) |
                                        cat_data['Subcategory'].isna()
                                    ]
                                    filtered_dfs.append(cat_data_filtered)
                                else:
                                    filtered_dfs.append(cat_data)
                            
                            if filtered_dfs: final_df = pd.concat(filtered_dfs)
                            else: final_df = pd.DataFrame(columns=products_df.columns)
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
                    if not final_df.empty: display_product_list(final_df)
                    else: st.info("👆 Please select one or more **Categories**.")
                else: st.info("👈 Please select a **Catalogue** to begin.")

    with tab2:
        st.markdown('## Review Cart Items')
        if st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_search = st.text_input("Find in Cart...", placeholder="Type name...").lower()
            if cart_search: cart_df = cart_df[cart_df['ItemName'].str.lower().str.contains(cart_search)]
            
            cart_df['Remove'] = False
            editable_df_view = cart_df[['Catalogue', 'Category', 'ItemName', 'Remove']]
            
            edited_df = st.data_editor(
                editable_df_view, 
                column_config={
                    "Remove": st.column_config.CheckboxColumn("Remove?", default=False, width="small"),
                    "Catalogue": st.column_config.TextColumn("Catalogue Source", width="medium"),
                    "Category": st.column_config.TextColumn("Category", width="medium"), 
                    "ItemName": st.column_config.TextColumn("Product Name", width="large")
                }, 
                hide_index=True, 
                key="cart_data_editor_fixed",
                use_container_width=True
            )
            
            indices_to_remove = edited_df[edited_df['Remove'] == True].index.tolist()
            if indices_to_remove: pids_to_remove = cart_df.loc[indices_to_remove, 'ProductID'].tolist()
            else: pids_to_remove = []
            
            c_remove, c_clear = st.columns([1, 1])
            with c_remove:
                if st.button(f"Remove {len(pids_to_remove)} Selected Items", disabled=not pids_to_remove): 
                    remove_from_cart(pids_to_remove)
                    st.rerun()
            with c_clear:
                if st.button("Clear Cart"): 
                    st.session_state.cart = [] 
                    st.session_state.gen_pdf_bytes = None
                    st.session_state.gen_excel_bytes = None
                    st.rerun()
        else: st.info("Cart Empty")

    with tab3:
        st.markdown('## Export Catalogue')
        if not st.session_state.cart: st.info("Cart is empty.")
        else:
            st.markdown("### 1. Select Case Sizes per Category")
            cart_categories = sorted(list(set([item['Category'] for item in st.session_state.cart])))
            full_case_size_df = pd.DataFrame()
            if os.path.exists(CASE_SIZE_PATH):
                try:
                    full_case_size_df = pd.read_excel(CASE_SIZE_PATH, dtype=str)
                    full_case_size_df.columns = [c.strip() for c in full_case_size_df.columns]
                except: st.error("Error loading Case Size.xlsx")

            selection_map = {}
            if not full_case_size_df.empty:
                suffix_col = next((c for c in full_case_size_df.columns if "suffix" in c.lower()), None)
                cbm_col = next((c for c in full_case_size_df.columns if "cbm" in c.lower()), "CBM")
                
                if not suffix_col: st.error(f"Could not find 'Carton Suffix' column. Found: {full_case_size_df.columns.tolist()}")
                else:
                    for cat in cart_categories:
                        options = full_case_size_df[full_case_size_df['Category'] == cat]
                        if not options.empty:
                            options['DisplayLabel'] = options.apply(lambda x: f"{x[suffix_col]} (CBM: {x[cbm_col]})", axis=1)
                            label_list = options['DisplayLabel'].tolist()
                            selected_label = st.selectbox(f"Select Case Size for **{cat}**", label_list, key=f"select_case_{cat}")
                            selected_row = options[options['DisplayLabel'] == selected_label].iloc[0]
                            selection_map[cat] = selected_row.to_dict()
                        else: st.warning(f"No Case Size options found for category: {cat}")
            
            st.markdown("---")
            name = st.text_input("Client Name", "Valued Client")
            if st.button("Generate Catalogue & Order Sheet"):
                cart_data = st.session_state.cart
                schema_cols = ['Catalogue', 'Category', 'Subcategory', 'ItemName', 'Fragrance', 'SKU Code', 'ImageB64', 'Packaging', 'IsNew']
                df_final = pd.DataFrame(cart_data)
                for col in schema_cols: 
                    if col not in df_final.columns: df_final[col] = ''
                df_final = df_final[schema_cols].sort_values(['Catalogue', 'Category', 'Subcategory'])
                df_final['SerialNo'] = range(1, len(df_final)+1)
                
                st.toast("Generating files...", icon="⏳")
                st.session_state.gen_excel_bytes = generate_excel_file(df_final, name, selection_map)
                
                if CONFIG:
                    try:
                        logo = get_image_as_base64_str(LOGO_PATH, resize=True, max_size=(200,100)) 
                        html = generate_pdf_html(df_final, name, logo, selection_map)
                        
                        options = {
                            # --- PDF SETTINGS (CLOUD OPTIMIZED) ---
  
                            'page-size': 'A4',
                            'margin-top': '0mm',
                            'margin-right': '0mm',
                            'margin-bottom': '0mm',
                            'margin-left': '0mm',
                            'encoding': "UTF-8",
                            'no-outline': None,
                            'enable-local-file-access': None,
                            'disable-smart-shrinking': None,  # <--- STOP THE SERVER FROM SHRINKING PAGES
                            'dpi': 96,                        # <--- FORCE STANDARD RESOLUTION
                            'zoom': 1.0,                      # <--- PREVENT UNWANTED SCALING
                            'print-media-type': None          # <--- ENSURE CSS IS READ CORRECTLY
    
   
                        }
                        
                        st.session_state.gen_pdf_bytes = pdfkit.from_string(html, False, configuration=CONFIG, options=options)
                        st.toast("PDF and Excel generated!", icon="🎉")
                    except Exception as e: 
                        st.error(f"Error generating PDF: {e}")
                        st.session_state.gen_pdf_bytes = None
                else: st.warning("wkhtmltopdf configuration missing."); st.session_state.gen_pdf_bytes = None

            c_pdf, c_excel = st.columns(2)
            with c_pdf:
                if st.session_state.gen_pdf_bytes: st.download_button("⬇️ Download PDF Catalogue", st.session_state.gen_pdf_bytes, f"{name.replace(' ', '_')}_catalogue.pdf", type="primary")
            with c_excel:
                if st.session_state.gen_excel_bytes: st.download_button("⬇️ Download Excel Order Sheet", st.session_state.gen_excel_bytes, f"{name.replace(' ', '_')}_order.xlsx", type="secondary")



