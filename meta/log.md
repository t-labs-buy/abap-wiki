# Ingestion Log

Append-only chronological history. One entry per ingest, newest at the bottom. Never edit or delete past entries.

**Entry format:**

```
- YYYY-MM-DD: Ingested {source description}. Updated [[page]], [[page]]. Created [[page]]. Open question: {question} — added to [[Open-Questions/{WS}]].
```

---

- 2026-07-14: Vault skeleton created (zones, meta files, templates). No content ingested yet.

- 2026-07-14: Ingested OTC Design Review Meeting Notes 2026-07-14.txt. Created OTC workstream page, 4 stakeholders (Anna Larsen, Jonas Weber, Priya Nair, Senthil Palanivelu), meeting page, decision (custom credit auto-release job), spec (draft), development OTC-E-001 (ZSD_CREDIT_AUTORELEASE), estimation, OTC Open-Questions page (Q1-Q3), Gotcha + Pattern for BAPI_TRANSACTION_COMMIT WAIT flag (P2P+OTC), and 2 FAQ pages (technical, process-and-transport). No new registry entities.

- 2026-07-14: Ingested abap_naming_conventions.txt. Created 01-standards/coding/Standard - ABAP Naming Conventions.md (Zone 01 evergreen coding standard). No new entities; linked to [[OTC - E-001 - Credit Auto-Release Job]] as field example. Added index entry.

- 2026-07-15: Curation — reorganized meta/index.md: moved all appended entries into their zone sections (01-standards/Coding now links [[Standard - ABAP Naming Conventions]]; OTC pages under 02-workstreams sections; patterns/gotchas/FAQs under 03-intelligence). No page content changed.

- 2026-07-15: Ingested INT.119.0 FTDS CR045 BP Address Validation 3.0.docx. Triaged as OTC spec. Updated [[OTC]] and meta/entities.md (added Sonepar, Geposit, CGI, ES). Created spec [[OTC - Spec - BP Address Validation]], development [[OTC - CR045 - BP Address Validation]], decision [[Decision - OTC - Address type removed from validation criteria - 2026-01-29]], and stakeholders [[OTC - Andreas Kvarnö]], [[OTC - Madeleine Jacobsson]], [[OTC - Tomas Kuniholm]], [[OTC - Hashini]]. Noted CR040→CR045 dependency and shared ZSD_ADR_VLD with CR044. No open-questions/FAQ additions — source Open-Questions section was empty.

- 2026-07-20: Ingested ABAP Dev standards.pdf (formal Veda standards doc, v0.2). Updated [[Standard - ABAP Naming Conventions]] with the authoritative module-code naming scheme, code conventions, and SAP module-code appendix. Created [[Standard - ABAP Programming Guidelines]], [[Standard - ABAP Performance Guidelines]] (01-standards/coding), and [[Process - Code Review]] (04-internal/processes). Updated meta/entities.md: added RE and BI module codes and Veda as document author.

- 2026-07-20: Ingested INT 1.0_Code_Review_Checklist_Tracker.xlsx (code review of report ZADUSR_SYNC, CR INT1.0 AD SAP User Integration, system EDE/200). Registered new workstream [[INT]] and system EDE in meta/entities.md; added `vedakala` alias to Veda. Created [[INT]], [[INT - Ramalakshmi]], [[INT - Vedakala]], and development [[INT - ZADUSR_SYNC]] (draft/ai-generated). Captured review Fail: missing sy-subrc check after READ at line 193. Updated [[Process - Code Review]] with checklist structure and this applied example.

- 2026-07-21: Adopted CP-1 (controlled tag vocabulary) from PROPOSAL - Organizational Memory Adoption. Added Tag Vocabulary (8 categories, 41 tags) to meta/entities.md; added Tag Discipline section to CLAUDE.md; added tag rule to conventions.md; ingest pipeline prompt now enforces vocabulary tags (ENTITIES_BUDGET raised 8k→16k). Migrated tags on all 30 vault pages: dropped type:/workstream: echoes, normalized aliases (sm36/batch→batch-job), enriched credit-job pages with bapi/batch-job.
