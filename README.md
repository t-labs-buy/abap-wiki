# ABAP Vault

The canonical memory of the ABAP delivery project — standards, decisions, meeting outcomes, developments, and lessons learned.

**Read `CLAUDE.md` first.** It is the operating constitution: how knowledge is filed, named, linked, and de-duplicated. Every ingestion run and every Claude Code session follows it.

## How to use this vault

- **Contribute:** drop any document (transcript, deck, spec — or ABAP source code exports for auto-documentation) into the OneDrive inbox folder. The pipeline ingests it automatically within minutes.
- **Read:** open this folder as a vault in Obsidian. Follow `[[wikilinks]]` between pages.
- **Ask:** run `claude` inside this folder and ask questions in plain English — answers cite vault pages.
- **Review:** after your document is ingested, skim the pages it touched and fix anything wrong.

## Structure

| Folder             | Holds                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| `01-standards/`    | Coding standards, architecture principles, landscape docs (changes rarely)                        |
| `02-workstreams/`  | Active work per workstream: meetings, decisions, specs (FS/TS), developments, estimations, issues |
| `03-intelligence/` | Reusable learnings: patterns, lessons, gotchas, troubleshooting guides, FAQs                      |
| `04-internal/`     | Team operations: contacts, onboarding, processes, runbooks                                        |
| `meta/`            | Index, log, dedup table, entity registry                                                          |
| `raw/`             | Ingestion pipeline: `inbox/` (unprocessed) and `processed/` (archive)                             |

Never delete pages — set `status: archived` in the frontmatter instead. Files enter only through the drop-zone.

## Supported file types

What the ingest pipeline (`.github/scripts/abap-ingest.py`) can read, and what it uses to do it. Every extractor degrades gracefully: if a library or binary is missing, the file is logged and left in `raw/inbox/` for the curator rather than breaking the run.

| File type           | Primary extractor            | Fallback                     | System binary                    | Ready in CI |
| ------------------- | ---------------------------- | ---------------------------- | -------------------------------- | ----------- |
| PDF                 | `pdfplumber`                 | OCR path (below)             | —                                | Yes         |
| PDF (no text layer) | `pdf2image` + `pytesseract`  | none — logged for curator    | `poppler-utils`, `tesseract-ocr` | Yes         |
| DOCX                | `pandoc` binary              | `python-docx`                | `pandoc` (primary only)          | Yes         |
| PPTX                | `markitdown`                 | `python-pptx`                | —                                | Yes         |
| XLSX                | `openpyxl` (dual load)       | none — logged                | —                                | Yes         |
| XLS                 | `xlrd`                       | LibreOffice → XLSX extractor | `soffice` (fallback only)        | Yes         |
| DOC                 | LibreOffice → DOCX extractor | none — logged                | `soffice`                        | No          |
| PPT                 | LibreOffice → PPTX extractor | none — logged                | `soffice`                        | No          |

Formats handled without an extraction library:

| File type                 | Handling                                          |
| ------------------------- | ------------------------------------------------- |
| TXT, MD, CSV, ABAP source | Direct file read (UTF-8, falling back to latin-1) |
| VTT                       | Same read, then timestamps and cue tags stripped  |
| PNG, JPG, GIF, WEBP       | Base64-encoded and sent to Claude vision          |
| Audio / video             | Not extractable — marked `TRANSCRIPTION NEEDED`   |

**Legacy `.doc` and `.ppt` currently have no working path**, because the LibreOffice install is commented out in `.github/workflows/abap-vault-ingest.yml` (it adds ~2 min to every run). They will always land on the curator until that line is enabled. Re-save them as `.docx`/`.pptx`, or export to PDF, before dropping them.

Other unprocessable inputs: password-protected files, Visio (export to PNG first), and anything over ~40 MB via the OneDrive bridge.

Extractor tests live in `.github/scripts/tests/` — see the README there for how to run them.
