---
title: "Standard - ABAP Naming Conventions"
type: standard
zone: 01-standards
status: evergreen
owner: ""
created: 2026-08-27
updated: 2026-08-27
workstream: ""
tags: [naming-conventions]
source_files: [ABAP_dev_standards.pdf]
---

# Standard - ABAP Naming Conventions

Naming conventions for all custom (Z) ABAP repository objects and in-code identifiers. Objects not covered here are named by team decision.

> **Customer naming conventions take precedence over this standard where they exist.** When maintaining existing code, these conventions must be retrospectively applied.

`XX` = the two-character SAP **module code** (see [[Standard - ABAP Programming Guidelines]] and the module-code appendix; e.g. FI, CO, MM, SD, RE, BI).

## Object Naming Conventions

| Object | Format | Example |
| ------ | ------ | ------- |
| Classes | `ZCL_XX_<Description>` | `ZCL_FI_CUSTOMER_CREATE` |
| Interfaces | `ZIF_XX_<Description>` | `ZIF_FI_CUSTOMER_CREATE` |
| Tables | `ZXX_<Description>` | `ZMM_PROD_HIER` |
| Field names in custom tables | `Z<Description>` — or a standard SAP name if used for the same purpose (e.g. `WAERS` for currency) | `ZCUSTOMER_NAME`, `WAERS` |
| Data Elements | `ZXX_<Description>` | `ZMM_PROD_HIER` |
| Domains | `ZXX_<Description>` | `ZMM_PROD_HIER` |
| Function Groups | `ZFGXX_<Function Group>` | `ZFGSD_PRICING_MASTER` |
| BADI | `ZXX_<BADI_DEFINITION>` | `ZFI_CUSTOMER_UPD` |
| Projects (Customer Enhancements) | `ZXX_<Description>` | `ZFI_CUSTOMER` |
| Enhancement Spot | `ZXX_ES_<Enhancement Spot Name>` | `ZFI_ES_CUSTOMER_UPD` |
| Composite Enhancement Spot | `ZXX_CS_<Composite Enhancement Spot Name>` | `ZFI_CS_CUSTOMER_UPD` |
| Enhancement Point | `ZXX_EP_<Enhancement Point Name>` | `ZFI_EP_CUSTOMER_UPD` |
| Enhancement Implementations | `ZXX_EI_<Enhancement Implementation Name>` | `ZFI_EI_CUSTOMER_UPD` |
| Composite Enhancement Implementations | `ZXX_CI_<Composite Enhancement Implementation Name>` | `ZFI_CI_CUSTOMER_UPD` |
| Function Modules | `ZXX_<FunctionModuleName>` | `ZFI_CUSTOMER_ADDR_UPD` |
| Programs | `ZXX_<Description>` | `ZFI_MASS_ASSET_TRANSFER` |
| Includes | `ZIXX_<IncludeName>` | `ZIFI_MASS_ASSET_TRANSFER_TOP` |
| Message Class | `ZXX_<Description>` | `ZFI_MSG` |
| Search Helps | `ZXX_<Description>` | `ZFI_GET_CUST_BANK_DETAILS` |
| Smart forms | `ZXX_<Description>` | `ZFI_INVOICE_PRINT` |
| Structures | `ZSXX_<Description>` | `ZSFI_VENDOR_LIST` |
| Table Types | `ZTTXX_<Description>` | `ZTTFI_VENDOR_LIST` |
| Lock Object name | `EZ_<Tablename>` | `EZ_KNA1` |
| Transactions | `ZXX_<Description>` | `ZFI_ASSET_POST` |
| Views | `ZYXX_<Description>` | `ZVMM_PROD_HIER` |
| OData Project Name | `ZXX_<Description>` | `ZFI_POST_CUSTOMER` |
| Web Service | `ZWS_<Description>` | `ZWS_PRODUCT_MASTER` |
| Workflow Standard Task | `ZTSXX_<RIVEFNO>_<Description>` | `ZTSFI_INVOICE_APPR` |
| Workflow Task Group | `ZTGXX_<Description>` | `ZTGFI_INVOICE_APPR` |
| Workflow Rules | `ZRUXXX_<Description>` | `ZRUFI_INV` |

## Code Conventions (in-code identifiers)

| Object | Format | Notes |
| ------ | ------ | ----- |
| Field Symbols | `<FS_<Description>>` | Field symbols should be typed wherever possible (type `DATA` or type `ANY`). |
| Global Constants | `GC_<Description>` | Constants should generally be defined as global constants. |
| Local Constants | `LC_<Description>` | Use `LC_` if local constants are required. |
| Types | `TY_<Description>` | e.g. `TY_ORDER_DATA` |
| Global Variables | `GV_` var, `GT_` internal table, `GS_` structure, `GR_` range | e.g. `GV_AUFNR`, `GT_ORDER_DATA`, `GS_ORDER_DATA`, `GR_ALV` |
| Local Variables | `LV_` var, `LT_` internal table, `LS_` structure, `LR_` range | e.g. `LV_AUFNR`, `LT_ORDER_DATA`, `LS_ORDER_DATA`, `LR_ALV` |
| Parameters* | `IV_` import, `EX_` export, `CH_` changing, `IT_` import table, `ET_` export table, `CT_` changing table, `R_` returning | IM→Import, EX→Export, CH→Changing, IT→Import Tables, ET→Export Tables, CT→Changing Tables, R→Returning parameters from methods |
| Selection-Screen Select-Options | `S_<Description>` | e.g. `S_LIFNR` — use `S` for Select-Options |
| Selection-Screen Parameters | `P_<Description>` | e.g. `P_DATE` — use `P` for single selection-screen parameters |

*Parameter naming conventions apply to Forms, Function Modules, and Class Method interfaces.

## Related

- [[Standard - ABAP Programming Guidelines]]
- [[Standard - ABAP Performance Guidelines]]
- [[Process - Code Review]] — naming compliance is a review gate

## Linked from

- [[Process - Code Review]] (process)
- [[Standard - ABAP Programming Guidelines]] (standard)
