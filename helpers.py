#helpers.py
import os
import pandas as pd
from flask import abort, url_for

# -----------------
# Helper functions
# -----------------
def load_excel(file_path, sheets=None):
    """
    Load links from an Excel workbook.
    - If `sheets` is None: loads all sheets.
    - If `sheets` is a list: loads only those sheets.
    Returns: list of dicts with all link rows.
    """
    if not os.path.exists(file_path):
        abort(404, description=f"File not found: {file_path}")

    # Load workbook once
    xls = pd.ExcelFile(file_path)
    all_links = []

    # Decide which sheets to load
    if sheets is None:
        sheets = xls.sheet_names

    for sheet_name in sheets:
        if sheet_name not in xls.sheet_names:
            print(f"[WARN] Sheet '{sheet_name}' not found in workbook, skipping.")
            continue

        df = pd.read_excel(xls, sheet_name=sheet_name)
        df = df.fillna('')
        
        # ✅ Ensure a Team column exists (fallback to sheet name)
        if 'Team' not in df.columns:
            df['Team'] = sheet_name
        else:
            df['Team'] = df['Team'].replace('', sheet_name)

        all_links.extend(df.to_dict(orient='records'))

    return all_links


def prepare_links(links):
    logo_folder = "static/data/logo"

    for link in links:

        # -------------------------------
        # URL handling
        # -------------------------------
        url = link.get('URL', '').strip()

        if url.startswith('http://') or url.startswith('https://'):
            link['target'] = '_blank'
            link['href'] = url
        elif url:
            link['target'] = '_self'
            link['href'] = url_for('team_page', team_name=url.strip('/'))
        else:
            link['target'] = '_self'
            link['href'] = '#'

        # -------------------------------
        # ICON AUTO-DETECT 
        # -------------------------------
        icon_name = link.get("icon") or link.get("Icon") or ""
        icon_name = icon_name.strip()

        detected_icon_path = "/static/data/logo/default.png"  # fallback

        if icon_name:
            base_path = os.path.join(logo_folder, icon_name)

            # Try all possible extensions
            for ext in ["png", "jpg", "jpeg", "svg", "webp"]:
                full_path = f"{base_path}.{ext}"
                if os.path.isfile(full_path):
                    detected_icon_path = f"/static/data/logo/{icon_name}.{ext}"
                    break

        link["logo"] = detected_icon_path

    return links


