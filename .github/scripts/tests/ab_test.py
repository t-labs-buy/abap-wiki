#!/usr/bin/env python3
"""A/B: current abap-ingest extractors vs markitdown, per format, on hard cases.

Content-level checks, not just "did it return text". Each check is a
(name, fn(text) -> bool). Outputs land in ./ab-out/ for eyeballing.
"""
import os
import re
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
OUT = os.path.join(HERE, "ab-out")
os.makedirs(OUT, exist_ok=True)

os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-for-import")
spec = importlib.util.spec_from_file_location(
    "abap_ingest",
    os.path.join(os.path.dirname(HERE), "abap-ingest.py"),
)
ing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ing)

from markitdown import MarkItDown
MID = MarkItDown()


def md_convert(path):
    try:
        return MID.convert(path).text_content
    except Exception as e:
        return f"<<markitdown ERROR: {e}>>"


def normalize(text):
    """Undo cosmetic markdown escaping and rewrite HTML table rows as
    pipe rows so one set of checks covers both output styles."""
    text = re.sub(r"\\([_\-*#|.\[\]])", r"\1", text or "")

    def table_to_pipes(m):
        rows = []
        for tr in re.findall(r"<tr>([\s\S]*?)</tr>", m.group(0)):
            cells = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", tr)
            rows.append("| " + " | ".join(c.strip() for c in cells) + " |")
        return "\n".join(rows)

    return re.sub(r"<table>[\s\S]*?</table>", table_to_pipes, text)


def order(text, *needles):
    pos = -1
    for n in needles:
        p = text.find(n)
        if p < 0 or p < pos:
            return False
        pos = p
    return True


def once(text, needle):
    return text.count(needle) == 1


def row_has_empty_between(text, left, right):
    """left and right on one table row with an empty cell between them."""
    for line in text.splitlines():
        if left in line and right in line:
            seg = line[line.index(left) + len(left):line.index(right)]
            cells = [c.strip() for c in seg.split("|")]
            if len(cells) >= 3 and any(c == "" for c in cells[1:-1]):
                return True
    return False


CHECKS = {
    "docx": [
        ("heading present",        lambda t: "BP Address Validation" in t),
        ("doc order kept",         lambda t: order(t, "INTRO-BEFORE-TABLE", "NONE_DEFAULT", "OUTRO-AFTER-TABLE", "TAIL-PARA")),
        ("empty cell aligned",     lambda t: row_has_empty_between(t, "Street", "NONE_DEFAULT")),
        ("merged cell not tripled", lambda t: once(t, "MERGED-SPAN-NOTE")),
        ("normal row intact",      lambda t: "City" in t and "BERLIN_DEFAULT" in t),
    ],
    "pptx": [
        ("title present",          lambda t: "SLIDE-ONE-TITLE" in t),
        ("speaker notes slide 1",  lambda t: "SPEAKER-NOTE-ALPHA" in t),
        ("speaker notes slide 2",  lambda t: "SPEAKER-NOTE-BETA" in t),
        ("grouped shapes",         lambda t: "GROUP-CHILD-ONE" in t and "GROUP-CHILD-TWO" in t),
        ("slide order",            lambda t: order(t, "SLIDE-ONE-TITLE", "GROUP-CHILD-ONE")),
        ("empty cell aligned",     lambda t: row_has_empty_between(t, "ZSD_ORDER_CHECK", "ANNA_OWNER")),
        ("merged cell not tripled", lambda t: once(t, "MERGED-FOOTER-ROW")),
    ],
    "xlsx": [
        ("uncached formula kept",  lambda t: "=C2-B2" in t and "=SUM(B2:B3)" in t),
        ("empty cell aligned",     lambda t: row_has_empty_between(t, "ZMM_GR_BADI", "3")),
        ("merged note present",    lambda t: "MERGED-XLSX-NOTE" in t),
        ("second sheet present",   lambda t: "SECOND-SHEET-MARKER" in t),
        ("sheet names kept",       lambda t: "Estimates" in t and "Assumptions" in t),
        ("total row kept",         lambda t: "TOTAL_ROW" in t),
    ],
    "xls": [
        ("header present",         lambda t: "LEGACY-XLS-HEADER" in t),
        ("data row present",       lambda t: "ZFI_OLD_REPORT" in t),
        ("tail cell present",      lambda t: "LEGACY-TAIL-CELL" in t),
    ],
    "pdf": [
        ("heading present",        lambda t: "PDF-BEFORE-TABLE" in t),
        ("doc order kept",         lambda t: order(t, "PDF-BEFORE-TABLE", "PDF_NONE_DEFAULT", "PDF-AFTER-TABLE")),
        ("empty cell aligned",     lambda t: row_has_empty_between(t, "Street", "PDF_NONE_DEFAULT")),
        ("table rows present",     lambda t: "PDF_BERLIN" in t),
    ],
    "scanned-pdf": [
        ("OCR marker found",       lambda t: "SCANNED-OCR-MARKER" in t),
        ("step content found",     lambda t: "STMS" in t and "release task" in t),
    ],
}


