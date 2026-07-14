# ABAP Vault

The canonical memory of the ABAP delivery project — standards, decisions, meeting outcomes, developments, and lessons learned.

**Read `CLAUDE.md` first.** It is the operating constitution: how knowledge is filed, named, linked, and de-duplicated. Every ingestion run and every Claude Code session follows it.

## How to use this vault

- **Contribute:** drop any document (transcript, deck, spec) into the OneDrive inbox folder. The pipeline ingests it automatically within minutes.
- **Read:** open this folder as a vault in Obsidian. Follow `[[wikilinks]]` between pages.
- **Ask:** run `claude` inside this folder and ask questions in plain English — answers cite vault pages.
- **Review:** after your document is ingested, skim the pages it touched and fix anything wrong.

## Structure

| Folder             | Holds                                                                        |
| ------------------ | ---------------------------------------------------------------------------- |
| `01-standards/`    | Coding standards, architecture principles, landscape docs (changes rarely)   |
| `02-workstreams/`  | Active work per workstream: meetings, decisions, specs, developments, issues |
| `03-intelligence/` | Reusable learnings: patterns, lessons, gotchas, FAQs                         |
| `04-internal/`     | Team operations: contacts, onboarding, processes, runbooks                   |
| `meta/`            | Index, log, dedup table, entity registry                                     |
| `raw/`             | Ingestion pipeline: `inbox/` (unprocessed) and `processed/` (archive)        |

Never delete pages — set `status: archived` in the frontmatter instead. Files enter only through the drop-zone.
