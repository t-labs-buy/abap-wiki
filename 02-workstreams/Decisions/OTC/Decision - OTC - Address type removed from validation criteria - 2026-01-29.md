---
title: "Decision - OTC - Address type removed from validation criteria - 2026-01-29"
type: decision
zone: 02-workstreams
status: active
owner: "Andreas Kvarnö"
created: 2026-07-15
updated: 2026-07-21
workstream: OTC
tags: [master-data, address-validation]
source_files: ["INT.119.0 FTDS CR045 BP Address Validation 3.0.docx"]
---

# Decision — Remove address type from BP address validation criteria

**Workstream:** [[OTC]]
**Date:** 2026-01-29 (spec v3.0)
**Status:** Confirmed (documented in CR045 FTDS v3.0)

## Context

In earlier versions of the CR045 BP Address Validation design, **address type** was part of the validation criteria matched against reference table `ZSD_ADR_VLD`.

## Decision

Address type is **no longer** a validation criterion.

## Rationale

It has been decided to only upload **relevant address types** into `ZSD_ADR_VLD`. Because the table only ever holds relevant address types, checking address type at validation time is redundant.

## Consequences

- Simplifies the online validation and the detection report — matching is only on postal code and city (same-row) per [[OTC - Spec - BP Address Validation]].
- Affects [[OTC - CR045 - BP Address Validation]].

Source: CR045 / INT.119.0 FTDS v3.0.

## Linked from

- [[OTC - Andreas Kvarnö]] (stakeholder)
- [[OTC - CR045 - BP Address Validation]] (development)
- [[OTC - Spec - BP Address Validation]] (spec)
- [[OTC]] (workstream)
