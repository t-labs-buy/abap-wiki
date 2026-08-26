# Tests

## Prompt suggester

`prompt_suggest_test.py` gates `../prompt-suggest.py`, the starter prompts the
`abap-wiki` skill offers when nobody has asked anything yet. No dependencies —
it builds a synthetic vault in a temp directory and runs the script against it:

```bash
python3 prompt_suggest_test.py    # exits non-zero on regression
```

It asserts the promise the skill makes to a reader — every question offered is
answered by a page that exists — plus the filters that keep that promise
honest: archived pages excluded, near-empty pages dropped, draft and
`ai-generated` pages flagged rather than presented as settled, role tags kept
out of cross-workstream questions, `--near`/`--about`/`--workstream` filtering
to what they claim, and byte-identical output on identical input. It runs in
the Vault Graph Health workflow.

## Community summaries

`community_test.py` gates `../vault_communities.py` and
`../community-summarize.py`, which build `meta/communities.md` — the cluster map
the `abap-wiki` skill reads to answer questions about the vault as a whole.

```bash
python3 community_test.py    # exits non-zero on regression
```

Four properties are load-bearing and each is asserted here. Community
signatures must be stable, or every ingest re-summarises the whole vault
instead of just what changed. The generated file must contain no
`[[wikilinks]]` and must not alter what graph-health sees, since a generated
meta file that mints edges makes the checker demand backlinks for pages nobody
wrote. Every page name printed must exist — the same promise
`prompt_suggest_test.py` enforces for suggested prompts. And with no API key or
no `anthropic` package the script must still exit 0 with usable scaffolding.

It also covers the cache: an unchanged vault reuses every summary, an edited
page invalidates its own community and no other, `--dry-run` writes nothing and
`--force` ignores the cache. No dependencies and no API calls — it builds a
synthetic vault in a temp directory and stands in for the model.

## Extractor tests

Content-level tests for the document extractors in `../abap-ingest.py`.

```bash
pip install anthropic pdfplumber python-pptx python-docx openpyxl xlrd \
            "markitdown[pptx,docx,xlsx,xls,pdf]" pytesseract pdf2image reportlab xlwt
# system: pandoc, tesseract-ocr, poppler-utils

python make_fixtures.py     # writes fixtures/
python ab_test.py           # our extractors vs markitdown, per format
python fallback_test.py     # degradation gate: exits non-zero on regression
python robustness_test.py   # hardening gate: exits non-zero on regression
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

`robustness_test.py` is the second gate. It covers the hardening fixes: binary
formats are refused rather than decoded to mojibake and sent to the API,
BOM-declared UTF-16/32 decodes to real text, `meta/inbox.md` and `meta/log.md`
are not model-writable, and permanently unprocessable files are recorded so
they stop retrying every run while transient failures stay retryable.

Two `ab_test.py` rows fail by design in a local run without LibreOffice:
`current-libreoffice-fallback` (correctly returns nothing when `soffice` is
absent) and the markitdown rows noted above.
