---
title: "Gotcha - BAPI_TRANSACTION_COMMIT wait flag"
type: gotcha
zone: 03-intelligence
status: active
owner: "Priya Nair"
created: 2026-07-14
updated: 2026-07-21
workstream: ""
tags: [bapi, locking]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# Gotcha — BAPI_TRANSACTION_COMMIT WAIT flag

## Scope

- **Applies to:** any ABAP code calling `BAPI_TRANSACTION_COMMIT` where a subsequent step in the same run depends on the committed data or on the lock being released — especially batch/periodic jobs that immediately re-read or re-process the same objects. Observed in P2P and OTC batch jobs on this project.
- **Does not apply to:** a final commit with no dependent follow-up step in the same program flow — there `WAIT = 'X'` only adds runtime. No release dependency recorded (standard BAPI behavior, not project-specific).

## Behavior

Calling `BAPI_TRANSACTION_COMMIT` **without** `WAIT = 'X'` returns control before the database update/locking work has fully completed. In batch jobs that immediately re-process or re-read the same objects, this caused intermittent **"order still locked"** errors.

## Fix

Always pass `WAIT = 'X'` when a subsequent step depends on the committed data or on the lock being released.

## Observed in

- **P2P** batch jobs — intermittent "order still locked" errors (raised by Priya Nair).
- **OTC** — mitigated up-front in [[OTC - E-001 - Credit Auto-Release Job]] by using `WAIT = 'X'`.

## Related

- [[Pattern - BAPI_TRANSACTION_COMMIT WAIT in batch jobs]]
- [[OTC - Design Review - 2026-07-14]]

## Linked from

- [[Decision - OTC - Custom credit auto-release job - 2026-07-14]] (decision)
- [[OTC - Design Review - 2026-07-14]] (meeting)
- [[OTC - E-001 - Credit Auto-Release Job]] (development)
- [[OTC - Priya Nair]] (stakeholder)
- [[Pattern - BAPI_TRANSACTION_COMMIT WAIT in batch jobs]] (pattern)
