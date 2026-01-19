import streamlit as st
import pandas as pd
import json
import os
import shutil
import uuid
from fuzzywuzzy import fuzz

# --- CONFIG & PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "database.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGE_DIR = os.path.join(BASE_DIR, "images")

# Specific File Paths
CASE_SIZE_PATH = os.path.join(BASE_DIR, "Case Size.xlsx")
CATALOGUE_PATHS = {
    "HEM Product Catalogue": os.path.join(BASE_DIR, "Hem catalogue.xlsx"),
    "Sacred Elements Catalogue": os.path.join(BASE_DIR, "SacredElement.xlsx"),
    "Pooja Oil Catalogue": os.path.join(BASE_DIR, "Pooja Oil Catalogue.xlsx"),
    "Candle Catalogue": os.path.join(BASE_DIR, "Candle Catalogue.xlsx"),
}

# Ensure environment is ready
for d in [DB_DIR, ASSETS_DIR, IMAGE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# Robust Mapping for Sync
COL_MAP = {
    "Sub-Category": "Subcategory", "Sub Category": "Subcategory",
    "Item Name": "ItemName", "Description": "Fragrance",
    "SKU Code": "SKUCode", "SKU": "SKUCode",
    "New Product ( Indication )": "IsNew"
}
CASE_MAP = {
    "Carton Suffix": "Suffix", "Suffix": "Suffix",
    "CBM": "CBM", "Packing": "Packing", "Master Ctn": "Packing"
}

# --- HELPER FUNCTIONS ---
def clean_key(text):
    if not isinstance(text, str): return ""
    text = text.lower().strip().replace(' ', '').replace('_', '').replace('-', '')
    for stop_word in ['catalogue', 'image', 'images', 'product', 'products', 'img']:
        text = text.replace(stop_word, '')
    return text

def load_db():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r') as f: return json.load(f)
        except: pass
    return {"catalogues": [], "products": [], "case_sizes": [], "defaults": {}}

def save_db(db):
    with open(DB_PATH, 'w') as f: json.dump(db, f, indent=4)

# --- UI SETUP ---
st.set_page_config(page_title="HEM ADMIN BACKEND", layout="wide")
db = load_db()

# SIDEBAR NAVIGATION
with st.sidebar:
    st.title("🛠️ SYSTEM ADMIN")
    menu = st.radio("Navigation", [
        "1. Cover Page Image",
        "2. Our Story Image",
        "3. Catalogue Management",
        "4. Products Master",
        "5. Case Size Master",
        "6. Default Case Sizes",
        "7. Product Image Linker",
        "8. New Product Tagging",
        "🔄 Initial Sync"
    ])

# --- TAB 1 & 2: IMAGES ---
if menu in ["1. Cover Page Image", "2. Our Story Image"]:
    label = "Cover Page" if "1" in menu else "Our Story"
    fname = "cover page.png" if "1" in menu else "2.1 page of pdf.jpg"
    st.header(f"Manage {label}")
    path = os.path.join(ASSETS_DIR, fname)
    if os.path.exists(path):
        st.image(path, width=300)
        if st.button(f"Remove Current {label}"): os.remove(path); st.rerun()
    else:
        st.warning(f"No {label} found. Upload one to set it.")
    
    up = st.file_uploader(f"Upload/Replace {label}", type=['png', 'jpg', 'jpeg'])
    if up: 
        with open(path, "wb") as f: f.write(up.getbuffer())
        st.success("Uploaded Successfully!"); st.rerun()

# --- TAB 3: CATALOGUES ---
elif menu == "3. Catalogue Management":
    st.header("Catalogue Creation")
    st.info("Define which catalogues are active.")
    df_cat = pd.DataFrame(db["catalogues"]) if db["catalogues"] else pd.DataFrame(columns=["Name", "Status"])
    ed_cat = st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)
    if st.button("Save Catalogues"):
        db["catalogues"] = ed_cat.to_dict(orient="records")
        save_db(db); st.success("Saved!")

