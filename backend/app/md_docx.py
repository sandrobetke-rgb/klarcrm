"""Einfacher Markdown → Word-Konverter für Lastenheft und Benutzerbeschreibung (Download im Programm).

Unterstützt: Überschriften #–####, Absätze, Aufzählungen (-, *, 1.), Tabellen (| … |), **fett**, `Code`, Zitate (>),
horizontale Linien. Seitenformat A4, Arial, Kopf- und Fußzeile.
"""
import re

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)")


def _runs(par, text: str, bold: bool = False, size: float | None = None):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Links → Text
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(9)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); r.italic = True
        else:
            r = par.add_run(part)
        if bold:
            r.bold = True
        if size:
            r.font.size = Pt(size)


def _shade(cell, hex_fill: str):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill)
    tcpr.append(shd)


def _rule(doc):
    p = doc.add_paragraph()
    ppr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "6"); b.set(qn("w:space"), "1"); b.set(qn("w:color"), "999999")
    bdr.append(b); ppr.append(bdr)


def _table(doc, rows: list[list[str]]):
    header = True
    if all(not c.strip() for c in rows[0]):  # Tabelle ohne Kopfzeile (z. B. Deckblatt-Angaben)
        rows, header = rows[1:], False
    ncol = max(len(r) for r in rows)
    t = doc.add_table(rows=len(rows), cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, row in enumerate(rows):
        for j in range(ncol):
            cell = t.cell(i, j)
            cell.paragraphs[0].text = ""
            _runs(cell.paragraphs[0], (row[j] if j < len(row) else "").strip(), bold=(i == 0 and header), size=8.5)
            if (i == 0 and header) or (not header and j == 0):
                _shade(cell, "DCE6F2")
    if header:  # Kopfzeile auf jeder Seite wiederholen
        trpr = t.rows[0]._tr.get_or_add_trPr()
        h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trpr.append(h)
    doc.add_paragraph()


def markdown_to_docx(md: str, title: str) -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(1.8)
    st = doc.styles["Normal"]
    st.font.name = "Arial"; st.font.size = Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    for name, size in (("Title", 22), ("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11), ("Heading 4", 10)):
        hs = doc.styles[name]
        hs.font.name = "Arial"; hs.font.size = Pt(size); hs.font.bold = True
        hs.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        rf = hs.element.get_or_add_rPr().get_or_add_rFonts()
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            rf.attrib.pop(qn(a), None)
        rf.set(qn("w:ascii"), "Arial"); rf.set(qn("w:hAnsi"), "Arial")
        hs.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        hs.paragraph_format.space_after = Pt(6)
        hs.paragraph_format.keep_with_next = True
    hp = sec.header.paragraphs[0]; hp.text = f"KlarCRM · {title}"; hp.runs[0].font.size = Pt(8)
    fp = sec.footer.paragraphs[0]; fp.text = "© SB/Thinkworks"; fp.runs[0].font.size = Pt(8)

    lines = md.splitlines()
    i, first_h1 = 0, True
    para: list[str] = []

    def flush():
        if para:
            p = doc.add_paragraph()
            _runs(p, " ".join(x.strip() for x in para))
            para.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush(); i += 1; continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"\s*:?-{2,}:?\s*", c) for c in cells):
                    rows.append([c.replace("<br>", " / ") for c in cells])
                i += 1
            if rows:
                _table(doc, rows)
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 1 and first_h1:
                doc.add_paragraph(txt, style="Title"); first_h1 = False
            else:
                doc.add_heading(re.sub(r"[*`]", "", txt), level=min(lvl, 4))
            i += 1; continue
        if re.fullmatch(r"-{3,}|\*{3,}", s):
            flush(); _rule(doc); i += 1; continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", ln)
        if m:
            flush()
            depth = min(len(m.group(1)) // 2, 2)
            style = "List Number" if m.group(2)[0].isdigit() else "List Bullet"
            if depth:
                style += f" {depth + 1}"
            txt = m.group(3)
            i += 1
            # Fortsetzungszeilen (eingerückt, kein neuer Listenpunkt) gehören zum Punkt
            while i < len(lines) and lines[i].strip() and lines[i].startswith((" ", "\t")) \
                    and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) and not lines[i].strip().startswith("|"):
                txt += " " + lines[i].strip(); i += 1
            p = doc.add_paragraph(style=style)
            _runs(p, txt)
            continue
        if s.startswith(">"):
            flush()
            txt = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                txt.append(lines[i].strip().lstrip(">").strip()); i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.8)
            _runs(p, " ".join(txt))
            for r in p.runs:
                r.italic = True
            continue
        para.append(s)
        i += 1
    flush()
    return doc
