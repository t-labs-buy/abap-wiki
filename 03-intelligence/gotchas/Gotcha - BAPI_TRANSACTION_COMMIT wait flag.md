---
title: "Gotcha - BAPI_TRANSACTION_COMMIT wait flag"
type: gotcha
zone: 03-intelligence
status: active
owner: "Priya Nair"
created: 2026-07-14
updated: 2026-07-14
workstream: ""
tags: [gotcha, bapi, commit, locking]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# Gotcha — BAPI_TRANSACTION_COMMIT WAIT flag

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
