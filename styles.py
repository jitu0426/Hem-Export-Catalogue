"""
HEM Product Catalogue v3 - Luxury Dark Gold Theme
===================================================
Full CSS for a premium dark-themed app with gold accents,
animated gradients, glassmorphism cards, and rich typography.
Injected via st.markdown(APP_CSS, unsafe_allow_html=True) in app.py.
"""

APP_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════════════
   GOOGLE FONTS
═══════════════════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

/* ═══════════════════════════════════════════════════════════════════════════
   CSS DESIGN TOKENS
═══════════════════════════════════════════════════════════════════════════ */
:root {
    /* Dark backgrounds */
    --bg-deep:    #0a0a0f;
    --bg-dark:    #0f0f18;
    --bg-card:    #141420;
    --bg-card2:   #1a1a2e;
    --bg-glass:   rgba(20,20,35,0.85);

    /* Gold palette */
    --gold:       #c9a84c;
    --gold-light: #e8cc7a;
    --gold-dark:  #9a7a2e;
    --gold-glow:  rgba(201,168,76,0.25);
    --gold-glow2: rgba(201,168,76,0.08);

    /* Accent colors */
    --accent-blue:   #4a9eff;
    --accent-green:  #2ecc71;
    --accent-red:    #e74c3c;
    --accent-purple: #9b59b6;

    /* Text */
    --text-white:  #ffffff;
    --text-light:  #e8e8f0;
    --text-mid:    #a0a0c0;
    --text-muted:  #60607a;

    /* Borders */
    --border-gold:   rgba(201,168,76,0.3);
    --border-glass:  rgba(255,255,255,0.08);
    --border-dark:   rgba(255,255,255,0.04);

    /* Shadows */
    --shadow-gold:   0 0 30px rgba(201,168,76,0.15);
    --shadow-dark:   0 8px 32px rgba(0,0,0,0.6);
    --shadow-card:   0 4px 20px rgba(0,0,0,0.4);
    --shadow-glow:   0 0 60px rgba(201,168,76,0.1);

    /* Spacing & radius */
    --r-sm:  6px;
    --r-md:  12px;
    --r-lg:  18px;
    --r-xl:  24px;

    /* Transitions */
    --t-fast:   0.15s ease;
    --t-normal: 0.25s ease;
    --t-slow:   0.4s ease;
}

/* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL RESET & BASE
═══════════════════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

/* Dark background for the entire app */
.stApp {
    background: var(--bg-deep) !important;
    color: var(--text-light) !important;
    font-family: 'Inter', sans-serif;
}

/* Remove Streamlit default white background */
.main .block-container {
    background: transparent !important;
    padding-top: 1rem;
    max-width: 1400px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ANIMATED BACKGROUND (subtle moving gradient)
═══════════════════════════════════════════════════════════════════════════ */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background:
        radial-gradient(ellipse 80% 50% at 20% 20%, rgba(201,168,76,0.05) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(74,158,255,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 100% 100% at 50% 50%, #0a0a0f 0%, #060608 100%);
    z-index: -1;
    pointer-events: none;
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN TITLE BANNER — Luxury logo header
═══════════════════════════════════════════════════════════════════════════ */
.main-title {
    background: linear-gradient(135deg,
        #0a0a0f 0%,
        #141425 30%,
        #1a1a35 60%,
        #0f0f1f 100%);
    border: 1px solid var(--border-gold);
    border-radius: var(--r-xl);
    padding: 36px 48px 28px;
    margin-bottom: 32px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-dark), var(--shadow-glow), inset 0 1px 0 rgba(201,168,76,0.2);
}

/* Shimmer sweep animation */
.main-title::before {
    content: '';
    position: absolute;
    top: 0; left: -150%;
    width: 300%; height: 100%;
    background: linear-gradient(90deg,
        transparent 30%,
        rgba(201,168,76,0.06) 50%,
        transparent 70%);
    animation: title-shimmer 4s ease-in-out infinite;
}

/* Gold horizontal rule above text */
.main-title::after {
    content: '';
    position: absolute;
    bottom: 0; left: 10%; right: 10%;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    opacity: 0.6;
}

@keyframes title-shimmer {
    0%   { left: -150%; }
    100% { left: 100%; }
}

/* The title text */
.main-title .title-brand {
    font-family: 'Playfair Display', serif;
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 6px;
    text-transform: uppercase;
    background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 50%, var(--gold-dark) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: block;
    margin-bottom: 6px;
    text-shadow: none;
    filter: drop-shadow(0 0 20px rgba(201,168,76,0.4));
}
.main-title .title-sub {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 400;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--text-mid);
    display: block;
    margin-top: 4px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB NAVIGATION
═══════════════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(20,20,35,0.9);
    border: 1px solid var(--border-glass);
    border-radius: var(--r-lg);
    padding: 6px;
    gap: 4px;
    backdrop-filter: blur(10px);
    box-shadow: var(--shadow-card);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 26px;
    font-weight: 600;
    font-size: 13px;
    color: var(--text-mid) !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    transition: all var(--t-normal);
    letter-spacing: 0.3px;
    font-family: 'Inter', sans-serif;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--gold-light) !important;
    background: rgba(201,168,76,0.06) !important;
    border-color: var(--border-gold) !important;
}

/* Active tab — gold gradient fill */
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(201,168,76,0.2), rgba(201,168,76,0.08)) !important;
    color: var(--gold-light) !important;
    border-color: var(--border-gold) !important;
    box-shadow: 0 0 20px rgba(201,168,76,0.15), inset 0 1px 0 rgba(201,168,76,0.2) !important;
}

