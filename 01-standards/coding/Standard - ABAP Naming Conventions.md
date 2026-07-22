---
title: "Standard - ABAP Naming Conventions"
type: standard
zone: 01-standards
status: evergreen
owner: "TBD"
created: 2026-07-14
updated: 2026-07-21
workstream: ""
tags: [naming-conventions]
source_files: ["abap_naming_conventions.txt", "ABAP Dev standards.pdf"]
---

# Standard — ABAP Naming Conventions

Canonical naming conventions for custom ABAP development on this project. Consistent naming keeps code readable and cleanly separates custom development from standard SAP.

> **Namespace rule:** All custom objects must begin with **Z** or **Y** (or a registered partner namespace like `/COMPANY/`). Letters A–S are reserved by SAP; using them risks objects being overwritten during upgrades.

> **Precedence:** **Customer (client) naming conventions take precedence over this document, if they exist.** When maintaining existing code, apply these standards retrospectively.

> **Formal source:** A formal project standards document exists — *ABAP Development Standards* (author: Veda; v0.1 2020-03-11, v0.2 with ABAP-on-HANA additions 2021-07-26). It introduces a **module-code (`XX`)** component in object names (see Appendix below and [[Standard - ABAP Programming Guidelines]], [[Standard - ABAP Performance Guidelines]]). Where the formal module-code scheme below differs from the generic industry prefixes in the earlier sections, **the formal module-code scheme is the authoritative project convention.**

Example adherence in the field: [[OTC - E-001 - Credit Auto-Release Job]] (report `ZSD_CREDIT_AUTORELEASE`, class `ZCL_SD_CREDIT_RELEASE`).

## Formal Object Naming Conventions (module-code scheme — authoritative)

`XX` = the SAP module code (see Appendix A). `<Description>` = meaningful description.

| Object | Format | Example |
| --- | --- | --- |
| Classes | `ZCL_XX_<Description>` | `ZCL_FI_CUSTOMER_CREATE` |
| Interfaces | `ZIF_XX_<Description>` | `ZIF_FI_CUSTOMER_CREATE` |
| Tables | `ZXX_<Description>` | `ZMM_PROD_HIER` |
| Field names in custom tables | `Z<Description>` (or standard SAP name if used for the same purpose, e.g. `WAERS`) | `ZCUSTOMER_NAME`, `WAERS` |
| Data Elements | `ZXX_<Description>` | `ZMM_PROD_HIER` |
| Domains | `ZXX_<Description>` | `ZMM_PROD_HIER` |
| Function Groups | `ZFGXX_<Function Group>` | `ZFGSD_PRICING_MASTER` |
| BAdI | `ZXX_<BADI_DEFINITION>` | `ZFI_CUSTOMER_UPD` |
| Projects (Customer Enhancements) | `ZXX_<Description>` | `ZFI_CUSTOMER` |
| Enhancement Spot | `ZXX_ES_<Name>` | `ZFI_ES_CUSTOMER_UPD` |
| Composite Enhancement Spot | `ZXX_CS_<Name>` | `ZFI_CS_CUSTOMER_UPD` |
| Enhancement Point | `ZXX_EP_<Name>` | `ZFI_EP_CUSTOMER_UPD` |
| Enhancement Implementations | `ZXX_EI_<Name>` | `ZFI_EI_CUSTOMER_UPD` |
| Composite Enhancement Implementations | `ZXX_CI_<Name>` | `ZFI_CI_CUSTOMER_UPD` |
| Function Modules | `ZXX_<FunctionModuleName>` | `ZFI_CUSTOMER_ADDR_UPD` |
| Programs | `ZXX_<Description>` | `ZFI_MASS_ASSET_TRANSFER` |
| Includes | `ZIXX_<IncludeName>` | `ZIFI_MASS_ASSET_TRANSFER_TOP` |
| Message Class | `ZXX_<Description>` | `ZFI_MSG` |
| Search Helps | `ZXX_<Description>` | `ZFI_GET_CUST_BANK_DETAILS` |
| Smart Forms | `ZXX_<Description>` | `ZFI_INVOICE_PRINT` |
| Structures | `ZSXX_<Description>` | `ZSFI_VENDOR_LIST` |
| Table Types | `ZTTXX_<Description>` | `ZTTFI_VENDOR_LIST` |
| Lock Object | `EZ_<Tablename>` | `EZ_KNA1` |
| Transactions | `ZXX_<Description>` | `ZFI_ASSET_POST` |
| Views | `ZYXX_<Description>` | `ZVMM_PROD_HIER` |
| OData Project | `ZXX_<Description>` | `ZFI_POST_CUSTOMER` |
| Web Service | `ZWS_<Description>` | `ZWS_PRODUCT_MASTER` |
| Workflow Standard Task | `ZTSXX_<RIVEFNO>_<Description>` | `ZTSFI_INVOICE_APPR` |
| Workflow Task Group | `ZTGXX_<Description>` | `ZTGFI_INVOICE_APPR` |
| Workflow Rules | `ZRUXXX_<Description>` | `ZRUFI_INV` |

