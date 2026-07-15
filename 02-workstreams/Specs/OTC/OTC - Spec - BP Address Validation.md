---
title: "OTC - Spec - BP Address Validation"
type: spec
zone: 02-workstreams
status: draft
owner: "Andreas Kvarnö"
created: 2026-07-15
updated: 2026-07-15
workstream: OTC
tags: [spec, master-data, business-partner, address-validation]
source_files: ["INT.119.0 FTDS CR045 BP Address Validation 3.0.docx"]
---

# Spec — BP Address Validation (CR045 / INT.119.0)

**Workstream:** [[OTC]]
**Status:** Draft — v3.0 (2026-01-29). Technical solution, error-handling/logging, testing and risk sections still open in the source document.

## Functional summary

Sonepar uses an external provider (**Geposit**) to keep an updated register of valid Swedish addresses. This register is loaded into the custom reference table **ZSD_ADR_VLD** and matched against SAP Business Partners with country code **SE** in order to:

1. **During BP maintenance (create/change)** — prevent entry/save of an invalid address.
2. **After a reference-table update** — identify existing BPs whose address is no longer valid.

The same table (ZSD_ADR_VLD) is also used for sales-order address validation (CR044, built by [[OTC - Hashini]]).

## Address validation during BP maintenance

- Applies to manual **creation and change** of BPs via GUI (t-code **BP**) and Fiori apps: *Maintain BP*, *Manage Business Partner Master Data*, *Manage Supplier Master Data*, *Manage Customer Master Data*, including Fiori **mass change** apps.
- **Not** applied to creation/change coming through integrations (per functional solution — integration path handled separately).

### Selection criteria (parameter table)

- A flexible parameter table defines which BPs address validation applies to; behaves like any SAP input field with include/exclude ranges.
- Blank field = no discrimination criterion.
- Clarification (2025-12-18): **Business Partner** and **Archive flag** are always maintained as **EXCLUDE** in the parameter table.
  - Example: BP `3000000040`, archive flag unchecked, maintained as exclude → validation **should** take place.
  - Example: BP `300000050`, archive flag checked, maintained as exclude → validation should **not** take place.
- Archive flag (BUT000-XDELE) must support both **include** and **exclude** of archived BPs.

### Match logic against ZSD_ADR_VLD

| Compared | BP table | BP field | Reference field (ZSD_ADR_VLD) |
| --- | --- | --- | --- |
| Postal Code | ADDR1_DATA | POST_CODE1 | POST_CODE |
| City | ADDR1_DATA | CITY1 | LOCALITY |

- Both postal code and city must exist, **and appear in the same row** of ZSD_ADR_VLD.
- Postal code: SE format is `XXX YY` in SAP but `XXXYY` in the reference table — **ignore blanks** when comparing.
- City comparison is **not case sensitive**.
- v3.0 change: address type is **no longer** a validation criterion (only relevant address types are uploaded to ZSD_ADR_VLD). See [[Decision - OTC - Address type removed from validation criteria - 2026-01-29]].

### Behaviour on invalid address

- Save is blocked; red error message:
  - EN: "Address does not match reference table ZSD_ADR_VLD"
  - SV: "Adressen stämmer inte överens med referenstabell ZSD_ADR_VLD"

## Address validation report (after reference-table update)

When Sonepar receives a new register from Geposit:
1. Extract existing table; analyse (outside SAP) which postal codes/cities disappear and which city+postal-code combos change.
2. Use results as filter to extract affected BPs.
3. Upload the latest register into ZSD_ADR_VLD (existing values overwritten).
4. Maintain affected BPs (manual or mass-change app) with valid address data.
5. As a precaution, run a background report to verify all BPs are consistent with the updated table.

Report requirements:
- Available in **GUI and Fiori**, triggered manually or via job.
- Lists all BPs whose address is not compatible with the reference table.
- Uses the same selection-criteria parameter table and match logic as online validation.
- Output **exportable to Excel**.

## Impacted business processes

- BP master data maintenance (customer / supplier / general BP).
- Sales-order processing (shares ZSD_ADR_VLD via CR044).
- **CR040** (set transportation zone + default unloading point in BP master data) has a **dependency on CR045** — it relies on the validated postal code and city.

## Related

- Development: [[OTC - CR045 - BP Address Validation]]
- Decision: [[Decision - OTC - Address type removed from validation criteria - 2026-01-29]]
- Reference data provider: [[Geposit]]
- Shared table dependency: [[OTC - CR044 - Order Address Validation]]
- Downstream dependency: [[OTC - CR040 - Transportation Zone Derivation]]
