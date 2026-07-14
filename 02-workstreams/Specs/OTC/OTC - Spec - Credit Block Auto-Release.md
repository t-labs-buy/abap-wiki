---
title: "OTC - Spec - Credit Block Auto-Release"
type: spec
zone: 02-workstreams
status: draft
owner: "Priya Nair"
created: 2026-07-14
updated: 2026-07-14
workstream: OTC
tags: [spec, credit-management]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# Spec — Credit Block Auto-Release

**Workstream:** [[OTC]]
**Status:** Draft — Priya Nair to complete technical spec by 2026-07-18

## Functional summary

Key-account sales orders (customer group Z1) that are held in credit block should be released automatically when open exposure is below the insured limit recorded in the legacy ZINSURANCE table. Replaces the manual VKM3 release performed by the credit team (~4h/day).

## Technical outline

- Report **ZSD_CREDIT_AUTORELEASE** with logic class **ZCL_SD_CREDIT_RELEASE**.
- Reads insured limit from ZINSURANCE (broker-feed maintained).
- Compares against open exposure; releases eligible orders via BAPI_SALESORDER_CHANGE / release FM.
- Scheduled every 30 minutes via SM36.
- Writes a BAL application-log entry per released order (compliance requirement).
- Commit with `BAPI_TRANSACTION_COMMIT WAIT = 'X'`.

## Related

- Development: [[OTC - E-001 - Credit Auto-Release Job]]
- Decision: [[Decision - OTC - Custom credit auto-release job - 2026-07-14]]
- Open questions: [[Open-Questions/OTC|OTC Open Questions]]
