---
title: "OTC - CR045 - BP Address Validation"
type: development
zone: 02-workstreams
status: draft
owner: "TBD"
created: 2026-07-15
updated: 2026-07-21
workstream: OTC
tags: [wricef, master-data, business-partner, address-validation]
source_files: ["INT.119.0 FTDS CR045 BP Address Validation 3.0.docx"]
---

# OTC - CR045 - BP Address Validation

**Workstream:** [[OTC]]
**Reference:** INT.119.0 / SAP CR25_045
**Type:** Enhancement + Report (WRICEF)
**Status:** Draft — design spec v3.0; build not yet confirmed.

## Purpose

Validate SAP Business Partner (country SE) addresses against the custom reference table `ZSD_ADR_VLD` (loaded from the Geposit valid-address register). Two components:

1. **Online validation enhancement** — blocks save of a BP with an invalid postal code / city / combination during create/change via GUI (t-code BP) and Fiori apps (incl. mass change). Red error message (EN/SV).
2. **Detection report** — GUI + Fiori report (manual or job) listing existing BPs whose address is out of range after ZSD_ADR_VLD is updated; exportable to Excel.

See [[OTC - Spec - BP Address Validation]] for full functional/technical detail and match logic.

## Key logic notes

- Postal code SE format `XXX YY` (SAP) vs `XXXYY` (reference) — ignore blanks when comparing.
- City comparison case-insensitive.
- Postal code and city must be found on the **same row** of ZSD_ADR_VLD.
- Address type removed as criterion in v3.0 — see [[Decision - OTC - Address type removed from validation criteria - 2026-01-29]].
- Flexible selection-criteria parameter table (SAP input-field style include/exclude); BP number and archive flag always maintained as EXCLUDE.

## Dependencies

- [[ZSD_ADR_VLD]] (custom reference table — POST_CODE, LOCALITY; loaded from Geposit)
- [[BUT000]] (BP: PARTNER, BU_GROUP, XDELE)
- [[ADDR1_DATA]] (address: COUNTRY, POST_CODE1, CITY1)
- [[Geposit]] (external valid-address register provider)
- [[OTC - CR044 - Order Address Validation]] (shares ZSD_ADR_VLD; built by [[OTC - Hashini]])
- [[OTC - CR040 - Transportation Zone Derivation]] (depends on validated address from CR045)
- t-code BP; Fiori apps: Maintain BP, Manage Business Partner Master Data, Manage Supplier Master Data, Manage Customer Master Data

## Effort

- Not yet estimated.