Naming conventions for object types not listed here should be decided within the development team.

## Formal Code Conventions (variables, parameters — authoritative)

| Object | Format | Notes |
| --- | --- | --- |
| Field Symbols | `<FS_<Description>>` | Type them wherever possible (`TYPE DATA`/`TYPE ANY`). |
| Global Constants | `GC_<Description>` | Constants should generally be defined as **global** (`GC_`). |
| Local Constants | `LC_<Description>` | Use only when a local constant is required. |
| Types | `TY_<Description>` | e.g. `TY_ORDER_DATA` |
| Global Variables | `GV_` / `GT_` / `GS_` / `GR_` | Variable / Internal Table / Structure / Range |
| Local Variables | `LV_` / `LT_` / `LS_` / `LR_` | Variable / Internal Table / Structure / Range |
| Parameters* | `IV_` / `EX_` / `CH_` / `IT_` / `ET_` / `CT_` / `R_` | Import / Export / Changing / Import Tables / Export Tables / Changing Tables / Returning |
| Select-Options | `S_<Description>` | e.g. `S_LIFNR` |
| Screen Parameters | `P_<Description>` | Single selection-screen parameter, e.g. `P_DATE` |

*Parameter naming applies to Forms, Function Modules, and Class Method interfaces.

## Appendix A — SAP Module Codes

| Module | Code |
| --- | --- |
| Financial Accounting – GL/AR/AP/AA | FI |
| Controlling | CO |
| Materials Management | MM |
| Sales and Distribution | SD |
| Retail | RE |
| BW/BI | BI |

---

## Earlier generic reference (industry best practice — superseded where it conflicts with the formal scheme above)

### Data Dictionary (DDIC) Objects

| Object Type | Prefix | Example | Description |
| --- | --- | --- | --- |
| Database Table | `Zt_` / `Z` | `Zt_CUSTOMERS` | Transparent table storing transaction or master data |
| Structure | `Zs_` | `Zs_ORDER_DETAILS` | Global structure for data passing / interface definitions |
| Table Type | `Ztt_` | `Ztt_ORDER_DETAILS` | Global table type for internal tables |
| Data Element | `Zde_` | `Zde_CUST_ID` | Elementary data type defining semantic properties |
| Domain | `Zd_` | `Zd_STATUS_CODE` | Technical domain defining data types / value ranges |
| Database View | `Zv_` | `Zv_ACTIVE_USERS` | View combining data from multiple tables |
| Search Help | `Zsh_` | `Zsh_CUST_FINDER` | Input help (F4) object |

### Variables and Data Types (scope + type prefix)

**Scope Prefixes:** `l` local, `g` global, `s` static, `c` constant.
**Type Prefixes:** `v_` elementary, `s_` structure, `t_` internal table, `r_` reference, `o_` object instance.
**Common examples:** `lv_amount`, `ls_customer`, `lt_orders`, `gv_company_code`, `co_max_retries`. Class attributes use `mv_`, `ms_`, `mt_`.

### Object-Oriented ABAP

- Classes `ZCL_`, Interfaces `ZIF_`, Exception Classes `ZCX_`.
- Method parameters: Importing `iv_/is_/it_/io_`, Exporting `ev_/es_/et_/eo_`, Changing `cv_/cs_/ct_/co_`, Returning `rv_/rs_/rt_/ro_`.

### Programs and Function Modules (generic)

- Reports `Z_`/`ZR_`, Module Pools `ZSAPM_`/`ZM_`, Includes `ZINC_` (`_TOP`, `_F01`, `_O01`), Function Groups `ZFG_`, Function Modules `ZFM_`/`Z_`.

---

_Where the earlier generic prefixes conflict with the formal module-code scheme, follow the formal scheme. Assign a named owner to confirm project-specific deviations. See also [[Standard - ABAP Programming Guidelines]] and [[Standard - ABAP Performance Guidelines]]._

## Linked from

- [[INT - Vedakala]] (stakeholder)
- [[INT - ZADUSR_SYNC]] (development)
- [[Process - Code Review]] (process)
- [[Standard - ABAP Performance Guidelines]] (standard)
- [[Standard - ABAP Programming Guidelines]] (standard)
