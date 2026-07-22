---
title: "Pattern - BAPI_TRANSACTION_COMMIT WAIT in batch jobs"
type: pattern
zone: 03-intelligence
status: active
owner: "Priya Nair"
created: 2026-07-14
updated: 2026-07-21
workstream: ""
tags: [bapi, batch-job, locking]
source_files: ["OTC Design Review Meeting Notes 2026-07-14.txt"]
---

# Pattern — Use WAIT = 'X' on BAPI_TRANSACTION_COMMIT in batch jobs

## Context

Batch/periodic jobs that commit changes and then continue processing (or re-read/re-lock the same objects) must ensure the commit is fully applied before proceeding.

## When To Apply

- **Applies to:** batch/periodic jobs that commit via `BAPI_TRANSACTION_COMMIT` and continue processing the same or dependent objects in the same run.
- **Does not apply to:** flows where nothing after the commit depends on the committed state or the released lock (e.g. a job's final commit) — the WAIT adds runtime without preventing anything.

## Approach

Always call `BAPI_TRANSACTION_COMMIT` with `WAIT = 'X'` inside batch jobs.

## Observed in

- **P2P** — batch jobs hit intermittent "order still locked" errors without the WAIT flag.
- **OTC** — [[OTC - E-001 - Credit Auto-Release Job]] adopts `WAIT = 'X'` from the outset.

## Related

- [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]]

## Linked from

- [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]] (gotcha)
