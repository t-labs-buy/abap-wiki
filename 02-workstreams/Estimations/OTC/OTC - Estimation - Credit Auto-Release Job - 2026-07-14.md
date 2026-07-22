---
title: "OTC - Estimation - Credit Auto-Release Job - 2026-07-14"
type: estimation
zone: 02-workstreams
status: draft
owner: "Priya Nair"
created: 2026-07-14
updated: 2026-07-21
workstream: OTC
tags: [wave-2, credit-management]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# Estimation — Credit Auto-Release Job

**Workstream:** [[OTC]]
**Date:** 2026-07-14
**Status:** Initial — to be confirmed in the Wave 2 estimation sheet.

## Scope

Custom periodic report to auto-release credit-blocked key-account sales orders. See [[OTC - E-001 - Credit Auto-Release Job]].

## Assumptions

- ZINSURANCE data available and current enough for the exposure check.
- Reuse of standard release BAPI/FM; no FSCM broker interface rebuild.

## Per-object estimate

| Object | Activity | Estimated (PD) | Actual (PD) |
| --- | --- | --- | --- |
| ZSD_CREDIT_AUTORELEASE / ZCL_SD_CREDIT_RELEASE | Development | 5 | TBD |
| — | Testing | 2 | TBD |
| — | Documentation | 1 | TBD |
| **Total** | | **8** | TBD |

Complexity: medium.

## Linked from

- [[OTC - Design Review - 2026-07-14]] (meeting)
- [[OTC - E-001 - Credit Auto-Release Job]] (development)
