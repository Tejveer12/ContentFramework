import pandas as pd
import json


# --- Helper Functions ---

def parse_key_features(text):
    """Parses bullet points from text into a list of strings."""
    if pd.isna(text):
        return []
    lines = str(text).split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if line.startswith('•'):
            line = line[1:].strip()
        if line:
            cleaned.append(line)
    return cleaned


def create_page_obj(row, name, placement_tag):
    """Creates a standardized dictionary for a page."""
    return {
        "name": name,
        "page_type": row.get('PAGE TYPE', 'Main Page'),
        "placement": [placement_tag],
        "description": row.get('PAGE DESCRIPTION') if pd.notna(row.get('PAGE DESCRIPTION')) else None,
        "key features/sections": parse_key_features(row.get('KEY SECTIONS/FEATURES')),
        "sub_pages": []
    }


def process_header(df):
    """Parses the Header dataframe into a nested tree structure."""
    root_pages = []
    active_parents = {}

    for idx, row in df.iterrows():
        level = 0
        name = ""

        # Determine hierarchy level
        if pd.notna(row.get('MAIN NAV / LAUNCH POINT')):
            level = 1
            name = row['MAIN NAV / LAUNCH POINT']
        elif pd.notna(row.get('TIER 2 MEGA MENU ITEM')):
            level = 2
            name = row['TIER 2 MEGA MENU ITEM']
        elif pd.notna(row.get('TIER 3 MEGA MENU ITEM')):
            level = 3
            name = row['TIER 3 MEGA MENU ITEM']
        elif pd.notna(row.get('FINAL DESTINATION')):
            level = 4
            name = row['FINAL DESTINATION']
        else:
            continue

        page_obj = create_page_obj(row, name, "Header")

        if level == 1:
            root_pages.append(page_obj)
            active_parents[1] = page_obj
            # Reset deeper levels
            for l in range(2, 6):
                active_parents[l] = None
        else:
            parent = active_parents.get(level - 1)
            if parent:
                parent['sub_pages'].append(page_obj)
                active_parents[level] = page_obj
                for l in range(level + 1, 6):
                    active_parents[l] = None
            else:
                root_pages.append(page_obj)
                active_parents[level] = page_obj

    return root_pages


def process_footer(df):
    """Parses the Footer dataframe into a nested tree structure."""
    root_pages = []
    active_parents = {}

    for idx, row in df.iterrows():
        level = 0
        name = ""

        if pd.notna(row.get('FOOTER MENU TITLE')):
            level = 1
            name = row['FOOTER MENU TITLE']
        elif pd.notna(row.get('NESTED MENU ITEMS')):
            level = 2
            name = row['NESTED MENU ITEMS']
        else:
            continue

        page_obj = create_page_obj(row, name, "Footer")

        if level == 1:
            root_pages.append(page_obj)
            active_parents[1] = page_obj
            active_parents[2] = None
        else:
            parent = active_parents.get(1)
            if parent:
                parent['sub_pages'].append(page_obj)
                active_parents[2] = page_obj
            else:
                root_pages.append(page_obj)

    return root_pages


def merge_pages(pages1, pages2):
    """Merges two lists of pages, combining placements if names match."""
    merged_map = {p['name']: p for p in pages1}

    for p2 in pages2:
        name = p2['name']
        if name in merged_map:
            p1 = merged_map[name]
            # Merge placements
            for place in p2['placement']:
                if place not in p1['placement']:
                    p1['placement'].append(place)
            # Recursively merge sub-pages
            p1['sub_pages'] = merge_pages(p1['sub_pages'], p2['sub_pages'])
        else:
            merged_map[name] = p2

    return list(merged_map.values())


def clean_empty_subpages(pages):
    """Recursively removes empty 'sub_pages' keys."""
    for page in pages:
        if not page['sub_pages']:
            del page['sub_pages']
        else:
            clean_empty_subpages(page['sub_pages'])


# --- Main Execution Function ---

def convert_excel_to_json(excel_path, output_json_path):
    print(f"Reading file: {excel_path}...")

    # Read the specific sheets directly from Excel
    # header=2 means the 3rd row is the header (0, 1, 2)
    try:
        df_header = pd.read_excel(excel_path, sheet_name="1️⃣ Header Navigation Content", header=2)
        df_footer = pd.read_excel(excel_path, sheet_name="2️⃣ Footer Navigation Content", header=2)
    except ValueError as e:
        print(f"Error reading sheets. Ensure sheet names match exactly. \nDetails: {e}")
        return

    # Process hierarchies
    header_pages = process_header(df_header)
    footer_pages = process_footer(df_footer)

    # Merge
    final_pages = merge_pages(header_pages, footer_pages)

    # Clean
    clean_empty_subpages(final_pages)

    output_json = {
        "site": "The ToolBox",
        "pages": final_pages
    }

    # Save
    with open(output_json_path, "w", encoding='utf-8') as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)

    print(f"Success! JSON saved to {output_json_path}")


# --- Usage ---

# Simply change this path to your local Excel file path
excel_file_path = 'data/training/Example-1-BICKFORD USA/output/AI Copy Bickford USA_ Content Framework_.xlsx'
convert_excel_to_json(excel_file_path, 'toolbox_structure.json')