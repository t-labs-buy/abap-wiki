---
title: "OTC - Design Review - 2026-07-14"
type: meeting
zone: 02-workstreams
status: active
owner: "Senthil Palanivelu"
created: 2026-07-14
updated: 2026-07-21
workstream: OTC
tags: [design-review, credit-management]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# OTC Design Review — 2026-07-14

**Date:** 2026-07-14, 10:00–11:00 CET
**Topic:** Sales order enhancement for automatic credit-block release
**Workstream:** [[OTC]]

## Attendees

- [[OTC - Anna Larsen]] — Client, SD Lead
- [[OTC - Jonas Weber]] — Client, Integration Architect
- [[OTC - Priya Nair]] — Our team, ABAP Senior Dev
- [[OTC - Senthil Palanivelu]] — Our team, Tech Lead

## Summary

Key-account sales orders (customer group Z1) get stuck in credit block even when open exposure is below the insured limit; the credit team releases them manually in VKM3 (~4h/day). A design review chose a custom periodic auto-release job over standard FSCM configuration because the insured-limit data (ZINSURANCE, external broker feed) is not replicated into FSCM.

## Pages updated by this meeting

- [[Decision - OTC - Custom credit auto-release job - 2026-07-14]] — approach decision
- [[OTC - E-001 - Credit Auto-Release Job]] — new development record
- [[OTC - Spec - Credit Block Auto-Release]] — spec (to be drafted by 2026-07-18)
- [[OTC - Estimation - Credit Auto-Release Job - 2026-07-14]] — initial effort
- [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]] — raised by Priya
- [[Open-Questions/OTC|OTC Open Questions]] — Q1, Q2, Q3

## Next steps

- Priya drafts the technical spec by 2026-07-18.
- Senthil adds the object to the Wave 2 WRICEF list.
- Follow-up review scheduled for 2026-07-22.

## Linked from

- [[Decision - OTC - Custom credit auto-release job - 2026-07-14]] (decision)
- [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]] (gotcha)
- [[OTC]] (workstream)
- [[Open-Questions/OTC|OTC Open Questions]] (open-questions)
