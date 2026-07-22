---
title: "OTC - E-001 - Credit Auto-Release Job"
type: development
zone: 02-workstreams
status: active
owner: "Priya Nair"
created: 2026-07-14
updated: 2026-07-21
workstream: OTC
tags: [wricef, report, credit-management, bapi, batch-job]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# OTC - E-001 - Credit Auto-Release Job

**Workstream:** [[OTC]]
**Objects:** report `ZSD_CREDIT_AUTORELEASE`, class `ZCL_SD_CREDIT_RELEASE`
**Type:** Enhancement / Report (WRICEF — to be added to Wave 2 list)

## Purpose

Periodic job that automatically releases credit-blocked key-account sales orders (customer group Z1) when open exposure is below the insured limit in ZINSURANCE. See [[OTC - Spec - Credit Block Auto-Release]] and [[Decision - OTC - Custom credit auto-release job - 2026-07-14]].

## Runtime

- Scheduled every 30 minutes via SM36.
- Writes a BAL application-log entry for every released order (compliance requirement).
- Commits with `BAPI_TRANSACTION_COMMIT WAIT = 'X'` — see [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]].

## Effort

- Initial estimate: 8 person-days (dev 5, test 2, doc 1). Complexity medium. To be confirmed in Wave 2 estimation sheet.
- See [[OTC - Estimation - Credit Auto-Release Job - 2026-07-14]].

## Dependencies

- [[ZINSURANCE]] (legacy table, broker-feed maintained)
- [[BAPI_SALESORDER_CHANGE]]
- [[BAPI_TRANSACTION_COMMIT]]
- VKM3 (manual release transaction being replaced)
- BAL (application log)

## Open questions

- Q1: IDoc to CRM vs change pointers (Jonas)
- Q2: stale broker-feed handling (Anna)
- Q3: transporting the SM36 job definition
- See [[Open-Questions/OTC|OTC Open Questions]]

## Linked from

- [[Decision - OTC - Custom credit auto-release job - 2026-07-14]] (decision)
- [[FAQ - Credit Auto-Release Integration]] (faq)
- [[FAQ - Transporting Background Jobs]] (faq)
- [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]] (gotcha)
- [[OTC - Design Review - 2026-07-14]] (meeting)
- [[OTC - Estimation - Credit Auto-Release Job - 2026-07-14]] (estimation)
- [[OTC - Priya Nair]] (stakeholder)
- [[OTC - Senthil Palanivelu]] (stakeholder)
- [[OTC - Spec - Credit Block Auto-Release]] (spec)
- [[OTC]] (workstream)
- [[Open-Questions/OTC|OTC Open Questions]] (open-questions)
- [[Pattern - BAPI_TRANSACTION_COMMIT WAIT in batch jobs]] (pattern)
- [[Standard - ABAP Naming Conventions]] (standard)
