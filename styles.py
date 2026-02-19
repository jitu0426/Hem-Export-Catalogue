"""
HEM Product Catalogue v3 - HEM Brand Light Theme
==================================================
Authentic HEM Corporation light palette:
  Primary:   HEM Crimson Red   #c8102e
  Secondary: Saffron Amber     #e8870a
  Accent:    Warm Gold         #fdbc00
  Background:Warm Cream White  #fff9f5
  Cards:     Pure White        #ffffff
  Dark text: Charcoal          #1a0a0a

Injected via st.markdown(APP_CSS, unsafe_allow_html=True) in app.py.
"""

APP_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════════════
   GOOGLE FONTS — Cinzel for headings + Inter for body
═══════════════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

/* ═══════════════════════════════════════════════════════════════════════════
   CSS DESIGN TOKENS — HEM Brand (Light Mode)
═══════════════════════════════════════════════════════════════════════════ */
:root {
    /* ── HEM Brand Reds ── */
    --hem-red:        #c8102e;
    --hem-red-deep:   #8b0a1e;
    --hem-red-light:  #e8304a;
    --hem-red-pale:   #fdedf0;
    --hem-red-glow:   rgba(200,16,46,0.14);

    /* ── Saffron / Amber ── */
    --saffron:        #e8870a;
    --saffron-light:  #f5a832;
    --saffron-pale:   #fff5e6;
    --saffron-glow:   rgba(232,135,10,0.15);

    /* ── Gold ── */
    --gold:           #fdbc00;
    --gold-dark:      #c49200;
    --gold-pale:      #fffbe6;

    /* ── Light Backgrounds ── */
    --bg-page:        #fff9f5;
    --bg-card:        #ffffff;
    --bg-card-warm:   #fffaf7;
    --bg-cream:       #fdf5ee;
    --bg-sidebar:     #1a0508;

    /* ── Borders ── */
    --border-red:     rgba(200,16,46,0.20);
    --border-saffron: rgba(232,135,10,0.22);
    --border-gold:    rgba(253,188,0,0.30);
    --border-light:   rgba(0,0,0,0.08);
    --border-medium:  rgba(0,0,0,0.12);

    /* ── Text ── */
    --text-dark:   #1a0a0a;
    --text-body:   #3d2020;
    --text-mid:    #6b4040;
    --text-muted:  #a07070;
    --text-white:  #ffffff;

    /* ── Shadows ── */
    --shadow-sm:   0 1px 4px rgba(200,16,46,0.08), 0 2px 8px rgba(0,0,0,0.06);
    --shadow-md:   0 4px 16px rgba(200,16,46,0.10), 0 2px 8px rgba(0,0,0,0.08);
    --shadow-lg:   0 8px 32px rgba(200,16,46,0.12), 0 4px 16px rgba(0,0,0,0.08);
    --shadow-red:  0 4px 20px rgba(200,16,46,0.25);

    /* ── Radius ── */
    --r-sm:  6px;
    --r-md:  12px;
    --r-lg:  18px;
    --r-xl:  24px;

    /* ── Transitions ── */
    --t-fast:   0.15s ease;
    --t-normal: 0.25s ease;
}

/* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL BASE — Warm cream background
═══════════════════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: var(--bg-page) !important;
    color: var(--text-body) !important;
    font-family: 'Inter', sans-serif;
}

.main .block-container {
    background: transparent !important;
    padding-top: 1rem;
    max-width: 1440px;
}

/* Subtle warm gradient background */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background:
        radial-gradient(ellipse 60% 40% at 10% 5%,  rgba(200,16,46,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 50% 35% at 90% 90%, rgba(232,135,10,0.03) 0%, transparent 60%),
        radial-gradient(ellipse 100% 100% at 50% 50%, #fff9f5 0%, #fdf4ee 100%);
    z-index: -1;
    pointer-events: none;
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN TITLE BANNER
═══════════════════════════════════════════════════════════════════════════ */
.main-title {
    background: linear-gradient(135deg,
        #c8102e 0%,
        #a50d26 30%,
        #8b0a1e 60%,
        #a50d26 80%,
        #c8102e 100%);
    border-radius: var(--r-xl);
    padding: 38px 52px 30px;
    margin-bottom: 28px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg), 0 0 0 1px rgba(255,255,255,0.08) inset;
}

/* Saffron shimmer sweep */
.main-title::before {
    content: '';
    position: absolute;
    top: 0; left: -150%;
    width: 300%; height: 100%;
    background: linear-gradient(90deg,
        transparent 30%,
        rgba(253,188,0,0.12) 50%,
        transparent 70%);
    animation: title-shimmer 5s ease-in-out infinite;
}

/* Bottom saffron-gold line */
.main-title::after {
    content: '';
    position: absolute;
    bottom: 0; left: 6%; right: 6%;
    height: 2px;
    background: linear-gradient(90deg,
        transparent,
        var(--saffron-light),
        var(--gold),
        var(--saffron-light),
        transparent);
    opacity: 0.7;
}

@keyframes title-shimmer {
    0%   { left: -150%; }
    100% { left: 100%;  }
}

/* Brand name */
.main-title .title-brand {
    font-family: 'Cinzel', serif;
    font-size: 46px;
    font-weight: 900;
    letter-spacing: 10px;
    text-transform: uppercase;
    background: linear-gradient(135deg,
        #ffd84d 0%,
        #fdbc00 25%,
        #ffffff 50%,
        #fdbc00 75%,
        #f5a832 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: block;
    margin-bottom: 8px;
    filter: drop-shadow(0 2px 12px rgba(0,0,0,0.25));
}

/* Subtitle */
.main-title .title-sub {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 5px;
    text-transform: uppercase;
    color: rgba(255,220,200,0.80);
    display: block;
    margin-top: 4px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB NAVIGATION
═══════════════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--r-lg);
    padding: 5px;
    gap: 3px;
    box-shadow: var(--shadow-sm);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 13px;
    color: var(--text-mid) !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    transition: all var(--t-normal);
    letter-spacing: 0.2px;
    font-family: 'Inter', sans-serif;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--hem-red) !important;
    background: var(--hem-red-pale) !important;
    border-color: var(--border-red) !important;
}

/* Active tab — HEM red */
.stTabs [aria-selected="true"] {
    background: var(--hem-red) !important;
    color: #ffffff !important;
    border-color: var(--hem-red) !important;
    box-shadow: var(--shadow-red) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════════════════════ */
/* ── Primary — HEM Red solid ── */
button[kind="primary"],
.stButton button[kind="primary"] {
    background: linear-gradient(135deg,
        #c8102e 0%,
        #e8304a 50%,
        #c8102e 100%) !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    box-shadow: 0 4px 14px rgba(200,16,46,0.30),
                inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: all var(--t-normal) !important;
    position: relative;
    overflow: hidden;
}
button[kind="primary"]::before {
    content: '';
    position: absolute;
    top: 0; left: -100%; width: 200%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    transition: left 0.4s ease;
}
button[kind="primary"]:hover::before { left: 100%; }
button[kind="primary"]:hover {
    box-shadow: 0 6px 22px rgba(200,16,46,0.40),
                inset 0 1px 0 rgba(255,255,255,0.20) !important;
    transform: translateY(-2px) !important;
}
button[kind="primary"]:active { transform: translateY(0) !important; }

/* ── Secondary — Saffron/Amber outline ── */
button[kind="secondary"],
.stButton button[kind="secondary"] {
    background: var(--saffron-pale) !important;
    color: var(--saffron) !important;
    border: 1px solid var(--border-saffron) !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    transition: all var(--t-normal) !important;
}
button[kind="secondary"]:hover {
    background: rgba(232,135,10,0.12) !important;
    border-color: var(--saffron) !important;
    box-shadow: 0 3px 12px rgba(232,135,10,0.20) !important;
    transform: translateY(-1px) !important;
}

/* ── Tertiary / default ── */
button[kind="tertiary"],
.stButton button {
    background: var(--bg-card) !important;
    color: var(--text-mid) !important;
    border: 1px solid var(--border-light) !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    transition: all var(--t-fast) !important;
    font-size: 12px !important;
}
button[kind="tertiary"]:hover {
    background: var(--hem-red-pale) !important;
    color: var(--hem-red) !important;
    border-color: var(--border-red) !important;
}

/* ── Download button — Gold ── */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg,
        var(--gold-pale),
        rgba(253,188,0,0.12)) !important;
    color: var(--gold-dark) !important;
    border: 1px solid var(--border-gold) !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    transition: all var(--t-normal) !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(253,188,0,0.20) !important;
    box-shadow: 0 3px 14px rgba(253,188,0,0.25) !important;
    transform: translateY(-1px) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   INPUT FIELDS
═══════════════════════════════════════════════════════════════════════════ */
.stTextInput input,
.stTextInput textarea {
    background: var(--bg-card) !important;
    color: var(--text-dark) !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--r-md) !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: border-color var(--t-fast), box-shadow var(--t-fast) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTextInput input::placeholder { color: var(--text-muted) !important; }
.stTextInput input:focus {
    border-color: var(--hem-red) !important;
    box-shadow: 0 0 0 3px var(--hem-red-glow), var(--shadow-sm) !important;
    outline: none !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--r-md) !important;
    color: var(--text-dark) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: border-color var(--t-fast) !important;
}
.stSelectbox > div > div:focus-within {
    border-color: var(--hem-red) !important;
    box-shadow: 0 0 0 3px var(--hem-red-glow), var(--shadow-sm) !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--r-md) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stMultiSelect > div > div:focus-within {
    border-color: var(--hem-red) !important;
    box-shadow: 0 0 0 3px var(--hem-red-glow) !important;
}
/* Chips */
[data-baseweb="tag"] {
    background: var(--hem-red-pale) !important;
    border: 1px solid var(--border-red) !important;
    color: var(--hem-red) !important;
    border-radius: 6px !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SIDEBAR — Deep HEM red dark (brand contrast)
═══════════════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,
        #1a0508 0%,
        #220a0c 40%,
        #1a0508 80%,
        #110305 100%) !important;
    border-right: 2px solid var(--hem-red) !important;
    box-shadow: 4px 0 24px rgba(200,16,46,0.15);
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--saffron-light) !important;
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.5px;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {
    color: rgba(255,220,200,0.75) !important;
}
section[data-testid="stSidebar"] .stCaption {
    color: rgba(200,130,130,0.65) !important;
    font-size: 11px;
}

/* Sidebar inputs */
section[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.08) !important;
    color: #fff9f5 !important;
    border-color: rgba(232,135,10,0.30) !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.08) !important;
    color: #fff9f5 !important;
    border-color: rgba(232,135,10,0.30) !important;
}