# --- TAB 4: PRODUCTS MASTER (UPDATED SEARCH) ---
elif menu == "4. Products Master":
    st.header("Products Master List")
    if not db["products"]: st.warning("Database empty. Please run 'Initial Sync'.")
    else:
        df_p = pd.DataFrame(db["products"])
        
        # 1. TEXT SEARCH (NEW)
        search_query = st.text_input("🔍 Global Search (SKU or Item Name)", placeholder="Type to find product...")
        
        # 2. DROPDOWN FILTERS
        c1, c2, c3 = st.columns(3)
        cat_opts = ["All"] + sorted(list(df_p['Catalogue'].unique()))
        sel_cat = c1.selectbox("Filter Catalogue", cat_opts)
        
        filtered_df = df_p
        
        # Apply Text Search
        if search_query:
            filtered_df = filtered_df[
                filtered_df['ItemName'].str.contains(search_query, case=False, na=False) |
                filtered_df['SKUCode'].str.contains(search_query, case=False, na=False)
            ]

        # Apply Dropdown Filters
        if sel_cat != "All":
            filtered_df = filtered_df[filtered_df['Catalogue'] == sel_cat]
            categ_opts = ["All"] + sorted(list(filtered_df['Category'].unique()))
            sel_categ = c2.selectbox("Filter Category", categ_opts)
            
            if sel_categ != "All":
                filtered_df = filtered_df[filtered_df['Category'] == sel_categ]
                sub_opts = ["All"] + sorted(list(filtered_df['Subcategory'].unique()))
                sel_sub = c3.selectbox("Filter Subcategory", sub_opts)
                if sel_sub != "All":
                    filtered_df = filtered_df[filtered_df['Subcategory'] == sel_sub]
        else:
            c2.selectbox("Filter Category", ["-"], disabled=True)
            c3.selectbox("Filter Subcategory", ["-"], disabled=True)

        st.markdown(f"**Showing {len(filtered_df)} products**")
        ed_p = st.data_editor(filtered_df, num_rows="dynamic", use_container_width=True, key="prod_editor")
        
        if st.button("Save Changes to Master"):
            if sel_cat == "All" and not search_query:
                db["products"] = ed_p.to_dict(orient="records")
                save_db(db); st.success("Master Database Updated!")
            else:
                st.warning("You are editing a filtered view. To save changes reliably to the whole database, please clear filters.")

# --- TAB 5: CASE SIZE MASTER ---
elif menu == "5. Case Size Master":
    st.header("Case Sizes Configuration")
    if not db["case_sizes"]: st.warning("No case sizes loaded.")
    else:
        df_cs = pd.DataFrame(db["case_sizes"])
        ed_cs = st.data_editor(df_cs, num_rows="dynamic", use_container_width=True)
        if st.button("Save Case Sizes"):
            db["case_sizes"] = ed_cs.to_dict(orient="records")
            save_db(db); st.success("Saved!")

# --- TAB 6: DEFAULT CASE SIZES ---
elif menu == "6. Default Case Sizes":
    st.header("Set Default Case Sizes")
    if not db["products"] or not db["case_sizes"]:
        st.error("Missing data. Run Sync first.")
    else:
        all_categories = sorted(list(set(p['Category'] for p in db["products"] if p['Category'] != "Uncategorized")))
        cs_df = pd.DataFrame(db["case_sizes"])
        if "defaults" not in db: db["defaults"] = {}
        
        updated_defaults = {}
        cols = st.columns([2, 3])
        cols[0].markdown("**Category**"); cols[1].markdown("**Default Case Size**")
        st.divider()
        
        for cat in all_categories:
            relevant_cs = cs_df[cs_df['Category'] == cat]
            if relevant_cs.empty:
                opts = ["NO OPTIONS AVAILABLE"]
                curr = "NO OPTIONS AVAILABLE"
            else:
                opts = relevant_cs.apply(lambda x: f"{x.get('Suffix','')} (CBM:{x.get('CBM','')})", axis=1).tolist()
                opts = ["None"] + opts
                saved = db["defaults"].get(cat, "None")
                curr = saved if saved in opts else "None"
            
            c1, c2 = st.columns([2, 3])
            c1.write(cat)
            sel = c2.selectbox(f"Sel {cat}", opts, index=opts.index(curr), label_visibility="collapsed")
            updated_defaults[cat] = sel
            
        if st.button("Save Defaults"):
            db["defaults"] = updated_defaults
            save_db(db); st.success("Saved!")

