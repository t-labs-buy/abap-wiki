# Processed Files — Deduplication Table

The pipeline checks this table before processing any file in `raw/inbox/`. Exact filename match = skip re-processing. Similar-but-different (v1 vs v2) = re-process and update existing pages.

One row per processed file. The pipeline appends; humans don't edit.

> Table emptied on 2026-08-13 as part of the vault reset. Files processed before that date are no longer recorded here and will be re-ingested if dropped into `raw/inbox/` again.

| Filename | Processed on | Pages touched | Notes |
| -------- | ------------ | ------------- | ----- |