/* Sidebar buttons — saffron */
section[data-testid="stSidebar"] button {
    background: rgba(232,135,10,0.15) !important;
    color: var(--saffron-light) !important;
    border: 1px solid rgba(232,135,10,0.35) !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] button:hover {
    background: rgba(232,135,10,0.28) !important;
    box-shadow: 0 0 14px rgba(232,135,10,0.22) !important;
}

/* Sidebar expanders */
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(255,255,255,0.05) !important;
    color: var(--saffron-light) !important;
    border: 1px solid rgba(200,16,46,0.20) !important;
    border-radius: var(--r-md) !important;
}
section[data-testid="stSidebar"] .streamlit-expanderHeader:hover {
    background: rgba(200,16,46,0.12) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   EXPANDERS
═══════════════════════════════════════════════════════════════════════════ */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    color: var(--text-body) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--r-md) !important;
    padding: 12px 18px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all var(--t-fast) !important;
    box-shadow: var(--shadow-sm) !important;
}
.streamlit-expanderHeader:hover {
    border-color: var(--border-red) !important;
    color: var(--hem-red) !important;
    background: var(--hem-red-pale) !important;
}
.streamlit-expanderContent {
    background: var(--bg-card-warm) !important;
    border: 1px solid var(--border-light) !important;
    border-top: none !important;
    border-radius: 0 0 var(--r-md) var(--r-md) !important;
    padding: 12px 18px 16px !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SECTION HEADERS
═══════════════════════════════════════════════════════════════════════════ */
.section-header {
    background: linear-gradient(135deg,
        var(--hem-red-pale) 0%,
        rgba(232,135,10,0.05) 70%,
        var(--hem-red-pale) 100%);
    border: 1px solid var(--border-red);
    border-left: 4px solid var(--hem-red);
    border-radius: 0 var(--r-md) var(--r-md) 0;
    padding: 14px 24px;
    margin: 20px 0 16px;
    font-family: 'Cinzel', serif;
    font-size: 18px;
    font-weight: 700;
    color: var(--hem-red-deep);
    letter-spacing: 0.8px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: var(--shadow-sm);
    position: relative;
    overflow: hidden;
}
.section-header::after {
    content: '';
    position: absolute;
    right: 20px; top: 50%; transform: translateY(-50%);
    width: 50px; height: 1px;
    background: linear-gradient(90deg, var(--saffron), transparent);
    opacity: 0.6;
}

/* ═══════════════════════════════════════════════════════════════════════════
   GLASS CARD → Clean white card
═══════════════════════════════════════════════════════════════════════════ */
.glass-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--r-xl);
    padding: 24px 28px;
    box-shadow: var(--shadow-md);
    margin: 12px 0;
    transition: border-color var(--t-normal), box-shadow var(--t-normal);
    position: relative;
    overflow: hidden;
}
.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg,
        var(--hem-red),
        var(--saffron),
        var(--gold),
        var(--saffron),
        var(--hem-red));
    border-radius: var(--r-xl) var(--r-xl) 0 0;
}
.glass-card:hover {
    border-color: var(--border-red);
    box-shadow: var(--shadow-lg);
}