/* Tab highlight bar — hide default blue underline */
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════════════════════ */
/* ── Primary (gold) ── */
button[kind="primary"],
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #c9a84c 0%, #e8cc7a 50%, #9a7a2e 100%) !important;
    color: #0a0a0f !important;
    border: none !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    box-shadow: 0 4px 15px rgba(201,168,76,0.3), inset 0 1px 0 rgba(255,255,255,0.2) !important;
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
    box-shadow: 0 8px 25px rgba(201,168,76,0.5), inset 0 1px 0 rgba(255,255,255,0.3) !important;
    transform: translateY(-2px) !important;
}
button[kind="primary"]:active { transform: translateY(0) !important; }

/* ── Secondary (dark glass blue) ── */
button[kind="secondary"],
.stButton button[kind="secondary"] {
    background: linear-gradient(135deg, rgba(74,158,255,0.15), rgba(74,158,255,0.05)) !important;
    color: var(--accent-blue) !important;
    border: 1px solid rgba(74,158,255,0.3) !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    transition: all var(--t-normal) !important;
    backdrop-filter: blur(8px) !important;
}
button[kind="secondary"]:hover {
    background: linear-gradient(135deg, rgba(74,158,255,0.25), rgba(74,158,255,0.12)) !important;
    border-color: var(--accent-blue) !important;
    box-shadow: 0 4px 20px rgba(74,158,255,0.25) !important;
    transform: translateY(-2px) !important;
}

/* ── Tertiary / default ── */
button[kind="tertiary"],
.stButton button {
    background: rgba(255,255,255,0.04) !important;
    color: var(--text-mid) !important;
    border: 1px solid var(--border-glass) !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    transition: all var(--t-fast) !important;
    font-size: 12px !important;
}
button[kind="tertiary"]:hover {
    background: rgba(255,255,255,0.08) !important;
    color: var(--text-light) !important;
    border-color: rgba(255,255,255,0.15) !important;
}

/* ── Download button (green) ── */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, rgba(46,204,113,0.2), rgba(46,204,113,0.08)) !important;
    color: var(--accent-green) !important;
    border: 1px solid rgba(46,204,113,0.35) !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    transition: all var(--t-normal) !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg, rgba(46,204,113,0.3), rgba(46,204,113,0.15)) !important;
    box-shadow: 0 4px 20px rgba(46,204,113,0.3) !important;
    transform: translateY(-2px) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   INPUT FIELDS — Dark glass style
═══════════════════════════════════════════════════════════════════════════ */
.stTextInput input,
.stTextInput textarea {
    background: rgba(20,20,35,0.8) !important;
    color: var(--text-light) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--r-md) !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: border-color var(--t-fast), box-shadow var(--t-fast) !important;
    backdrop-filter: blur(8px) !important;
}
.stTextInput input::placeholder { color: var(--text-muted) !important; }
.stTextInput input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important;
    background: rgba(25,25,42,0.95) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(20,20,35,0.8) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--r-md) !important;
    color: var(--text-light) !important;
    transition: border-color var(--t-fast), box-shadow var(--t-fast) !important;
}
.stSelectbox > div > div:focus-within {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    background: rgba(20,20,35,0.8) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--r-md) !important;
}
.stMultiSelect > div > div:focus-within {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important;
}
/* Selected chips in multiselect */
[data-baseweb="tag"] {
    background: linear-gradient(135deg, rgba(201,168,76,0.2), rgba(201,168,76,0.1)) !important;
    border: 1px solid var(--border-gold) !important;
    color: var(--gold-light) !important;
    border-radius: 6px !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SIDEBAR — Dark navy
═══════════════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080810 0%, #0c0c1a 50%, #080810 100%) !important;
    border-right: 1px solid var(--border-gold) !important;
    box-shadow: 4px 0 30px rgba(0,0,0,0.5);
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--gold) !important;
    font-family: 'Playfair Display', serif !important;
    letter-spacing: 0.5px;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {
    color: var(--text-mid) !important;
}
section[data-testid="stSidebar"] .stCaption {
    color: var(--text-muted) !important;
    font-size: 11px;
}

