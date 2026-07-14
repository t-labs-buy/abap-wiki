---
title: "Standard - ABAP Naming Conventions"
type: standard
zone: 01-standards
status: evergreen
owner: "TBD"
created: 2026-07-14
updated: 2026-07-14
workstream: ""
tags: [standard, naming-conventions, coding]
source_files: ["abap_naming_conventions.txt"]
---

# Standard — ABAP Naming Conventions

Canonical naming conventions for custom ABAP development on this project. Consistent naming keeps code readable and cleanly separates custom development from standard SAP.

> **Namespace rule:** All custom objects must begin with **Z** or **Y** (or a registered partner namespace like `/COMPANY/`). Letters A–S are reserved by SAP; using them risks objects being overwritten during upgrades.

Example adherence in the field: [[OTC - E-001 - Credit Auto-Release Job]] (report `ZSD_CREDIT_AUTORELEASE`, class `ZCL_SD_CREDIT_RELEASE`).

## Data Dictionary (DDIC) Objects

Descriptive abbreviations after the Z/Y prefix (SE11 global objects).

| Object Type | Prefix | Example | Description |
| --- | --- | --- | --- |
| Database Table | `Zt_` / `Z` | `Zt_CUSTOMERS` | Transparent table storing transaction or master data |
| Structure | `Zs_` | `Zs_ORDER_DETAILS` | Global structure for data passing / interface definitions |
| Table Type | `Ztt_` | `Ztt_ORDER_DETAILS` | Global table type for internal tables |
| Data Element | `Zde_` | `Zde_CUST_ID` | Elementary data type defining semantic properties |
| Domain | `Zd_` | `Zd_STATUS_CODE` | Technical domain defining data types / value ranges |
| Database View | `Zv_` | `Zv_ACTIVE_USERS` | View combining data from multiple tables |
| Search Help | `Zsh_` | `Zsh_CUST_FINDER` | Input help (F4) object |

## Variables and Data Types

Combine a **scope prefix** (where the variable lives) with a **type prefix** (kind of data held).

### Scope Prefixes

- `l` — Local (inside a method, form, or function)
- `g` — Global (throughout the program or class)
- `s` — Static (retains value between calls)
- `c` — Constant (fixed value)

### Type Prefixes

- `v_` — Elementary variable (string, integer, boolean, date)
- `s_` — Structure (single work area, multiple fields)
- `t_` — Internal table (collection of rows/structures)
- `r_` — Reference variable (pointer to object or data)
- `o_` — Object instance (class instantiation)

**Common examples:** `lv_amount` (local elementary), `ls_customer` (local structure), `lt_orders` (local internal table), `gv_company_code` (global elementary), `co_max_retries` (constant).

## Object-Oriented ABAP (Classes & Interfaces)

### Repository Level

- Classes: `ZCL_` (e.g., `ZCL_INVOICE_PROCESSOR`)
- Interfaces: `ZIF_` (e.g., `ZIF_PAYMENT_GATEWAY`)
- Exception Classes: `ZCX_` (e.g., `ZCX_AUTH_ERROR`)

### Method Parameters

| Parameter Type | Prefix | Example | Purpose |
| --- | --- | --- | --- |
| Importing | `iv_`, `is_`, `it_`, `io_` | `iv_user_id` | Read-only input into the method |
| Exporting | `ev_`, `es_`, `et_`, `eo_` | `es_user_profile` | Output returned to caller |
| Changing | `cv_`, `cs_`, `ct_`, `co_` | `ct_error_logs` | Input modified and returned |
| Returning | `rv_`, `rs_`, `rt_`, `ro_` | `rv_is_valid` | Single functional return value |

**Class attributes (member variables):** use `mv_`, `ms_`, `mt_` to indicate member scope and distinguish from local variables (`lv_`).

## Programs and Function Modules

- Executable Programs (Reports): `Z_` or `ZR_` (e.g., `ZR_SALES_REPORT`)
- Module Pools (Screen Dialogs): `ZSAPM_` or `ZM_` (e.g., `ZSAPM_INVENTORY`)
- Includes: `ZINC_` or suffix `_TOP` (global data), `_F01` (subroutines), `_O01` (PBO modules)
- Function Groups: `ZFG_` (e.g., `ZFG_USER_ADMIN`)
- Function Modules: `ZFM_` or `Z_` (e.g., `ZFM_GET_USER_DETAILS`)

---

_Company guidelines may vary slightly; the above reflects widely accepted industry best practice. Assign a named owner to confirm project-specific deviations._