/* ═══════════════════════════════════════════════════════════════════════════
   STATS BAR
═══════════════════════════════════════════════════════════════════════════ */
.stats-bar {
    display: flex;
    gap: 24px;
    align-items: center;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-left: 3px solid var(--saffron);
    border-radius: var(--r-lg);
    padding: 14px 24px;
    margin: 12px 0 18px;
    box-shadow: var(--shadow-sm);
    flex-wrap: wrap;
}
.stat-item {
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 500;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}
.stat-value {
    font-size: 18px;
    font-weight: 700;
    color: var(--hem-red);
    font-family: 'Cinzel', serif;
    display: block;
    line-height: 1.2;
    margin-top: 2px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   PRODUCT BADGES
═══════════════════════════════════════════════════════════════════════════ */
.badge-new {
    display: inline-block;
    background: var(--hem-red);
    color: #ffffff;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 10px;
    margin-left: 6px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    animation: badge-pulse 2s ease-in-out infinite;
    vertical-align: middle;
}
@keyframes badge-pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.75; box-shadow: 0 0 8px rgba(200,16,46,0.50); }
}

.badge-modified {
    display: inline-block;
    background: var(--saffron-pale);
    color: var(--saffron);
    font-size: 9px; font-weight: 800;
    padding: 2px 8px; border-radius: 10px;
    border: 1px solid var(--border-saffron);
    margin-left: 6px; text-transform: uppercase; letter-spacing: 0.8px;
    vertical-align: middle;
}

.badge-custom {
    display: inline-block;
    background: var(--gold-pale);
    color: var(--gold-dark);
    font-size: 9px; font-weight: 800;
    padding: 2px 8px; border-radius: 10px;
    border: 1px solid var(--border-gold);
    margin-left: 6px; text-transform: uppercase; letter-spacing: 0.8px;
    vertical-align: middle;
}

