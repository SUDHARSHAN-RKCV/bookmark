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
    Normalize link dicts and add safe defaults.
    Ensures keys exist: 'category', 'URL', 'href', 'target', 'Icon', 'Link Title', 'Type'
    """
    for link in links:
        # normalize category (handle both 'Category' and 'category' from Excel)
        link['category'] = (link.get('category') or link.get('Category') or '').strip()

        # normalize URL key (many sheets use 'URL' but some might use 'url')
        url_val = link.get('URL') or link.get('url') or ''
        url = str(url_val).strip()

        # defaults for display title / icon / type
        link['Link Title'] = link.get('Link Title') or link.get('Team / Title') or link.get('title') or ''
        link['Icon'] = link.get('Icon') or 'fa-link'
        link['Type'] = link.get('Type') or ''

        # compute href + target
        if url.lower().startswith('http://') or url.lower().startswith('https://'):
            link['target'] = '_blank'
            link['href'] = url
        elif url:  # internal route expected (e.g., roc or scipher)
            link['target'] = '_self'
            # If the URL already looks like a team route (starts with /team/), preserve it
            if url.startswith('/'):
                link['href'] = url
            else:
                # treat as team name / internal page — we keep current behavior:
                try:
                    link['href'] = url_for('team_page', team_name=url.strip('/'))
                except Exception:
                    # if url_for fails outside request context, fallback
                    link['href'] = f"/{url.strip('/')}"
        else:
            link['target'] = '_self'
            link['href'] = '#'

    return links