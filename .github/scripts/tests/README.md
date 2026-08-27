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

Five properties are load-bearing and each is asserted here. Community
signatures must be stable, or every ingest re-summarises the whole vault
instead of just what changed. The hierarchy must be a real tree: every
sub-cluster inside its parent, and the children of a cluster partitioning it
exactly. The generated file must contain no `[[wikilinks]]` and must not alter
what graph-health sees, since a generated meta file that mints edges makes the
checker demand backlinks for pages nobody wrote. Every page name printed must
exist — the same promise `prompt_suggest_test.py` enforces for suggested
prompts. And with no API key or no `anthropic` package the script must still
exit 0 with usable scaffolding.

It also covers the cache, including the part that only exists because summaries
are written bottom-up: an unchanged vault reuses everything, an edited page
invalidates its own cluster **and every ancestor** and nothing else,
`--dry-run` writes nothing and `--force` ignores the cache. No dependencies and
no API calls — it builds two synthetic vaults in temp directories (one flat,
one large enough that a cluster actually splits) and stands in for the model.

One test carries a warning worth reading before deleting it: *every community
is internally connected*. That is the guarantee Leiden's refinement phase adds
and plain Louvain does not make. It has always passed, which is the evidence
that writing the refinement phase would buy nothing. If it starts failing on
real content, that calculation has changed.

## Search

`search_test.py` gates `../vault_search.py` and `../vault-search.py`, which
replaced `grep -ril` in the `abap-wiki` skill.

```bash
python3 search_test.py    # exits non-zero on regression
```

Replacing grep means inheriting its promise — if the words are on the page, the
page is found — and adding the one grep never made: the page is found when the
reader's words are not the vault's. Both are asserted, along with ranking (a
page named for the subject outranks one that mentions it once), alias expansion
through `meta/entities.md`, ABAP identifier splitting, the wikilink-neighbour
boost, and the filters.

Two of its assertions are constitutional rather than about quality. **Nothing
under `raw/` or `meta/` may ever be returned** — answering from unprocessed
source material is forbidden, and a search tool that surfaces it invites
exactly that. And **the output must be byte-identical on identical input**, or
a cited answer cannot be reproduced.

The rest is degradation: no vector index, a query of nothing but stopwords, a
query that matches nothing, and an empty vault all exit 0 with something
sensible, because that is the state on a reader's laptop.

## Embedding index

`embed_test.py` gates `../embed-index.py`, which builds the committed vector
index the semantic tier of search reads.

```bash
python3 embed_test.py    # exits non-zero on regression
```

The index is unusual for this repo: a binary blob, produced by a paid API, read
on machines that have neither the key nor any way to tell a good vector from a
bad one. So most of the gate is about what happens when something is wrong.
Absent is a normal state — no key, no network, no index must all exit 0 and
leave lexical search working. A failed provider call must leave the committed
index exactly as it was, because a manifest that disagrees with its blob
returns confidently wrong neighbours. A changed model must rebuild rather than
mix two embedding spaces in one file. Every path in the manifest must be a page
that exists. And it must be incremental: a one-page edit re-embeds one page.

The provider is stubbed throughout with deterministic pseudo-vectors, so there
is no network call and no key needed. One test does real numerical work: int8
quantisation must preserve the top-5 ordering that float32 produced, which is
what makes a sub-megabyte committed index defensible.

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
