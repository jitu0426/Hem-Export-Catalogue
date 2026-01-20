import streamlit as st
import pandas as pd
import json
import os
import shutil
import uuid
from fuzzywuzzy import fuzz
from github import Github  # NEW LIBRARY

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="HEM ADMIN BACKEND", layout="wide")

# --- 2. PASSWORD PROTECTION ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Admin Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Admin Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# =========================================================
#      👇 SMART PATH & GITHUB SAVE SYSTEM 👇
# =========================================================

# Path Setup
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
TEST_FILE = "Hem catalogue.xlsx"

if os.path.exists(os.path.join(CURRENT_DIR, TEST_FILE)):
    BASE_DIR = CURRENT_DIR 
elif os.path.exists(os.path.join(PROJECT_ROOT, TEST_FILE)):
    BASE_DIR = PROJECT_ROOT 
else:
    BASE_DIR = PROJECT_ROOT

DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "database.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGE_DIR = os.path.join(BASE_DIR, "images")

# Ensure environment
for d in [DB_DIR, ASSETS_DIR, IMAGE_DIR]:
    if not os.path.exists(d): os.makedirs(d)

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

# --- NEW: PERMANENT GITHUB SAVE FUNCTION ---
def save_db(db_content):
    # 1. Save Locally (For immediate use)
    with open(DB_PATH, 'w') as f: json.dump(db_content, f, indent=4)
    
    # 2. Save to GitHub (For persistence)
    try:
        # Get token from secrets
        token = st.secrets["github_token"]
        g = Github(token)
        
        # --- IMPORTANT: CHANGE THIS TO YOUR GITHUB USERNAME/REPO ---
        # Format: "username/repo_name" (e.g., "jitu0426/Hem-Export-Catalogue")
        repo_name = "jitu0426/Hem-Export-Catalogue" 
        
        repo = g.get_repo(repo_name)
        file_path = "data/database.json"
        
        try:
            # Get the file to update it (we need its 'sha' ID)
            contents = repo.get_contents(file_path)
            repo.update_file(file_path, "Update DB from Admin Panel", json.dumps(db_content, indent=4), contents.sha)
            st.toast("✅ Saved permanently to GitHub!", icon="☁️")
        except:
            # If file doesn't exist yet on GitHub, create it
            repo.create_file(file_path, "Create DB from Admin Panel", json.dumps(db_content, indent=4))
            st.toast("✅ Created database on GitHub!", icon="nw")
            
    except Exception as e:
        st.error(f"⚠️ Saved locally, but failed to save to GitHub: {e}")
        st.info("Check your 'github_token' in Streamlit Secrets and your Repo Name in the code.")

# --- FILE PATHS FOR EXCEL ---
CASE_SIZE_PATH = os.path.join(BASE_DIR, "Case Size.xlsx")
CATALOGUE_PATHS = {
    "HEM Product Catalogue": os.path.join(BASE_DIR, "Hem catalogue.xlsx"),
    "Sacred Elements Catalogue": os.path.join(BASE_DIR, "SacredElement.xlsx"),
    "Pooja Oil Catalogue": os.path.join(BASE_DIR, "Pooja Oil Catalogue.xlsx"),
    "Candle Catalogue": os.path.join(BASE_DIR, "Candle Catalogue.xlsx"),
}
COL_MAP = { "Sub-Category": "Subcategory", "Sub Category": "Subcategory", "Item Name": "ItemName", "Description": "Fragrance", "SKU Code": "SKUCode", "SKU": "SKUCode", "New Product ( Indication )": "IsNew" }
CASE_MAP = { "Carton Suffix": "Suffix", "Suffix": "Suffix", "CBM": "CBM", "Packing": "Packing", "Master Ctn": "Packing" }

# --- UI SETUP ---
db = load_db()

with st.sidebar:
    st.title("🛠️ SYSTEM ADMIN")
    menu = st.radio("Navigation", [
        "1. Cover Page Image", "2. Our Story Image", "3. Catalogue Management",
        "4. Products Master", "5. Case Size Master", "6. Default Case Sizes",
        "7. Product Image Linker", "8. New Product Tagging", "🔄 Initial Sync"
    ])
    st.divider()
    if st.button("Logout"):
        del st.session_state["password_correct"]
        st.rerun()

# --- TABS LOGIC ---
if menu in ["1. Cover Page Image", "2. Our Story Image"]:
    st.info("⚠️ Image uploads are temporary on Cloud. Use Cloudinary for permanent images.")

elif menu == "3. Catalogue Management":
    st.header("Catalogue Creation")
    df_cat = pd.DataFrame(db["catalogues"]) if db["catalogues"] else pd.DataFrame(columns=["Name", "Status"])
    ed_cat = st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)
    if st.button("Save Catalogues"):
        db["catalogues"] = ed_cat.to_dict(orient="records")
        save_db(db)

