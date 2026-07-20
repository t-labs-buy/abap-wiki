# Extractor tests

Content-level tests for the document extractors in `../abap-ingest.py`.

```bash
pip install anthropic pdfplumber python-pptx python-docx openpyxl xlrd \
            "markitdown[pptx,docx,xlsx,xls,pdf]" pytesseract pdf2image reportlab xlwt
# system: pandoc, tesseract-ocr, poppler-utils

python make_fixtures.py    # writes fixtures/
python ab_test.py          # our extractors vs markitdown, per format
python fallback_test.py    # degradation: exits non-zero on regression
```

`make_fixtures.py` builds documents engineered to break naive extractors: empty
table cells, horizontally merged cells, interleaved heading/table/paragraph
order, PPTX speaker notes and grouped shapes, XLSX formulas with no cached
value, a legacy `.xls`, and an image-only PDF with no text layer.

`ab_test.py` is a comparison report, not a pass/fail gate — some markitdown
rows are expected to fail, which is the evidence for what we did and didn't
adopt. `fallback_test.py` is the gate: it simulates each missing binary and
module and asserts every extractor either falls back with content intact or
returns `None` cleanly, so a missing dependency never breaks the pipeline.

Two `ab_test.py` rows fail by design in a local run without LibreOffice:
`current-libreoffice-fallback` (correctly returns nothing when `soffice` is
absent) and the markitdown rows noted above.
