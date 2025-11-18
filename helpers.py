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
    """
    Add target and href logic for internal vs external links.
    If the URL starts with http(s):// -> open externally.
    Otherwise, treat it as an internal route.
    """
    for link in links:
        url = link.get('URL', '').strip()

        if url.startswith('http://') or url.startswith('https://'):
            link['target'] = '_blank'   # external link
            link['href'] = url
        elif url:  # internal link
            link['target'] = '_self'
            link['href'] = url_for('team_page', team_name=url.strip('/'))
        else:
            link['target'] = '_self'
            link['href'] = '#'

    return links
