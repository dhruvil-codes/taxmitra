"""Export utility for generating PDF, TXT, and Markdown response documents."""

from __future__ import annotations

import pymupdf


def generate_pdf_from_text(text: str, title: str = "Income Tax Response") -> bytes:
    """Generate a clean, professional A4 letterhead PDF from response letter text."""
    doc = pymupdf.open()
    left_margin = 54
    top_margin = 54
    bottom_margin = 788  # A4 height 842 - 54
    font_name = "helv"
    font_size = 10
    line_height = 14
    max_chars_per_line = 85

    lines: list[str] = []
    for raw_line in text.split("\n"):
        if not raw_line.strip():
            lines.append("")
            continue
        words = raw_line.split(" ")
        current = ""
        for w in words:
            test = current + (" " if current else "") + w
            if len(test) <= max_chars_per_line:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)

    page = doc.new_page(width=595, height=842)
    y = top_margin
    page_num = 1

    for line in lines:
        if y > bottom_margin:
            # Page footer
            page.insert_text(
                pymupdf.Point(260, 810),
                f"Page {page_num}",
                fontsize=8,
                fontname=font_name,
                color=(0.4, 0.4, 0.4),
            )
            page = doc.new_page(width=595, height=842)
            page_num += 1
            y = top_margin

        if line:
            is_bold = (
                line.startswith("Date:")
                or line.startswith("To")
                or line.startswith("Ref:")
                or line.startswith("PAN:")
                or line.startswith("ASSESSMENT YEAR:")
                or line.startswith("DIN:")
                or line.startswith("Sub:")
                or line.startswith("Subject:")
                or line.startswith("Dear Sir")
                or line.startswith("Respected Sir")
                or line.startswith("Thanking you")
                or line.startswith("Yours faithfully")
                or line.startswith("List of Enclosures")
                or (line[:3].strip().isdigit() and line.strip().endswith("."))
            )
            fn = "hebo" if is_bold else font_name
            page.insert_text(
                pymupdf.Point(left_margin, y),
                line,
                fontsize=font_size,
                fontname=fn,
                color=(0.08, 0.08, 0.08),
            )
        y += line_height

    page.insert_text(
        pymupdf.Point(260, 810),
        f"Page {page_num}",
        fontsize=8,
        fontname=font_name,
        color=(0.4, 0.4, 0.4),
    )
    return doc.tobytes()
