---
title: "Standard - ABAP Programming Guidelines"
type: standard
zone: 01-standards
status: evergreen
owner: "TBD"
created: 2026-07-20
updated: 2026-07-20
workstream: ""
tags: [standard, coding, programming-guidelines, documentation]
source_files: ["ABAP Dev standards.pdf"]
---

# Standard — ABAP Programming Guidelines

Project programming rules and documentation standards for custom ABAP development. Source: *ABAP Development Standards* (author: Veda). Companion to [[Standard - ABAP Naming Conventions]] and [[Standard - ABAP Performance Guidelines]].

> **Objective:** deliver a consistent set of conventions to maximise quality, value, and maintainability. Everyone in the development process must apply these standards. **Customer naming/coding conventions take precedence** where they exist.

## Guiding Principles

- **Simplicity** — clarity of purpose is a prerequisite. Readable code enables future change and adequate testing. Use in-line/single-line comments where they aid understanding. *Keep it simple.*
- **Flexibility** — build for easy future adaptation; document thoroughly for later modifications and bug fixes.
- **User-acceptance** — all end-user-facing development must be as user-friendly as possible.
- **Performance** — well-performing programs reduce runtimes and drive user acceptance. Custom code is a main source of performance problems — see [[Standard - ABAP Performance Guidelines]].

## General Considerations

1. **No changes to standard SAP programs** (exception: OSS Notes).
2. Requirements must be clearly defined before development starts (preferably a signed-off functional/mapping specification).
3. Before creating a new ABAP object, review existing programs for reuse as a template or to fill the requirement.
4. All custom objects must follow the naming standards — see [[Standard - ABAP Naming Conventions]].
5. Technical specifications and unit-test documentation are the developer's responsibility.

## General Programming Rules

1. All coding done within the defined **DEV** environment.
2. **Standard-first:** look for standard functionality before building new (supported, modular, lowers TCO).
3. Do **not** copy-and-modify existing programs (causes confusion, duplication, support pain). Investigate the original for modification; only create a new program if that is not possible.
4. Assign custom developments to the **package** related to that module.
5. **Internal tables:** define **without header line**; process loops by assigning field symbols `<fs>` for performance.
6. **Subroutines / form routines:** use to increase readability; **all formal parameters must be typed**.
7. **Text elements:** use text-elements for output literals (central maintenance + translation). Maintain original language **English**; size text symbols ~50% larger than English.
8. **BOOLEAN:** SAP has no Boolean type — use DDIC `BOOLE-BOOLE` or `XFELD`; values `'X'` = true, `SPACE` = false.
9. **No hard coding:** use text elements for output; define values as constants in the DATA part or in table **ZTVARVC** (e.g. plants/org values that may change).
10. **Authority checks:** find the correct authorization object(s); every report should belong to an authorization group.
11. **Table modifications:** programs that update SAP standard master/transactional data **MUST** use transaction codes via standard FMs, BAPIs, BDC, or `CALL TRANSACTION` (ensures LUW, rollback, locking, edits). **Never** update SAP tables directly. **Never** update configuration tables via ABAP.
12. **Error handling:** proper handling to avoid uncontrolled terminations; check return codes after every relevant event; use CATCH for runtime errors; explicitly test all expected `SY-SUBRC` values when more than two are possible; capture and report all error logs.
13. Use **in-line declarations** wherever possible.
14. Avoid generic messages (a message with just 4 variables).
15. Do not use **WAIT** statements unconditionally (performance risk).
16. **Use classes wherever possible** — promotes reusability and flexibility.

## Program Documentation

### Header block (every report)

```
**********************************************************************
* Program     : ZXX_EXAMPLE_PROGRAM
* Author      : Name
* Created     : MM/DD/YYYY
* TR#         : XXXXXXXXXX
* Description : Example program which does some sort of reporting
```

### Change documentation (every post-release change)

```
**********************************************************************
* Changed On     : DD/MM/YYYY
* Changed By      : Name
* TR#            : XXXXXXXXXX
* Defect/Ticket# : <if applicable>
* Description    :
**********************************************************************
```

- **Do not delete existing code** during a change — comment it out with attribution.
- Reference added lines against the revision block. Example:

```
lv_amount = ls_mseg-dmbtr.  "Commented <User ID> <Date> <Defect/ChangeNo>
lv_amount = ls_mseg-wrbtr.  "Inserted  <User ID> <Date> <Defect/ChangeNo>
```

- Block changes marked with `*>>>>>> Start of Insert/Comments …` and `*<<<<<<< End of Insert/comments …` fences plus `<User ID> <Date> <Defect/ChangeNo>`.

## Related

- [[Standard - ABAP Naming Conventions]]
- [[Standard - ABAP Performance Guidelines]]
- [[Process - Code Review]]
