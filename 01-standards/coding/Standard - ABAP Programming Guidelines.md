---
title: "Standard - ABAP Programming Guidelines"
type: standard
zone: 01-standards
status: evergreen
owner: ""
created: 2026-08-27
updated: 2026-08-27
workstream: ""
tags: [documentation, authorization]
source_files: [ABAP_dev_standards.pdf]
---

# Standard - ABAP Programming Guidelines

General ABAP development rules that standardize custom development for quality, value, and maintainability. Every developer must familiarize themselves with these and apply them; when maintaining existing code the standards must be retrospectively applied. Customer standards take precedence where they exist.

## Guiding Principles

- **Simplicity** — Transparency and clarity of purpose are prerequisites for any development. Readability is essential for future changeability and adequate testing. Single-line / in-line comments in every part of the code are essential. Keep it simple.
- **Flexibility** — Development should allow easy future adaptation to changed circumstances. Good, detailed documentation is essential for later modifications and bug fixes.
- **User-Acceptance** — All end-user-interfacing development should be as user-friendly as possible.
- **Performance** — Well-performing programs reduce runtimes and drive user acceptance. User-defined programs are a main trigger of performance problems, which are painful to detect and correct — avoid them from the beginning. See [[Standard - ABAP Performance Guidelines]].

## General Considerations

1. No changes may be made to standard SAP programs (exception: OSS Notes).
2. Requirements should be clearly defined before development starts (preferably in a signed-off functional specification / mapping document).
3. Before creating a new ABAP, existing programs will be reviewed to determine if they can be used as a template or fill the requirement.
4. All custom development objects have to be named according to the naming standards — see [[Standard - ABAP Naming Conventions]].
5. Technical Specifications and Unit Test documentation are the responsibility of the developer.

## General Programming Rules (adhere to unless approved)

1. All coding must be done within the defined DEV environment.
2. Look to standard functionality first before developing new — standard functionality is supported, modular, and reduces redundant custom code, significantly reducing Total Cost of Ownership.
3. Existing programs should not be copied and modified (causes confusion, duplicates code, hard to support); instead investigate the original for modification. If not possible, a new program may be created.
4. Custom developments will typically be assigned to the package related to that module.
5. **Internal tables:** should be defined **without header line**. Loops should be processed by assigning field symbols `<fs>` (points to the field content at runtime — positive performance effect).
6. **Subroutines / Form routines:** use form routines to increase readability; all formal parameters have to be typed.
7. **Standard texts / text elements:** the use of text-elements is the appropriate way to output text literals in a report — enables central maintenance and translation. All text elements have to be maintained in **English** as the original language. Set the length of text symbols to be 50% larger than the English text (most languages are less compact).
8. **BOOLEAN:** SAP has no Boolean data type. For all switch elements (checkboxes, radio buttons, etc.) use variables referring to DDIC object `BOOLE-BOOLE` or `XFELD`. Possible values: `'X'` = true, `SPACE` = false.
9. **Hard coding** of values is not good practice. Use text-elements for printed/screen output, headers, etc. Define values as constants in the DATA part or in the `ZTVARVC` table. Example: avoid `IF plant = 'US01'` — organizations change and plants get added; store such values in `ZTVARVC`.
10. **Authority checks:** effort should be made to find the correct authorization object(s) to check. As a rule, authorization checks should be used whenever appropriate to verify the user's access level, and every report should belong to an authorization group.
11. **Table modifications by ABAP programs:**
    - Programs that update SAP standard master and transactional data **MUST ALWAYS** use SAP transaction codes (where available) via standard SAP Function Modules, BAPIs, BDC, or `CALL TRANSACTION` — this ensures logical units of work, rollback, locking, and edits. **SAP tables MUST NEVER be updated directly.**
    - ABAP programs **MUST NEVER** be used to update configuration tables.
12. **Error handling:**
    - All programs must include proper error handling to avoid undesirable terminations — return codes must be checked after every relevant event.
    - Use `CATCH`/`ENDCATCH` to trap runtime errors.
    - If more than two possible `SY-SUBRC` values are possible after an event, all expected values should be tested explicitly and handled.
    - All error logs should be captured and reported to the user.
13. **Declaring variables:** use in-line declarations wherever possible.
14. **Messages:** use of generic messages (message with just 4 variables) should be avoided.
15. **Wait statements:** should not be used unconditionally — they can lead to performance issues.
16. **Use classes wherever possible** — promotes code reusability and flexibility.

## Program Documentation

### Header Documentation

A report header **must** be included in every report. It contains general information on the program and a history of changes. The header block should be:

```
**********************************************************************
* Program     : ZXX_EXAMPLE_PROGRAM
* Author      : Name
* Created     : MM/DD/YYYY
* TR#         : XXXXXXXXXX
* Description : Example Program which does some sort of reporting
```

### Change Documentation

All changes made after first release **must** be tracked in the Revision Log section of the header and within the code itself:

```
**********************************************************************
* Changed On    : 20/3/2020
* Changed By    : Name
* TR#           : XXXXXXXXXX
* Defect/Ticket#: <if applicable>
* Description   :
**********************************************************************
```

During a code change, existing code should **NOT** be deleted. If no longer relevant it may be removed by commenting out appropriately. Any added lines should also be referenced against the revision block. Examples:

```
lv_amount = ls_mseg-dmbtr. "Commented <User ID> <Date> <Defect/ChangeNo>
lv_amount = ls_mseg-wrbtr. "Inserted  <User ID> <Date> <Defect/ChangeNo>

*>>>>>> Start of Comments <User ID> <Date> <Defect/ChangeNo>
...<Commented Code>
*<<<<<<< End of comments  <User ID> <Date> <Defect/ChangeNo>

*>>>>>> Start of Insert <User ID> <Date> <Defect/ChangeNo>
...<Inserted Code>
*<<<<<<< End of Insert  <User ID> <Date> <Defect/ChangeNo>
```

## Related

- [[Standard - ABAP Naming Conventions]]
- [[Standard - ABAP Performance Guidelines]]
- [[Process - Code Review]]

## Linked from

- [[Process - Code Review]] (process)
- [[Standard - ABAP Naming Conventions]] (standard)
- [[Standard - ABAP Performance Guidelines]] (standard)
