# Ingestion Log

Append-only chronological history. One entry per ingest, newest at the bottom. Never edit or delete past entries.

**Entry format:**

```
- YYYY-MM-DD: Ingested {source description}. Updated [[page]], [[page]]. Created [[page]]. Open question: {question} — added to [[Open-Questions/{WS}]].
```

---

- 2026-08-13: **Vault reset.** All content pages (zones 01–04), all `raw/inbox/` and `raw/processed/` source files, and the pre-reset ingest history were removed to start knowledge capture from scratch. Kept: CLAUDE.md, all `_Template-*.md` files, folder READMEs, `meta/conventions.md`. Reset: `meta/index.md`, `meta/inbox.md` (dedup table emptied — previously processed files will be re-ingested if dropped again), `meta/entities.md` (project-specific entities and accumulated tag vocabulary stripped back to the generic seed). The pre-reset vault remains in git history at commit `12a8241`.

- 2026-08-27: Ingested ABAP_dev_standards.pdf (SAP ABAP Development Standards, v0.2, author Veda). Created [[Standard - ABAP Naming Conventions]], [[Standard - ABAP Programming Guidelines]], [[Standard - ABAP Performance Guidelines]] (all 01-standards/coding), and [[Process - Code Review]] (04-internal). Updated meta/entities.md (added module slugs RE=Retail, BI=BW/BI from Appendix A). Updated meta/index.md. No workstream-specific or reusable-learning content extracted; document is stable Zone-01 reference material.
