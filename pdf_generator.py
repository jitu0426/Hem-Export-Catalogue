"""
HEM Product Catalogue v3 — PDF & Excel Generator
==================================================
PDF engine priority:
  1. wkhtmltopdf (pdfkit)  — Windows local, if binary found
  2. WeasyPrint             — Streamlit Cloud (Linux), pure-Python, no binary needed

Excel uses xlsxwriter for professional formatting.
"""

import os
import io
import gc
import platform
import subprocess
import logging

import pandas as pd
import streamlit as st

from config import BASE_DIR, LOGO_PATH, STORY_IMG_1_PATH, COVER_IMAGE_URL, JOURNEY_IMAGE_URL
from cloudinary_client import get_image_as_base64_str
from data_loader import create_safe_id

logger = logging.getLogger(__name__)

# ── Optional WeasyPrint import (available on Streamlit Cloud) ─────────────
HAS_WEASYPRINT = False
try:
    from weasyprint import HTML as WP_HTML
    HAS_WEASYPRINT = True
    logger.info("WeasyPrint available ✓")
except Exception as e:
    logger.info(f"WeasyPrint not available ({e}) — will use pdfkit if possible.")

# ── pdfkit / wkhtmltopdf configuration ───────────────────────────────────
import pdfkit
PDFKIT_CONFIG = None
try:
    if platform.system() == "Windows":
        candidates = [
            r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
            r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
            os.path.join(BASE_DIR, "bin", "wkhtmltopdf.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=p)
                logger.info(f"wkhtmltopdf found: {p}")
                break
    else:
        # Linux / macOS
        try:
            wp_path = subprocess.check_output(["which", "wkhtmltopdf"]).decode().strip()
            PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=wp_path)
        except Exception:
            if os.path.exists("/usr/bin/wkhtmltopdf"):
                PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
except Exception as e:
    logger.warning(f"pdfkit config error: {e}")
    PDFKIT_CONFIG = None


# ═════════════════════════════════════════════════════════════════════════
# STORY PAGE HTML
# ═════════════════════════════════════════════════════════════════════════
def generate_story_html(story_img_b64: str) -> str:
    """Build the 'Our Journey' page HTML for insertion into the catalogue PDF."""
    text1 = (
        "HEM Corporation is amongst top global leaders in the manufacturing and export "
        "of perfumed agarbattis. For over three decades we have been distributing "
        "high-quality masala sticks, agarbattis, dhoops, and cones to customers in "
        "more than 70 countries. HEM has been awarded as the 'Top Exporters' brand "
        "for incense sticks by the Export Promotion Council for Handicraft (EPCH) "
        "for three consecutive years (2008–2011)."
    )
    text2 = (
        "From a brand founded by three brothers in 1983, HEM Fragrances has come a "
        "long way. HEM started as a simple incense store offering masala agarbatti, "
        "thuribles, and dhoops. With time, HEM expanded to meet the global demand for "
        "aromatherapy, meditation aids, and premium fragrance products. Today HEM "
        "serves over 70 countries and is the most preferred incense brand worldwide."
    )
    img_tag = (
        f'<img src="data:image/jpeg;base64,{story_img_b64}" '
        f'style="max-width:100%;height:auto;border:1px solid #c9a84c;border-radius:6px;" />'
        if story_img_b64
        else '<div style="padding:40px;border:2px dashed #c9a84c;color:#c9a84c;text-align:center;">Image not found</div>'
    )
    return f"""
    <div class="story-page" style="page-break-after:always;padding:25px 50px;
         font-family:sans-serif;background:#0a0a0f;color:#e8e8f0;">
      <h1 style="text-align:center;color:#c9a84c;font-size:28pt;margin-bottom:16px;
                 letter-spacing:3px;text-transform:uppercase;">Our Journey</h1>
      <div style="height:2px;background:linear-gradient(90deg,transparent,#c9a84c,transparent);margin-bottom:24px;"></div>
      <p style="font-size:11pt;line-height:1.7;margin-bottom:20px;text-align:justify;">{text1}</p>
      <div style="overflow:auto;margin-bottom:20px;">
        <div style="float:left;width:50%;padding-right:20px;font-size:11pt;line-height:1.7;text-align:justify;">{text2}</div>
        <div style="float:right;width:46%;text-align:center;">{img_tag}</div>
      </div>
      <div style="clear:both;"></div>
      <h2 style="text-align:center;font-size:13pt;color:#c9a84c;margin-top:24px;letter-spacing:2px;">
        INNOVATION · CREATIVITY · SUSTAINABILITY
      </h2>
    </div>
    """


# ═════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS HTML
# ═════════════════════════════════════════════════════════════════════════
def generate_table_of_contents_html(df_sorted: pd.DataFrame) -> str:
    """Generate the Table of Contents with category thumbnail cards."""
    css = """
    <style>
      .toc-title{text-align:center;font-family:serif;font-size:30pt;color:#c9a84c;
                 margin:10px 0 6px;text-transform:uppercase;letter-spacing:3px;}
      .toc-gold-line{height:2px;background:linear-gradient(90deg,transparent,#c9a84c,transparent);
                     margin:0 auto 20px;width:60%;}
      h3.toc-cat-header{background:linear-gradient(135deg,#1a1a2e,#141420);
                        color:#c9a84c;font-family:sans-serif;font-size:14pt;
                        padding:10px 16px;margin:0 0 14px;border-left:5px solid #c9a84c;
                        border-radius:0 6px 6px 0;page-break-inside:avoid;}
      .idx-grid{display:block;width:100%;font-size:0;}
      a.idx-card{display:inline-block;width:30%;margin:1.5%;height:195px;
                 background:#141420;border-radius:8px;text-decoration:none;
                 overflow:hidden;border:1px solid rgba(201,168,76,0.3);
                 page-break-inside:avoid;vertical-align:top;}
      .idx-img{width:100%;height:155px;background-repeat:no-repeat;
               background-position:center;background-size:contain;background-color:#0f0f18;}
      .idx-label{height:40px;background:linear-gradient(135deg,#c9a84c,#9a7a2e);
                 color:#0a0a0f;font-family:sans-serif;font-size:8.5pt;font-weight:800;
                 display:block;line-height:40px;text-align:center;text-transform:uppercase;
                 letter-spacing:0.8px;white-space:nowrap;overflow:hidden;
                 text-overflow:ellipsis;padding:0 10px;}
      .clearfix::after{content:"";clear:both;display:table;}
    </style>
    <div id="main-index" class="toc-page"
         style="page-break-after:always;padding:20px;background:#0a0a0f;">
      <h1 class="toc-title">Table of Contents</h1>
      <div class="toc-gold-line"></div>
    """
    catalogues = df_sorted["Catalogue"].unique()
    first = True
    for cat_name in catalogues:
        pb = "" if first else 'style="page-break-before:always;padding-top:20px;"'
        css += f'<div {pb}>'
        css += f'<h3 class="toc-cat-header">{cat_name}</h3>'
        css += '<div class="idx-grid clearfix">'
        cat_df = df_sorted[df_sorted["Catalogue"] == cat_name]
        for category in cat_df["Category"].unique():
            grp = cat_df[cat_df["Category"] == category]
            rep_img = ""
            for _, row in grp.iterrows():
                s = str(row.get("ImageB64", ""))
                if len(s) > 100:
                    rep_img = s
                    break
            bg = f"background-image:url('data:image/png;base64,{rep_img}');" if rep_img else "background-color:#1a1a2e;"
            safe_id = create_safe_id(category)
            css += f"""
            <a href="#category-{safe_id}" class="idx-card">
              <div class="idx-img" style="{bg}"></div>
              <div class="idx-label">{category}</div>
            </a>"""
        css += "</div><div style='clear:both;'></div></div>"
        first = False
    css += "</div>"
    return css


# ═════════════════════════════════════════════════════════════════════════
# FULL PDF HTML BUILDER
# ═════════════════════════════════════════════════════════════════════════
def generate_pdf_html(df_sorted: pd.DataFrame, customer_name: str,
                      logo_b64: str, case_selection_map: dict) -> str:
    """Assemble complete HTML: Cover → Story → TOC → Product pages."""

    def load_img(fname, specific=None, resize=False, max_size=(500, 500)):
        """Try multiple paths to load an image as base64."""
        paths = []
        if specific:
            paths.append(specific)
        paths += [
            os.path.join(BASE_DIR, "assets", fname),
            os.path.join(BASE_DIR, fname),
        ]
        for p in paths:
            if os.path.exists(p):
                return get_image_as_base64_str(p, resize=resize, max_size=max_size)
        return ""

    # Load images
    cover_b64    = get_image_as_base64_str(COVER_IMAGE_URL) or load_img("cover page.png")
    story_b64    = get_image_as_base64_str(JOURNEY_IMAGE_URL, max_size=(600, 600)) or \
                   load_img("image-journey.png", specific=STORY_IMG_1_PATH, resize=True, max_size=(600, 600))
    watermark_b64= load_img("watermark.png")

    # ── Global PDF CSS ────────────────────────────────────────────────────
    html_parts = [f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@page{{size:A4;margin:0;}}
*{{box-sizing:border-box;}}
html,body{{margin:0!important;padding:0!important;width:100%!important;
           background:#0a0a0f!important;color:#e8e8f0;}}
#wm{{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;
     background-image:url('data:image/png;base64,{watermark_b64}');
     background-repeat:repeat;background-size:cover;opacity:0.04;}}
.cover-page{{width:210mm;height:260mm;display:block;position:relative;
             margin:0;padding:0;overflow:hidden;page-break-after:always;}}
.cover-page img{{width:100%;height:100%;object-fit:cover;}}
.cat-content{{padding:8mm 10mm 50px;position:relative;z-index:1;}}
.cat-heading{{background:linear-gradient(135deg,#141420,#1a1a2e);
              color:#c9a84c;font-size:16pt;padding:10px 18px;
              margin-bottom:4px;font-weight:bold;font-family:sans-serif;
              border-left:5px solid #c9a84c;page-break-inside:avoid;clear:both;}}
.category-heading{{color:#e8e8f0;font-size:13pt;padding:8px 0 4px;
                   border-bottom:1px solid rgba(201,168,76,0.4);
                   margin-top:6mm;clear:both;font-family:serif;
                   page-break-inside:avoid;width:100%;}}
.subcat-hdr{{color:#4a9eff;font-size:10pt;font-weight:bold;margin:10px 0 4px;
             clear:both;font-family:sans-serif;border-left:2px solid #4a9eff;
             padding-left:8px;page-break-inside:avoid;width:100%;}}
.cs-table{{width:100%;border-collapse:collapse;font-size:8.5pt;
           margin-bottom:10px;clear:both;background:rgba(20,20,35,0.9);}}
.cs-table th{{border:1px solid rgba(201,168,76,0.3);background:rgba(201,168,76,0.12);
              padding:4px;text-align:center;font-weight:bold;color:#c9a84c;}}
.cs-table td{{border:1px solid rgba(255,255,255,0.08);padding:4px;
              text-align:center;color:#a0a0c0;}}
.cat-block{{display:block;font-size:0;clear:both;page-break-inside:auto;
            margin-bottom:18px;width:100%;page-break-before:always;}}
h1.cat-heading + .cat-block{{page-break-before:avoid!important;}}
.prod-card{{display:inline-block;width:23%;margin:8px 1%;vertical-align:top;
            font-size:12pt;padding:0;background:#141420;
            border:1px solid rgba(201,168,76,0.25);border-radius:6px;
            text-align:center;position:relative;overflow:hidden;
            height:178px;page-break-inside:avoid;}}
.card-img{{width:100%;height:112px;position:relative;
           background-color:#0f0f18;border-bottom:1px solid rgba(201,168,76,0.15);
           overflow:hidden;}}
.card-img img{{position:absolute;top:0;bottom:0;left:0;right:0;margin:auto;
               max-width:95%;max-height:95%;width:auto;height:auto;display:block;}}
.card-info{{height:62px;display:block;padding:5px;}}
.card-name{{font-family:serif;color:#e8e8f0;line-height:1.2;
            font-weight:bold;margin:0;padding-top:4px;display:block;}}
.new-badge{{position:absolute;top:0;right:0;background:#e74c3c;color:white;
            font-size:7px;font-weight:bold;padding:2px 7px;
            border-radius:0 0 0 5px;z-index:10;letter-spacing:0.5px;}}
.clearfix::after{{content:"";clear:both;display:table;}}
</style></head><body style="margin:0;padding:0;">
<div id="wm"></div>
<div class="cover-page">
  <img src="data:image/png;base64,{cover_b64}" alt="Cover" />
</div>
"""]

    # Story page
    html_parts.append(generate_story_html(story_b64))
    # Table of Contents
    html_parts.append(generate_table_of_contents_html(df_sorted))
    # Open catalogue content wrapper
    html_parts.append('<div class="cat-content clearfix">')

    def fuzzy_get(row_data, keys):
        """Fuzzy-match a value from row_data by partial key name."""
        for k in keys:
            for dk in row_data:
                if k.lower() in dk.lower():
                    return str(row_data[dk])
        return "-"

    cur_catalogue = cur_category = cur_subcategory = None
    is_first = True
    cat_open = False

    for index, row in df_sorted.iterrows():
        # ── New catalogue section ─────────────────────────────────────────
        if row["Catalogue"] != cur_catalogue:
            if cat_open:
                html_parts.append("</div>")
                cat_open = False
            cur_catalogue = row["Catalogue"]
            cur_category = cur_subcategory = None
            pb = 'style="page-break-before:always;"' if not is_first else ""
            html_parts.append(
                f'<div style="clear:both;"></div>'
                f'<h1 class="cat-heading" {pb}>{cur_catalogue}</h1>'
            )
            is_first = False

        # ── New category section ──────────────────────────────────────────
        if row["Category"] != cur_category:
            if cat_open:
                html_parts.append("</div>")
            cur_category = row["Category"]
            cur_subcategory = None
            safe_id = create_safe_id(cur_category)
            row_data = case_selection_map.get(cur_category, {})

            html_parts.append('<div class="cat-block clearfix">')
            cat_open = True

            html_parts.append(
                f'<h2 class="category-heading" id="category-{safe_id}">'
                f'<a href="#main-index" style="float:right;font-size:9px;color:#c9a84c;'
                f'text-decoration:none;font-weight:normal;font-family:sans-serif;'
                f'margin-top:4px;">INDEX ↑</a>{cur_category}</h2>'
            )

            # Case size table
            if row_data:
                desc = row_data.get("Description", "")
                if desc:
                    html_parts.append(
                        f'<p style="color:#a0a0c0;font-size:9.5pt;font-style:italic;margin:4px 0;">'
                        f'<strong style="color:#c9a84c;">Case Size:</strong> {desc}</p>'
                    )
                packing = fuzzy_get(row_data, ["Packing", "Master Ctn"])
                gross   = fuzzy_get(row_data, ["Gross Wt", "Gross Weight"])
                net     = fuzzy_get(row_data, ["Net Wt", "Net Weight"])
                length  = fuzzy_get(row_data, ["Length"])
                breadth = fuzzy_get(row_data, ["Breadth", "Width"])
                height  = fuzzy_get(row_data, ["Height"])
                cbm     = fuzzy_get(row_data, ["CBM"])
                html_parts.append(
                    f'<table class="cs-table"><tr>'
                    f'<th>Packing/Ctn</th><th>Gross Wt (Kg)</th><th>Net Wt (Kg)</th>'
                    f'<th>L (Cm)</th><th>B (Cm)</th><th>H (Cm)</th><th>CBM</th></tr>'
                    f'<tr><td>{packing}</td><td>{gross}</td><td>{net}</td>'
                    f'<td>{length}</td><td>{breadth}</td><td>{height}</td><td>{cbm}</td></tr>'
                    f'</table>'
                )

        # ── Subcategory header ────────────────────────────────────────────
        sub = str(row.get("Subcategory", "")).strip()
        if sub and sub.upper() != "N/A" and sub.lower() != "nan":
            if sub != cur_subcategory:
                cur_subcategory = sub
                html_parts.append(f'<div class="subcat-hdr">{sub}</div>')

        # ── Product card ──────────────────────────────────────────────────
        img_b64 = row.get("ImageB64", "")
        if str(img_b64).startswith("http"):
            img_b64 = get_image_as_base64_str(img_b64)
        mime = "image/png" if img_b64 and "png" in str(img_b64)[:30].lower() else "image/jpeg"
        img_html = (
            f'<img src="data:{mime};base64,{img_b64}" alt="img" />'
            if img_b64
            else '<div style="padding-top:35px;color:#3a3a5a;font-size:9px;">NO IMAGE</div>'
        )
        new_badge = (
            '<div class="new-badge">NEW</div>' if row.get("IsNew") == 1 else ""
        )
        name = str(row.get("ItemName", "N/A"))
        fs = "9pt" if len(name) < 30 else ("8pt" if len(name) < 50 else "7pt")

        html_parts.append(f"""
        <div class="prod-card">
          {new_badge}
          <div class="card-img">{img_html}</div>
          <div class="card-info">
            <div class="card-name" style="font-size:{fs};">
              <span style="color:#c9a84c;margin-right:2px;">{index+1}.</span>{name}
            </div>
          </div>
        </div>""")

    if cat_open:
        html_parts.append("</div>")
    html_parts.append('<div style="clear:both;"></div></div></body></html>')
    return "".join(html_parts)


# ═════════════════════════════════════════════════════════════════════════
# EXCEL ORDER SHEET
# ═════════════════════════════════════════════════════════════════════════
def generate_excel_file(df_sorted: pd.DataFrame, customer_name: str,
                        case_selection_map: dict) -> bytes:
    """Generate a formatted Excel order sheet with CBM calculator."""
    output = io.BytesIO()
    rows = []
    for idx, row in df_sorted.iterrows():
        cat = row["Category"]
        suffix, cbm = "", 0.0
        if cat in case_selection_map:
            cd = case_selection_map[cat]
            for k, v in cd.items():
                if "suffix" in k.lower():
                    suffix = str(v).strip()
                if "cbm" in k.lower():
                    try:
                        cbm = round(float(v), 3)
                    except Exception:
                        cbm = 0.0
            if suffix == "nan":
                suffix = ""
        full_name = str(row["ItemName"]).strip()
        if suffix:
            full_name = f"{full_name} {suffix}"
        rows.append({
            "Ref No":                        idx + 1,
            "Category":                      cat,
            "Product Name + Carton Name":    full_name,
            "Carton CBM":                    cbm,
            "Order Qty (Cartons)":           0,
            "Total CBM":                     0,
        })

    df_xl = pd.DataFrame(rows)
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_xl.to_excel(writer, index=False, sheet_name="Order Sheet", startrow=7)
        wb  = writer.book
        ws  = writer.sheets["Order Sheet"]

        # Formats
        hdr_fmt   = wb.add_format({"bold": True, "bg_color": "#1a1a2e",
                                    "font_color": "#c9a84c", "border": 1})
        input_fmt = wb.add_format({"bg_color": "#FFFCB7", "border": 1, "locked": False})
        lock_fmt  = wb.add_format({"border": 1, "locked": True, "num_format": "0.000"})
        cnt_fmt   = wb.add_format({"num_format": "0.00", "bold": True, "border": 1})
        title_fmt = wb.add_format({"bold": True, "font_size": 14,
                                    "font_color": "#c9a84c"})

        ws.protect()
        ws.freeze_panes(8, 0)

        ws.write("B1", f"Order Sheet — {customer_name}", title_fmt)
        ws.write("B2", "Total CBM:")
        ws.write_formula("C2", f"=SUM(F9:F{len(df_xl)+9})",
                         wb.add_format({"num_format": "0.000"}))
        for r, lbl in [(3, "20 FT (30 CBM)"), (4, "40 FT (60 CBM)"), (5, "40 FT HC (70 CBM)")]:
            ws.write(r-1, 1, "CONTAINER TYPE",
                     wb.add_format({"bold": True, "bg_color": "#1a1a2e",
                                     "font_color": "#c9a84c", "border": 1})) if r == 3 else None
            ws.write(r-1, 1, lbl, wb.add_format({"border": 1})) if r > 3 else None
        ws.write("B3", "CONTAINER TYPE", hdr_fmt)
        ws.write("C3", "ESTIMATED CONTAINERS", hdr_fmt)
        ws.write("B4", "20 FT  (30 CBM)",  wb.add_format({"border": 1}))
        ws.write("B5", "40 FT  (60 CBM)",  wb.add_format({"border": 1}))
        ws.write("B6", "40 FT HC (70 CBM)", wb.add_format({"border": 1}))
        ws.write_formula("C4", "=$C$2/30", cnt_fmt)
        ws.write_formula("C5", "=$C$2/60", cnt_fmt)
        ws.write_formula("C6", "=$C$2/70", cnt_fmt)

        for ci, col in enumerate(df_xl.columns):
            ws.write(7, ci, col, hdr_fmt)

        ws.set_column("A:A", 8)
        ws.set_column("B:B", 25)
        ws.set_column("C:C", 52)
        ws.set_column("D:F", 16)

        for i in range(len(df_xl)):
            ri = i + 9
            ws.write(ri - 1, 4, 0, input_fmt)
            ws.write_formula(ri - 1, 5, f"=D{ri}*E{ri}", lock_fmt)

    return output.getvalue()


# ═════════════════════════════════════════════════════════════════════════
# RENDER PDF — engine selection
# ═════════════════════════════════════════════════════════════════════════
def render_pdf(html_string: str):
    """
    Convert HTML → PDF bytes.

    Returns (pdf_bytes, engine_name) on success
         or (None, error_message) on failure.
    """
    try:
        if PDFKIT_CONFIG:
            # ── wkhtmltopdf (local Windows) ──────────────────────────────
            options = {
                "page-size":               "A4",
                "margin-top":              "0mm",
                "margin-right":            "0mm",
                "margin-bottom":           "0mm",
                "margin-left":             "0mm",
                "encoding":                "UTF-8",
                "no-outline":              None,
                "enable-local-file-access": None,
                "disable-smart-shrinking": None,
                "print-media-type":        None,
            }
            pdf = pdfkit.from_string(
                html_string, False,
                configuration=PDFKIT_CONFIG,
                options=options,
            )
            gc.collect()
            return pdf, "wkhtmltopdf"

        elif HAS_WEASYPRINT:
            # ── WeasyPrint (Streamlit Cloud / Linux) ─────────────────────
            pdf = WP_HTML(string=html_string, base_url=BASE_DIR).write_pdf()
            gc.collect()
            return pdf, "WeasyPrint"

        else:
            return None, (
                "No PDF engine found!\n"
                "• On Streamlit Cloud: add 'weasyprint' to requirements.txt and redeploy.\n"
                "• Locally on Windows: install wkhtmltopdf from https://wkhtmltopdf.org"
            )

    except Exception as exc:
        logger.error(f"PDF render error: {exc}")
        return None, str(exc)
