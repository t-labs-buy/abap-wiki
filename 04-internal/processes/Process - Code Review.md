---
title: "Process - Code Review"
type: process
zone: 04-internal
status: evergreen
owner: ""
created: 2026-08-27
updated: 2026-08-27
workstream: ""
tags: [code-review, naming-conventions, performance]
source_files: [ABAP_dev_standards.pdf]
---

# Process - Code Review

All code should pass through a code review **before releasing the transport**. This process defines the mandatory gates.

## Review Gates (all must pass before transport release)

1. The **extended syntax check (SLIN)** should display **no errors**.
2. **Strictly adhere to all naming and coding conventions** in the development standards. **If a client naming-convention document exists, it takes priority over the internal standards.** See [[Standard - ABAP Naming Conventions]] and [[Standard - ABAP Programming Guidelines]].
3. **Code Review Checklist** document duly filled.
4. Ensure **efficient runtime performance** — see [[Standard - ABAP Performance Guidelines]].
5. **Technical Unit Test Document** completed.

## Recommended Before Review

- Before releasing the transport, it is encouraged to perform an **ATC (ABAP Test Cockpit) run**. This allows the developer to find and correct problems before the central run does.

## Related

- [[Standard - ABAP Naming Conventions]]
- [[Standard - ABAP Programming Guidelines]]
- [[Standard - ABAP Performance Guidelines]]

## Linked from

- [[Standard - ABAP Naming Conventions]] (standard)
- [[Standard - ABAP Performance Guidelines]] (standard)
- [[Standard - ABAP Programming Guidelines]] (standard)