/* Sidebar inputs */
section[data-testid="stSidebar"] .stTextInput input {
    background: rgba(201,168,76,0.05) !important;
    border-color: rgba(201,168,76,0.2) !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(201,168,76,0.05) !important;
    border-color: rgba(201,168,76,0.2) !important;
}

/* Sidebar buttons: gold style */
section[data-testid="stSidebar"] button {
    background: linear-gradient(135deg, rgba(201,168,76,0.15), rgba(201,168,76,0.05)) !important;
    color: var(--gold-light) !important;
    border: 1px solid var(--border-gold) !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] button:hover {
    background: linear-gradient(135deg, rgba(201,168,76,0.25), rgba(201,168,76,0.12)) !important;
    box-shadow: 0 0 15px rgba(201,168,76,0.2) !important;
}

/* Sidebar expanders */
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(201,168,76,0.04) !important;
    color: var(--gold-light) !important;
    border: 1px solid rgba(201,168,76,0.15) !important;
    border-radius: var(--r-md) !important;
}
section[data-testid="stSidebar"] .streamlit-expanderHeader:hover {
    background: rgba(201,168,76,0.08) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   EXPANDERS
═══════════════════════════════════════════════════════════════════════════ */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(20,20,35,0.9), rgba(25,25,45,0.7)) !important;
    color: var(--text-light) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--r-md) !important;
    padding: 12px 18px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all var(--t-fast) !important;
    backdrop-filter: blur(8px);
}
.streamlit-expanderHeader:hover {
    border-color: var(--border-gold) !important;
    color: var(--gold-light) !important;
    background: linear-gradient(135deg, rgba(201,168,76,0.06), rgba(20,20,35,0.9)) !important;
}
.streamlit-expanderContent {
    background: rgba(14,14,24,0.6) !important;
    border: 1px solid var(--border-dark) !important;
    border-top: none !important;
    border-radius: 0 0 var(--r-md) var(--r-md) !important;
    padding: 12px 18px 16px !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SECTION HEADERS (inside tabs)
═══════════════════════════════════════════════════════════════════════════ */
.section-header {
    background: linear-gradient(135deg,
        rgba(201,168,76,0.12) 0%,
        rgba(201,168,76,0.04) 100%);
    border: 1px solid var(--border-gold);
    border-left: 4px solid var(--gold);
    border-radius: 0 var(--r-md) var(--r-md) 0;
    padding: 14px 24px;
    margin: 20px 0 16px;
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    font-weight: 700;
    color: var(--gold-light);
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: var(--shadow-gold), inset 0 1px 0 rgba(201,168,76,0.1);
    position: relative;
    overflow: hidden;
}
.section-header::after {
    content: '';
    position: absolute;
    right: 20px; top: 50%; transform: translateY(-50%);
    width: 60px; height: 1px;
    background: linear-gradient(90deg, var(--gold), transparent);
    opacity: 0.5;
}

/* ═══════════════════════════════════════════════════════════════════════════
   GLASS CARD component (used via st.markdown)
═══════════════════════════════════════════════════════════════════════════ */
.glass-card {
    background: linear-gradient(135deg, rgba(20,20,35,0.9), rgba(14,14,24,0.8));
    border: 1px solid var(--border-glass);
    border-radius: var(--r-xl);
    padding: 24px 28px;
    backdrop-filter: blur(16px);
    box-shadow: var(--shadow-card);
    margin: 12px 0;
    transition: border-color var(--t-normal), box-shadow var(--t-normal);
    position: relative;
    overflow: hidden;
}
.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201,168,76,0.3), transparent);
}
.glass-card:hover {
    border-color: var(--border-gold);
    box-shadow: var(--shadow-card), var(--shadow-gold);
}

/* ═══════════════════════════════════════════════════════════════════════════
   STATS BAR
═══════════════════════════════════════════════════════════════════════════ */
.stats-bar {
    display: flex;
    gap: 24px;
    align-items: center;
    background: linear-gradient(135deg, rgba(20,20,35,0.8), rgba(14,14,24,0.6));
    border: 1px solid var(--border-glass);
    border-radius: var(--r-lg);
    padding: 14px 24px;
    margin: 12px 0 18px;
    backdrop-filter: blur(8px);
    flex-wrap: wrap;
}
.stat-item {
    font-size: 12px;
    color: var(--text-mid);
    font-weight: 500;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}