elif menu == "4. Products Master":
    st.header("Products Master List")
    if not db["products"]: st.warning("Database empty. Please run 'Initial Sync'.")
    else:
        df_p = pd.DataFrame(db["products"])
        search_query = st.text_input("🔍 Global Search (SKU or Item Name)", placeholder="Type to find product...")
        
        c1, c2, c3 = st.columns(3)
        cat_opts = ["All"] + sorted(list(df_p['Catalogue'].unique()))
        sel_cat = c1.selectbox("Filter Catalogue", cat_opts)
        
        filtered_df = df_p
        if search_query:
            filtered_df = filtered_df[filtered_df['ItemName'].str.contains(search_query, case=False, na=False) | filtered_df['SKUCode'].str.contains(search_query, case=False, na=False)]
        if sel_cat != "All":
            filtered_df = filtered_df[filtered_df['Catalogue'] == sel_cat]
            categ_opts = ["All"] + sorted(list(filtered_df['Category'].unique()))
            sel_categ = c2.selectbox("Filter Category", categ_opts)
            if sel_categ != "All":
                filtered_df = filtered_df[filtered_df['Category'] == sel_categ]
                sub_opts = ["All"] + sorted(list(filtered_df['Subcategory'].unique()))
                sel_sub = c3.selectbox("Filter Subcategory", sub_opts)
                if sel_sub != "All": filtered_df = filtered_df[filtered_df['Subcategory'] == sel_sub]
        else:
            c2.selectbox("Filter Category", ["-"], disabled=True); c3.selectbox("Filter Subcategory", ["-"], disabled=True)

        st.markdown(f"**Showing {len(filtered_df)} products**")
        ed_p = st.data_editor(filtered_df, num_rows="dynamic", use_container_width=True, key="prod_editor")
        if st.button("Save Changes to Master"):
            if sel_cat == "All" and not search_query:
                db["products"] = ed_p.to_dict(orient="records")
                save_db(db)
            else: st.warning("Clear filters before saving to master.")

elif menu == "5. Case Size Master":
    st.header("Case Sizes Configuration")
    if not db["case_sizes"]: st.warning("No case sizes loaded.")
    else:
        df_cs = pd.DataFrame(db["case_sizes"])
        ed_cs = st.data_editor(df_cs, num_rows="dynamic", use_container_width=True)
        if st.button("Save Case Sizes"):
            db["case_sizes"] = ed_cs.to_dict(orient="records")
            save_db(db)

elif menu == "6. Default Case Sizes":
    st.header("Set Default Case Sizes")
    if not db["products"] or not db["case_sizes"]: st.error("Missing data.")
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
            opts = ["NO OPTIONS AVAILABLE"] if relevant_cs.empty else ["None"] + relevant_cs.apply(lambda x: f"{x.get('Suffix','')} (CBM:{x.get('CBM','')})", axis=1).tolist()
            saved = db["defaults"].get(cat, "None")
            curr = saved if saved in opts else "None"
            c1, c2 = st.columns([2, 3])
            c1.write(cat)
            sel = c2.selectbox(f"Sel {cat}", opts, index=opts.index(curr), label_visibility="collapsed")
            updated_defaults[cat] = sel
        if st.button("Save Defaults"):
            db["defaults"] = updated_defaults
            save_db(db)

elif menu == "7. Product Image Linker":
    st.warning("⚠️ Image linking is disabled on Cloud. Use Cloudinary auto-matching (ensure image names match product names).")

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
        ed_tag = st.data_editor(view[['Catalogue', 'ItemName', 'SKUCode', 'IsNew']], column_config={"IsNew": st.column_config.CheckboxColumn("NEW?", default=False)}, disabled=["Catalogue", "ItemName", "SKUCode"], hide_index=True, use_container_width=True)
        if st.button("Save Tag Updates"):
            updates = dict(zip(ed_tag['SKUCode'], ed_tag['IsNew']))
            count = 0
            for p in db["products"]:
                if p.get('SKUCode') in updates:
                    if p.get('IsNew') != updates[p['SKUCode']]:
                        p['IsNew'] = updates[p['SKUCode']]; count += 1
            save_db(db)
            st.success(f"Updated {count} products!")

elif menu == "🔄 Initial Sync":
    st.header("Sync Data & Images")
    if st.button("🚀 Run Full Sync"):
        with st.spinner("Processing..."):
            all_p = []
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
                        tmp['SKUCode'] = tmp.apply(lambda row: row['SKUCode'] if row['SKUCode'] != "nan" and row['SKUCode'] != "N/A" else f"GEN_{uuid.uuid4().hex[:8]}", axis=1)
                        all_p.extend(tmp.to_dict(orient="records"))
                    except Exception as e: st.error(f"Error in {name}: {e}")
            
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
            st.success(f"Sync Complete! Saved {len(all_p)} products to GitHub.")
