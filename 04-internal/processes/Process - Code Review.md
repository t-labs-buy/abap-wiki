---
title: "Process - Code Review"
type: process
zone: 04-internal
status: active
owner: "TBD"
created: 2026-07-20
updated: 2026-07-20
workstream: ""
tags: [process, code-review, quality-gate]
source_files: ["ABAP Dev standards.pdf"]
---

# Process — Code Review

All custom ABAP code must pass a code review **before the transport is released**. Source: *ABAP Development Standards* (author: Veda).

## Quality Gates (all must pass)

1. **Extended syntax check (SLIN)** displays **no errors**.
2. **Naming & coding conventions** are strictly followed — see [[Standard - ABAP Naming Conventions]] and [[Standard - ABAP Programming Guidelines]]. *If the client has a naming-convention document, it takes priority.*
3. **Code Review Checklist** document duly completed.
4. **Efficient runtime performance** ensured — see [[Standard - ABAP Performance Guidelines]].
5. **Technical Unit Test document** completed.

## Recommended before review

- Run **ATC (ABAP Test Cockpit)** to find and fix findings before the Central ATC run.
- Use **SAT** and **ST05** with production-like data volumes to catch performance bottlenecks.

## Notes

- Reviews happen in the **DEV** environment before transport release.
- No changes to standard SAP objects (exception: OSS Notes) — flag any such change during review.

## Related

- [[Standard - ABAP Programming Guidelines]]
- [[Standard - ABAP Performance Guidelines]]
- [[Standard - ABAP Naming Conventions]]