.stat-value {
    font-size: 18px;
    font-weight: 700;
    color: var(--gold-light);
    font-family: 'Playfair Display', serif;
    display: block;
    line-height: 1.2;
    margin-top: 2px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   PRODUCT BADGES
═══════════════════════════════════════════════════════════════════════════ */
.badge-new {
    display: inline-block;
    background: linear-gradient(135deg, rgba(231,76,60,0.25), rgba(192,57,43,0.15));
    color: #ff8070;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid rgba(231,76,60,0.4);
    margin-left: 6px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    animation: badge-pulse 2s ease-in-out infinite;
    vertical-align: middle;
}
@keyframes badge-pulse {
    0%, 100% { opacity: 1; box-shadow: none; }
    50% { opacity: 0.7; box-shadow: 0 0 6px rgba(231,76,60,0.4); }
}
.badge-modified {
    display: inline-block;
    background: linear-gradient(135deg, rgba(241,196,15,0.2), rgba(243,156,18,0.1));
    color: #f1c40f;
    font-size: 9px; font-weight: 800;
    padding: 2px 8px; border-radius: 10px;
    border: 1px solid rgba(241,196,15,0.35);
    margin-left: 6px; text-transform: uppercase; letter-spacing: 0.8px;
    vertical-align: middle;
}
.badge-custom {
    display: inline-block;
    background: linear-gradient(135deg, rgba(46,204,113,0.2), rgba(39,174,96,0.1));
    color: #2ecc71;
    font-size: 9px; font-weight: 800;
    padding: 2px 8px; border-radius: 10px;
    border: 1px solid rgba(46,204,113,0.35);
    margin-left: 6px; text-transform: uppercase; letter-spacing: 0.8px;
    vertical-align: middle;
}
.badge-in-cart {
    display: inline-block;
    background: linear-gradient(135deg, rgba(201,168,76,0.2), rgba(201,168,76,0.08));
    color: var(--gold-light);
    font-size: 9px; font-weight: 800;
    padding: 2px 8px; border-radius: 10px;
    border: 1px solid var(--border-gold);
    margin-left: 6px; text-transform: uppercase; letter-spacing: 0.8px;
    vertical-align: middle;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SUBCATEGORY HEADER (in product list)
═══════════════════════════════════════════════════════════════════════════ */
.subcat-header {
    background: linear-gradient(135deg, rgba(74,158,255,0.1), rgba(74,158,255,0.03));
    border-left: 3px solid var(--accent-blue);
    padding: 8px 14px;
    margin: 14px 0 6px;
    border-radius: 0 var(--r-sm) var(--r-sm) 0;
    font-size: 12px;
    font-weight: 700;
    color: var(--accent-blue);
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* ═══════════════════════════════════════════════════════════════════════════
   PRODUCT THUMBNAIL
═══════════════════════════════════════════════════════════════════════════ */
.product-thumb {
    border-radius: var(--r-sm);
    border: 1px solid var(--border-gold);
    object-fit: cover;
    background: var(--bg-card);
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
.product-thumb-placeholder {
    border-radius: var(--r-sm);
    border: 1px solid var(--border-glass);
    background: linear-gradient(135deg, rgba(201,168,76,0.05), rgba(20,20,35,0.8));
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; color: var(--text-muted);
}

/* ═══════════════════════════════════════════════════════════════════════════
   PRODUCT ROW hover effect
═══════════════════════════════════════════════════════════════════════════ */
.product-row-hover {
    border-radius: var(--r-sm);
    transition: background-color var(--t-fast);
    padding: 2px 4px;
    margin: 1px 0;
}
.product-row-hover:hover {
    background: rgba(201,168,76,0.04);
}

/* ═══════════════════════════════════════════════════════════════════════════
   CONFIRM DIALOG
═══════════════════════════════════════════════════════════════════════════ */
.confirm-dialog {
    background: linear-gradient(135deg, rgba(241,196,15,0.08), rgba(243,156,18,0.04));
    border: 1px solid rgba(241,196,15,0.3);
    border-radius: var(--r-md);
    padding: 16px 20px;
    margin: 8px 0;
    color: #f1c40f;
    font-size: 14px;
    backdrop-filter: blur(8px);
}
.confirm-dialog-danger {
    background: linear-gradient(135deg, rgba(231,76,60,0.1), rgba(192,57,43,0.05));
    border: 1px solid rgba(231,76,60,0.35);
    border-radius: var(--r-md);
    padding: 16px 20px;
    margin: 8px 0;
    color: #ff8070;
    font-size: 14px;
    backdrop-filter: blur(8px);
}

/* ═══════════════════════════════════════════════════════════════════════════
   DATA EDITOR (st.data_editor)
═══════════════════════════════════════════════════════════════════════════ */
div[data-testid="stDataEditor"] {
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--r-lg) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-card) !important;
    background: rgba(14,14,24,0.9) !important;
}
div[data-testid="stDataEditor"] thead th {
    background: rgba(201,168,76,0.08) !important;
    color: var(--gold-light) !important;
    font-weight: 700 !important;
    font-size: 11px !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--border-gold) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   METRICS
═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(20,20,35,0.9), rgba(14,14,24,0.7));
    border: 1px solid var(--border-glass);
    border-radius: var(--r-lg);
    padding: 18px 22px;
    box-shadow: var(--shadow-card);
    transition: border-color var(--t-normal), box-shadow var(--t-normal);
    position: relative;
    overflow: hidden;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--gold-dark), var(--gold), var(--gold-dark));
}
[data-testid="stMetric"]:hover {
    border-color: var(--border-gold);
    box-shadow: var(--shadow-card), var(--shadow-gold);
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
[data-testid="stMetricValue"] {
    color: var(--gold-light) !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   ALERTS / INFO / WARNING / ERROR
═══════════════════════════════════════════════════════════════════════════ */
.stAlert {
    border-radius: var(--r-md) !important;
    backdrop-filter: blur(8px) !important;
}
[data-testid="stAlert"] {
    border-radius: var(--r-md) !important;
    background: rgba(20,20,35,0.85) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   PROGRESS BAR
═══════════════════════════════════════════════════════════════════════════ */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--gold-dark), var(--gold), var(--gold-light)) !important;
    border-radius: 4px !important;
    box-shadow: 0 0 10px var(--gold-glow) !important;
}
.stProgress > div > div {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 4px !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   FORM
═══════════════════════════════════════════════════════════════════════════ */
.stForm {
    background: linear-gradient(135deg, rgba(20,20,35,0.9), rgba(14,14,24,0.7)) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: var(--r-xl) !important;
    padding: 24px !important;
    backdrop-filter: blur(16px) !important;
    box-shadow: var(--shadow-card) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHECKBOXES
═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stCheckbox"] label {
    color: var(--text-light) !important;
    font-size: 13px !important;
}
[data-testid="stCheckbox"] input[type="checkbox"]:checked + div {
    background: var(--gold) !important;
    border-color: var(--gold) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   DIVIDERS
═══════════════════════════════════════════════════════════════════════════ */
hr {
    border: none !important;
    border-top: 1px solid var(--border-glass) !important;
    margin: 24px 0 !important;
    position: relative;
}
hr::after {
    content: '◆';
    position: absolute;
    left: 50%; transform: translateX(-50%) translateY(-50%);
    background: var(--bg-dark);
    padding: 0 12px;
    color: var(--gold-dark);
    font-size: 10px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb {
    background: linear-gradient(var(--gold-dark), var(--gold));
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ═══════════════════════════════════════════════════════════════════════════
   TOAST NOTIFICATION
═══════════════════════════════════════════════════════════════════════════ */
[data-testid="stToast"] {
    background: rgba(20,20,35,0.95) !important;
    border: 1px solid var(--border-gold) !important;
    border-radius: var(--r-md) !important;
    color: var(--text-light) !important;
    backdrop-filter: blur(16px) !important;
    box-shadow: var(--shadow-dark), var(--shadow-gold) !important;
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
    opacity: 0.35;
    filter: grayscale(0.3);
}

/* ═══════════════════════════════════════════════════════════════════════════
   GOLD SEPARATOR (decorative line)
═══════════════════════════════════════════════════════════════════════════ */
.gold-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    margin: 24px 0;
    border: none;
    opacity: 0.4;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CART GLOW CARD (cart count metric)
═══════════════════════════════════════════════════════════════════════════ */
.cart-glow {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--gold), var(--gold-dark));
    color: #0a0a0f;
    font-size: 11px;
    font-weight: 800;
    min-width: 22px;
    height: 22px;
    border-radius: 11px;
    padding: 0 7px;
    margin-left: 8px;
    box-shadow: 0 0 12px rgba(201,168,76,0.5);
    letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
    .main-title .title-brand { font-size: 26px; letter-spacing: 3px; }
    .main-title { padding: 22px 20px 18px; }
    .stats-bar { flex-direction: column; gap: 10px; }
    .section-header { font-size: 16px; padding: 12px 18px; }
}
</style>
"""