# --- TAB 7: IMAGES ---
elif menu == "7. Product Image Linker":
    st.header("Visual Product Image Mapper")
    if not db["products"]: st.warning("Database empty. Run Initial Sync.")
    else:
        df_p = pd.DataFrame(db["products"])
        
        c1, c2, c3 = st.columns(3)
        cat_opts = ["All"] + sorted(list(df_p['Catalogue'].unique()))
        sel_cat = c1.selectbox("1. Catalogue", cat_opts)
        
        filtered_df = df_p
        if sel_cat != "All":
            filtered_df = filtered_df[filtered_df['Catalogue'] == sel_cat]
            categ_opts = ["All"] + sorted(list(filtered_df['Category'].unique()))
            sel_categ = c2.selectbox("2. Category", categ_opts)
            if sel_categ != "All":
                filtered_df = filtered_df[filtered_df['Category'] == sel_categ]
                sub_opts = ["All"] + sorted(list(filtered_df['Subcategory'].unique()))
                sel_sub = c3.selectbox("3. Subcategory", sub_opts)
                if sel_sub != "All": filtered_df = filtered_df[filtered_df['Subcategory'] == sel_sub]
        else:
            c2.selectbox("2. Category", ["-"], disabled=True)
            c3.selectbox("3. Subcategory", ["-"], disabled=True)
            
        st.divider()
        filtered_df['DisplayLabel'] = filtered_df['ItemName'] + " (" + filtered_df['SKUCode'] + ")"
        product_opts = filtered_df['DisplayLabel'].tolist()
        selected_label = st.selectbox("Select Product to Edit", ["Select..."] + product_opts)
        
        if selected_label != "Select...":
            selected_row = filtered_df[filtered_df['DisplayLabel'] == selected_label].iloc[0]
            sku = selected_row['SKUCode']
            col_preview, col_upload = st.columns(2)
            curr_path = os.path.join(IMAGE_DIR, f"{sku}.jpg")
            
            with col_preview:
                st.markdown("**Current Image:**")
                if os.path.exists(curr_path): st.image(curr_path, width=300)
                else: st.info("No image linked.")

            with col_upload:
                st.markdown("**Replace Image:**")
                up_img = st.file_uploader("Upload New (JPG/PNG)", type=['jpg', 'png', 'jpeg'])
                if up_img:
                    if st.button("Confirm Replace", type="primary"):
                        with open(curr_path, "wb") as f: f.write(up_img.getbuffer())
                        st.success("Updated!"); st.rerun()

# --- TAB 8: TAGGING ---
elif menu == "8. New Product Tagging":
    st.header("New Product Tags")
    if not db["products"]: st.warning("Run Sync first.")
    else:
        df_tag = pd.DataFrame(db["products"])
        if 'SKUCode' not in df_tag.columns: df_tag['SKUCode'] = "MISSING"
            
        c1, c2 = st.columns(2)
        f_cat = c1.selectbox("Filter Catalogue", ["All"] + list(df_tag['Catalogue'].unique()), key="tag_cat_filt")
        f_search = c2.text_input("Search Product Name", key="tag_search")
        
        view = df_tag
        if f_cat != "All": view = view[view['Catalogue'] == f_cat]
        if f_search: view = view[view['ItemName'].str.contains(f_search, case=False)]
        
        ed_tag = st.data_editor(
            view[['Catalogue', 'ItemName', 'SKUCode', 'IsNew']], 
            column_config={"IsNew": st.column_config.CheckboxColumn("NEW?", default=False)},
            disabled=["Catalogue", "ItemName", "SKUCode"],
            hide_index=True, use_container_width=True
        )
        if st.button("Save Tag Updates"):
            updates = dict(zip(ed_tag['SKUCode'], ed_tag['IsNew']))
            count = 0
            for p in db["products"]:
                if p.get('SKUCode') in updates:
                    if p.get('IsNew') != updates[p['SKUCode']]:
                        p['IsNew'] = updates[p['SKUCode']]; count += 1
            save_db(db); st.success(f"Updated {count} products!")

