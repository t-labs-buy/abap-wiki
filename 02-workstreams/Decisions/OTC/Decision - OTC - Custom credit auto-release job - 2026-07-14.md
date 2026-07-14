---
title: "Decision - OTC - Custom credit auto-release job - 2026-07-14"
type: decision
zone: 02-workstreams
status: active
owner: "Senthil Palanivelu"
created: 2026-07-14
updated: 2026-07-14
workstream: OTC
tags: [decision, credit-management, fscm]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# Decision — Custom credit auto-release job

**Workstream:** [[OTC]]
**Date:** 2026-07-14
**Status:** Confirmed (by Anna Larsen; agreed by Jonas Weber)

## Context

Key-account sales orders (customer group Z1) stall in credit block even when open exposure is below the insured limit. The insured-limit data lives in the legacy **ZINSURANCE** table, maintained by an external broker feed, and is **not** replicated into FSCM.

## Options considered

- **(a) Standard:** configure automatic release via FSCM credit management rules. (Jonas's initial preference.)
- **(b) Custom:** periodic Z-report that re-checks exposure against the insured limit in ZINSURANCE and calls the release/BAPI to unblock orders.

## Decision

Go with **option (b), the custom periodic job**.

## Rationale

- ZINSURANCE broker-feed data is not in FSCM.
- Rebuilding the broker interface into FSCM estimated at 25+ person-days — out of scope for Wave 2.
- Jonas agreed after seeing the interface effort; confirmed by Anna.

## Consequences

- New object [[OTC - E-001 - Credit Auto-Release Job]] (report ZSD_CREDIT_AUTORELEASE + class ZCL_SD_CREDIT_RELEASE), scheduled every 30 minutes via SM36.
- Hard compliance requirement: write a BAL application-log entry for every released order.
- Use `BAPI_TRANSACTION_COMMIT` with `WAIT = 'X'` — see [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]].

Source: [[OTC - Design Review - 2026-07-14]]
