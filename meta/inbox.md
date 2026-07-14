# Processed Files — Deduplication Table

The pipeline checks this table before processing any file in `raw/inbox/`. Exact filename match = skip re-processing. Similar-but-different (v1 vs v2) = re-process and update existing pages.

One row per processed file. The pipeline appends; humans don't edit.

| Filename | Processed on | Pages touched | Notes |
| -------- | ------------ | ------------- | ----- |
| OTC Design Review Meeting Notes 2026-07-14.txt | 2026-07-14 | 064a402dea2d09a5f18cab75fa502593 | — | 02-workstreams/Workstreams/OTC.md, 02-workstreams/Stakeholders/OTC/OTC - Anna Larsen.md, 02-workstreams/Stakeholders/OTC/OTC - Jonas Weber.md, 02-workstreams/Stakeholders/OTC/OTC - Priya Nair.md, 02-workstreams/Stakeholders/OTC/OTC - Senthil Palanivelu.md, 02-workstreams/Meetings/OTC/OTC - Design Review - 2026-07-14.md, 02-workstreams/Decisions/OTC/Decision - OTC - Custom credit auto-release job - 2026-07-14.md, 02-workstreams/Specs/OTC/OTC - Spec - Credit Block Auto-Release.md, 02-workstreams/Developments/OTC/OTC - E-001 - Credit Auto-Release Job.md, 02-workstreams/Estimations/OTC/OTC - Estimation - Credit Auto-Release Job - 2026-07-14.md, 02-workstreams/Open-Questions/OTC.md, 03-intelligence/gotchas/Gotcha - BAPI_TRANSACTION_COMMIT wait flag.md, 03-intelligence/patterns/Pattern - BAPI_TRANSACTION_COMMIT WAIT in batch jobs.md, 03-intelligence/faqs/technical/FAQ - Credit Auto-Release Integration.md, 03-intelligence/faqs/process-and-transport/FAQ - Transporting Background Jobs.md |
