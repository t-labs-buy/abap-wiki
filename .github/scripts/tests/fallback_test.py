#!/usr/bin/env python3
"""Degradation tests: a missing binary or module must never break the pipeline.

Simulates each dependency being absent and asserts the extractor either falls
back to a working path (with correct content) or returns None cleanly.
"""
import builtins
import importlib.util
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")

os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-for-import")
spec = importlib.util.spec_from_file_location(
    "abap_ingest",
    os.path.join(os.path.dirname(HERE), "abap-ingest.py"),
)
ing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ing)

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail and not cond else ''}")


class no_modules:
    """Make the named top-level modules raise ImportError."""
    def __init__(self, *names):
        self.names = set(names)

    def __enter__(self):
        self.real_import = builtins.__import__
        self.saved = {k: v for k, v in sys.modules.items()
                      if k in self.names or k.split(".")[0] in self.names}
        for k in list(sys.modules):
            if k in self.names or k.split(".")[0] in self.names:
                del sys.modules[k]

        def fake(name, *a, **kw):
            if name in self.names or name.split(".")[0] in self.names:
                raise ImportError(f"simulated missing module: {name}")
            return self.real_import(name, *a, **kw)

        builtins.__import__ = fake
        return self

    def __exit__(self, *exc):
        builtins.__import__ = self.real_import
        sys.modules.update(self.saved)


class no_binaries:
    """Make shutil.which return None for the named binaries."""
    def __init__(self, *names):
        self.names = set(names)

    def __enter__(self):
        self.real_which = shutil.which
        ing_which = ing.shutil.which

        def fake(cmd, *a, **kw):
            return None if cmd in self.names else self.real_which(cmd, *a, **kw)

        shutil.which = fake
        ing.shutil.which = fake
        return self

    def __exit__(self, *exc):
        shutil.which = self.real_which
        ing.shutil.which = self.real_which


print("\n=== DOCX: pandoc binary missing -> python-docx fallback ===")
with no_binaries("pandoc"):
    t = ing.extract_docx(os.path.join(FIX, "hard.docx"), "hard.docx") or ""
check("falls back and returns content", len(t) > 50)
check("heading survived fallback", "BP Address Validation" in t)
check("doc order survived fallback",
      t.find("INTRO-BEFORE-TABLE") < t.find("NONE_DEFAULT") < t.find("OUTRO-AFTER-TABLE"))
check("empty cell placeholder kept", "Street |  | NONE_DEFAULT" in t)
check("merged cell emitted once", t.count("MERGED-SPAN-NOTE") == 1)

print("\n=== DOCX: pandoc AND python-docx both missing -> clean None ===")
with no_binaries("pandoc"), no_modules("docx"):
    t = ing.extract_docx(os.path.join(FIX, "hard.docx"), "hard.docx")
check("returns None, no exception", t is None)

print("\n=== PPTX: markitdown missing -> python-pptx fallback ===")
with no_modules("markitdown"):
    t = ing.extract_pptx(os.path.join(FIX, "hard.pptx"), "hard.pptx") or ""
check("falls back and returns content", len(t) > 50)
check("speaker notes survived", "SPEAKER-NOTE-ALPHA" in t and "SPEAKER-NOTE-BETA" in t)
check("grouped shapes survived", "GROUP-CHILD-ONE" in t and "GROUP-CHILD-TWO" in t)
check("empty cell placeholder kept", "ZSD_ORDER_CHECK |  | ANNA_OWNER" in t)
check("merged cell emitted once", t.count("MERGED-FOOTER-ROW") == 1)

print("\n=== PPTX: markitdown AND python-pptx both missing -> clean None ===")
with no_modules("markitdown", "pptx"):
    t = ing.extract_pptx(os.path.join(FIX, "hard.pptx"), "hard.pptx")
check("returns None, no exception", t is None)

print("\n=== XLS: xlrd missing, no soffice -> clean None ===")
with no_modules("xlrd"), no_binaries("soffice", "libreoffice"):
    t = ing.extract_xls(os.path.join(FIX, "legacy.xls"), "legacy.xls")
check("returns None, no exception", t is None)

print("\n=== XLSX: openpyxl missing -> clean None ===")
with no_modules("openpyxl"):
    t = ing.extract_xlsx(os.path.join(FIX, "hard.xlsx"), "hard.xlsx")
check("returns None, no exception", t is None)

print("\n=== PDF: pdfplumber missing -> clean None ===")
with no_modules("pdfplumber"):
    t = ing.extract_pdf(os.path.join(FIX, "hard.pdf"), "hard.pdf")
check("returns None, no exception", t is None)

print("\n=== Scanned PDF: OCR deps missing -> clean None (not a crash) ===")
with no_modules("pytesseract", "pdf2image"):
    t = ing.extract_pdf(os.path.join(FIX, "scanned.pdf"), "scanned.pdf")
check("returns None, no exception", t is None)

print("\n=== Scanned PDF: OCR deps present -> OCR path runs ===")
t = ing.extract_pdf(os.path.join(FIX, "scanned.pdf"), "scanned.pdf") or ""
check("OCR recovered marker", "SCANNED-OCR-MARKER" in t)
check("OCR page label present", "(OCR)" in t)

print("\n=== Routing: read_inbox_file dispatches by extension ===")
check(".xls routes to extract_xls", ing.BINARY_EXTRACTORS.get("xls") == "extract_xls")
check(".doc/.ppt still legacy-converted", ing.LEGACY_OFFICE_TYPES == {"doc", "ppt"})
check("all extractor names resolve",
      all(name in dir(ing) for name in ing.BINARY_EXTRACTORS.values()))

print("\n=== Legacy .doc/.ppt with no soffice -> clean None ===")
with no_binaries("soffice", "libreoffice"):
    t = ing.extract_legacy_office(os.path.join(FIX, "hard.docx"), "x.doc", "doc")
check("returns None, no exception", t is None)

failed = [n for n, ok in RESULTS if not ok]
print(f"\n{'=' * 55}\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
if failed:
    print("FAILED: " + "; ".join(failed))
sys.exit(1 if failed else 0)