# --- TAB 9: SYNC ENGINE (UPDATED IMAGE CRAWLER) ---
elif menu == "🔄 Initial Sync":
    st.header("Sync Data & Images")
    st.markdown("This will crawl Excel files AND your `images/` folder structure to link products.")
    
    if st.button("🚀 Run Full Sync & Image Match"):
        with st.spinner("Processing Data & Crawling Images..."):
            all_p = []
            
            # 1. READ EXCEL
            for name, path in CATALOGUE_PATHS.items():
                if os.path.exists(path):
                    try:
                        tmp = pd.read_excel(path, dtype=str)
                        tmp.columns = [c.strip() for c in tmp.columns]
                        tmp = tmp.rename(columns=COL_MAP)
                        tmp['Catalogue'] = name
                        for r in ["Category", "Subcategory", "ItemName", "SKUCode", "IsNew", "Fragrance"]:
                            if r not in tmp.columns: tmp[r] = "N/A"
                        tmp['IsNew'] = pd.to_numeric(tmp['IsNew'], errors='coerce').fillna(0).astype(int)
                        # Fix Missing SKUs
                        tmp['SKUCode'] = tmp.apply(lambda row: row['SKUCode'] if row['SKUCode'] != "nan" and row['SKUCode'] != "N/A" else f"GEN_{uuid.uuid4().hex[:8]}", axis=1)
                        all_p.extend(tmp.to_dict(orient="records"))
                    except Exception as e: st.error(f"Error in {name}: {e}")
            
            # 2. CRAWL & MATCH IMAGES
            # We map "clean_filename" -> "full_path"
            found_images = {}
            for root, dirs, files in os.walk(IMAGE_DIR):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        clean_name = clean_key(os.path.splitext(file)[0])
                        found_images[clean_name] = os.path.join(root, file)
            
            match_count = 0
            for p in all_p:
                sku = p['SKUCode']
                clean_item_name = clean_key(p['ItemName'])
                
                # Check for match
                matched_path = None
                if clean_item_name in found_images:
                    matched_path = found_images[clean_item_name]
                else:
                    # Optional: Add Fuzzy Match here if exact match fails
                    pass
                
                # If matched, copy to root as SKU.jpg
                if matched_path:
                    dest_path = os.path.join(IMAGE_DIR, f"{sku}.jpg")
                    try:
                        shutil.copy2(matched_path, dest_path)
                        match_count += 1
                    except: pass

            # 3. READ CASE SIZES
            all_cs = []
            if os.path.exists(CASE_SIZE_PATH):
                try:
                    cs_df = pd.read_excel(CASE_SIZE_PATH, dtype=str)
                    cs_df.columns = [c.strip() for c in cs_df.columns]
                    cs_df = cs_df.rename(columns=CASE_MAP)
                    for r in ["Category", "Suffix", "CBM", "Packing"]:
                        if r not in cs_df.columns: cs_df[r] = ""
                    all_cs = cs_df.to_dict(orient="records")
                except: pass

            db["products"] = all_p
            db["case_sizes"] = all_cs
            db["catalogues"] = [{"Name": k, "Status": "Active"} for k in CATALOGUE_PATHS.keys()]
            save_db(db)
            st.success(f"Sync Complete! Loaded {len(all_p)} products. Matched {match_count} images.")