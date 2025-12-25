from openpyxl import Workbook
from openpyxl.styles import Font


HEADERS = [
    "MAIN NAV. ITEM / LAUNCH POINT",
    "DROPDOWN / NEXT STOP",
    "FINAL DESTINATION",
    "PAGE TYPE",
    "PAGE DESCRIPTION",
    "KEY SECTIONS / FEATURES",
    "CONTENT TYPE",
    "🌈 CONTENT LINK",
    "🌈 STATUS",
    "🌈 CLIENT NOTES"
]


def add_headers(ws):
    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)


def normalize_sections(page: dict):
    return page.get("key features/sections") or page.get("sections") or []


def format_sections(sections: list[str] | None):
    """
    Render sections as real bullet points (Excel line breaks)
    """
    if not sections:
        return None
    return "\n".join([f"• {s}" for s in sections])


def infer_content_status(description: str | None):
    if description:
        return "", ""
    return "", ""


def add_row(
    ws,
    main,
    dropdown,
    final,
    page_type,
    description,
    sections
):
    content_type, status = infer_content_status(description)

    ws.append([
        main or None,
        dropdown or None,
        final or None,
        page_type,
        description,
        format_sections(sections),
        content_type,
        f"{final} Page Copy" if description and final else None,
        status,
        None
    ])


def process_page(ws, page):
    page_name = page["name"]

    # HOME (special case: MAIN + FINAL)
    if page_name.lower() == "home":
        add_row(
            ws=ws,
            main="Home",
            dropdown=None,
            final=None,
            page_type=page["type"],
            description=page.get("description"),
            sections=normalize_sections(page)
        )
        return

    # LEVEL 1 — MAIN NAV ITEM ONLY
    add_row(
        ws=ws,
        main=page_name,
        dropdown=None,
        final=None,
        page_type=page["type"],
        description=page.get("description"),
        sections=normalize_sections(page)
    )

    # LEVEL 2 — COLLECTIONS (DROPDOWN ONLY)
    for sub in page.get("sub_pages") or []:
        add_row(
            ws=ws,
            main=None,
            dropdown=sub["name"],
            final=None,
            page_type=sub["type"],
            description=sub.get("description"),
            sections=normalize_sections(sub)
        )

        # LEVEL 3 — PRODUCTS (FINAL ONLY)
        for prod in sub.get("sub_sub_pages") or []:
            add_row(
                ws=ws,
                main=None,
                dropdown=None,
                final=prod["name"],
                page_type=prod["type"],
                description=prod.get("description"),
                sections=normalize_sections(prod)
            )


def json_to_excel(sitemap_json: dict, output_path: str):
    wb = Workbook()

    header_ws = wb.active
    header_ws.title = "Header"

    footer_ws = wb.create_sheet("Footer")

    add_headers(header_ws)
    add_headers(footer_ws)

    for page in sitemap_json.get("pages", []):
        placements = page.get("placement", [])

        if "Header" in placements:
            process_page(header_ws, page)

        if "Footer" in placements:
            process_page(footer_ws, page)

    wb.save(output_path)
