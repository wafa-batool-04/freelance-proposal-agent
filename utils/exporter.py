from __future__ import annotations

import io


def export_proposal(text: str, fmt: str = "docx") -> bytes | None:
    if fmt == "docx":
        return _to_docx(text)
    return None


def _to_docx(text: str) -> bytes | None:
    try:
        from docx import Document
        from docx.shared import Pt, Inches

        doc = Document()
        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)

        section = doc.sections[0]
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.25)

        for para in text.strip().split("\n"):
            doc.add_paragraph(para)

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None