.badge-in-cart {
    display: inline-block;
    background: linear-gradient(135deg, var(--hem-red), var(--hem-red-deep));
    color: #ffffff;
    font-size: 9px; font-weight: 800;
    padding: 2px 8px; border-radius: 10px;
    margin-left: 6px; text-transform: uppercase; letter-spacing: 0.8px;
    vertical-align: middle;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SUBCATEGORY HEADER
═══════════════════════════════════════════════════════════════════════════ */
.subcat-header {
    background: var(--saffron-pale);
    border-left: 3px solid var(--saffron);
    padding: 8px 14px;
    margin: 14px 0 6px;
    border-radius: 0 var(--r-sm) var(--r-sm) 0;
    font-size: 12px;
    font-weight: 700;
    color: var(--saffron);
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* ═══════════════════════════════════════════════════════════════════════════
   PRODUCT THUMBNAIL
═══════════════════════════════════════════════════════════════════════════ */
.product-thumb {
    border-radius: var(--r-sm);
    border: 1px solid var(--border-red);
    object-fit: cover;
    background: var(--bg-cream);
    box-shadow: var(--shadow-sm);
}
.product-thumb-placeholder {
    border-radius: var(--r-sm);
    border: 1px dashed var(--border-medium);
    background: var(--bg-cream);
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; color: var(--text-muted);
}

/* ═══════════════════════════════════════════════════════════════════════════
   PRODUCT ROW hover
═══════════════════════════════════════════════════════════════════════════ */
.product-row-hover {
    border-radius: var(--r-sm);
    transition: background-color var(--t-fast);
    padding: 2px 4px;
    margin: 1px 0;
}
.product-row-hover:hover {
    background: var(--hem-red-pale);
}

/* ═══════════════════════════════════════════════════════════════════════════
   CONFIRM DIALOG
═══════════════════════════════════════════════════════════════════════════ */
.confirm-dialog {
    background: var(--saffron-pale);
    border: 1px solid var(--border-saffron);
    border-radius: var(--r-md);
    padding: 16px 20px;
    margin: 8px 0;
    color: var(--saffron);
    font-size: 14px;
}
.confirm-dialog-danger {
    background: var(--hem-red-pale);
    border: 1px solid var(--border-red);
    border-radius: var(--r-md);
    padding: 16px 20px;
    margin: 8px 0;
    color: var(--hem-red-deep);
    font-size: 14px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   DATA EDITOR
═══════════════════════════════════════════════════════════════════════════ */
div[data-testid="stDataEditor"] {
    border: 1px solid var(--border-light) !important;
    border-radius: var(--r-lg) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-md) !important;
}
div[data-testid="stDataEditor"] thead th {
    background: var(--hem-red-pale) !important;
    color: var(--hem-red-deep) !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid var(--border-red) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   METRICS
═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--r-lg);
    padding: 18px 22px;
    box-shadow: var(--shadow-sm);
    transition: all var(--t-normal);
    position: relative;
    overflow: hidden;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg,
        var(--hem-red),
        var(--saffron),
        var(--gold));
}
[data-testid="stMetric"]:hover {
    border-color: var(--border-red);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
[data-testid="stMetricValue"] {
    color: var(--hem-red) !important;
    font-family: 'Cinzel', serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ALERTS
═══════════════════════════════════════════════════════════════════════════ */
.stAlert { border-radius: var(--r-md) !important; }
[data-testid="stAlert"] {
    border-radius: var(--r-md) !important;
    background: var(--bg-card) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   PROGRESS BAR — HEM Red → Saffron → Gold
═══════════════════════════════════════════════════════════════════════════ */
.stProgress > div > div > div {
    background: linear-gradient(90deg,
        var(--hem-red),
        var(--saffron),
        var(--gold)) !important;
    border-radius: 4px !important;
    box-shadow: 0 0 8px var(--saffron-glow) !important;
}
.stProgress > div > div {
    background: var(--border-light) !important;
    border-radius: 4px !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   FORM
═══════════════════════════════════════════════════════════════════════════ */
.stForm {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: var(--r-xl) !important;
    padding: 24px !important;
    box-shadow: var(--shadow-md) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHECKBOXES
═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stCheckbox"] label {
    color: var(--text-body) !important;
    font-size: 13px !important;
}
[data-testid="stCheckbox"] input[type="checkbox"]:checked + div {
    background: var(--hem-red) !important;
    border-color: var(--hem-red) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   RADIO BUTTONS
═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stRadio"] label {
    color: var(--text-body) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   DIVIDERS
═══════════════════════════════════════════════════════════════════════════ */
hr {
    border: none !important;
    border-top: 1px solid var(--border-light) !important;
    margin: 24px 0 !important;
    position: relative;
}
hr::after {
    content: '🔥';
    position: absolute;
    left: 50%; transform: translateX(-50%) translateY(-60%);
    background: var(--bg-page);
    padding: 0 10px;
    font-size: 12px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCROLLBAR — Subtle red
═══════════════════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f5eeee; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(var(--hem-red-light), var(--saffron));
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--hem-red); }

/* ═══════════════════════════════════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stToast"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-red) !important;
    border-left: 4px solid var(--hem-red) !important;
    border-radius: var(--r-md) !important;
    color: var(--text-body) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   EMPTY STATE
═══════════════════════════════════════════════════════════════════════════ */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}
.empty-state-icon {
    font-size: 56px;
    margin-bottom: 20px;
    opacity: 0.4;
}

/* ═══════════════════════════════════════════════════════════════════════════
   HEM RED DIVIDER (was gold-divider)
═══════════════════════════════════════════════════════════════════════════ */
.gold-divider {
    height: 2px;
    background: linear-gradient(90deg,
        transparent,
        var(--hem-red),
        var(--saffron),
        var(--hem-red),
        transparent);
    margin: 24px 0;
    border: none;
    opacity: 0.35;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CART BADGE
═══════════════════════════════════════════════════════════════════════════ */
.cart-glow {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--hem-red);
    color: #ffffff;
    font-size: 11px;
    font-weight: 800;
    min-width: 22px;
    height: 22px;
    border-radius: 11px;
    padding: 0 7px;
    margin-left: 8px;
    box-shadow: 0 2px 8px rgba(200,16,46,0.40);
    letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
    .main-title .title-brand { font-size: 28px; letter-spacing: 4px; }
    .main-title { padding: 24px 20px 18px; }
    .stats-bar { flex-direction: column; gap: 10px; }
    .section-header { font-size: 16px; padding: 12px 18px; }
}
</style>
"""