def run(fmt, variant, text):
    with open(os.path.join(OUT, f"{fmt}--{variant}.txt"), "w") as f:
        f.write(text or "")
    text = normalize(text)
    results = []
    for name, fn in CHECKS[fmt]:
        try:
            ok = bool(fn(text))
        except Exception:
            ok = False
        results.append((name, ok))
    passed = sum(1 for _, ok in results if ok)
    print(f"\n  [{variant}] {passed}/{len(results)}")
    for name, ok in results:
        print(f"    {'PASS' if ok else 'FAIL'}  {name}")
    return passed


def main():
    which = sys.argv[1:] or ["docx", "pptx", "xlsx", "xls", "pdf", "scanned-pdf"]

    if "docx" in which:
        p = os.path.join(FIX, "hard.docx")
        print("\n=== DOCX ===")
        run("docx", "current-pandoc", ing.extract_docx_pandoc(p))
        run("docx", "current-pythondocx-fallback", _docx_fallback(p))
        run("docx", "markitdown-mammoth", md_convert(p))

    if "pptx" in which:
        p = os.path.join(FIX, "hard.pptx")
        print("\n=== PPTX ===")
        run("pptx", "current-markitdown-primary", ing.extract_pptx_markitdown(p) or "")
        run("pptx", "current-pythonpptx-fallback", _pptx_fallback(p))

    if "xlsx" in which:
        p = os.path.join(FIX, "hard.xlsx")
        print("\n=== XLSX ===")
        run("xlsx", "current-openpyxl", ing.extract_xlsx(p, "hard.xlsx") or "")
        run("xlsx", "markitdown-pandas", md_convert(p))

    if "xls" in which:
        p = os.path.join(FIX, "legacy.xls")
        print("\n=== XLS (legacy) ===")
        run("xls", "current-xlrd-native", ing.extract_xls(p, "legacy.xls") or "")
        run("xls", "current-libreoffice-fallback", ing.extract_legacy_office(p, "legacy.xls", "xls") or "<<soffice unavailable>>")
        run("xls", "markitdown-xlrd", md_convert(p))

    if "pdf" in which:
        p = os.path.join(FIX, "hard.pdf")
        print("\n=== PDF (text layer) ===")
        run("pdf", "current-pdfplumber", ing.extract_pdf(p, "hard.pdf") or "")
        run("pdf", "markitdown", md_convert(p))

    if "scanned-pdf" in which:
        p = os.path.join(FIX, "scanned.pdf")
        print("\n=== PDF (scanned, no text layer) ===")
        run("scanned-pdf", "current-ocr", ing.extract_pdf(p, "scanned.pdf") or "")
        run("scanned-pdf", "markitdown", md_convert(p))


def _docx_fallback(path):
    """extract_docx with the pandoc branch disabled -> python-docx path."""
    orig = ing.extract_docx_pandoc
    ing.extract_docx_pandoc = lambda p: None
    try:
        return ing.extract_docx(path, os.path.basename(path)) or ""
    finally:
        ing.extract_docx_pandoc = orig


def _pptx_fallback(path):
    orig = ing.extract_pptx_markitdown
    ing.extract_pptx_markitdown = lambda p: None
    try:
        return ing.extract_pptx(path, os.path.basename(path)) or ""
    finally:
        ing.extract_pptx_markitdown = orig


if __name__ == "__main__":
    main()
