# Entity Registry — Canonical Names & Aliases

The single source of truth for names. Before creating **any** new workstream folder, workstream file, stakeholder folder, or development record, run the Pre-Create Normalization Check in `CLAUDE.md` against this registry.

- **Canonical Slug** is what appears in folder names, file names, frontmatter, and `[[wikilinks]]`.
- **Aliases** are lowercase, normalized variants (see the normalization table in `CLAUDE.md`).
- New alias spotted in a document → add it to the row. Genuinely new entity → add the row **first**, then create pages.

> ⚠️ **Seed data below is a starting proposal.** The rows marked _(verify)_ are common SAP workstream/module names — replace them with this project's real workstream list, system SIDs, and vendor names during setup. Delete rows that don't apply.

## Workstreams

| Canonical Slug | Display Name     | Aliases                                                                                   | Status     |
| -------------- | ---------------- | ----------------------------------------------------------------------------------------- | ---------- |
| OTC            | Order-to-Cash    | `otc`, `o2c`, `order to cash`, `order-to-cash`, `sd sales`                                | _(verify)_ |
| P2P            | Procure-to-Pay   | `p2p`, `ptp`, `procure to pay`, `purchase to pay`, `mm purchasing`                        | _(verify)_ |
| RTR            | Record-to-Report | `rtr`, `r2r`, `record to report`, `fi/co`, `finance`                                      | _(verify)_ |
| INT            | Integrations     | `int`, `integration`, `integrations`, `int1.0`, `ad sap user integration`, `ad user sync` | active     |

## SAP Modules

| Canonical Slug | Display Name         | Aliases                                                | Status     |
| -------------- | -------------------- | ------------------------------------------------------ | ---------- |
| SD             | Sales & Distribution | `sd`, `sales and distribution`, `sales & distribution` | _(verify)_ |
| MM             | Materials Management | `mm`, `materials management`                           | _(verify)_ |
| FI             | Financial Accounting | `fi`, `finance`, `financial accounting`, `gl/ar/ap/aa` | _(verify)_ |
| CO             | Controlling          | `co`, `controlling`                                    | _(verify)_ |
| PP             | Production Planning  | `pp`, `production planning`                            | _(verify)_ |
| RE             | Retail               | `re`, `retail`                                         | _(verify)_ |
| BI             | BW/BI                | `bi`, `bw`, `bw/bi`, `business intelligence`           | _(verify)_ |

## Systems

| Canonical Slug | Display Name            | Aliases                                      | Status                    |
| -------------- | ----------------------- | -------------------------------------------- | ------------------------- |
| DEV            | Development system      | `dev`, `development`, `dev box`, `d01`       | _(replace with real SID)_ |
| QAS            | Quality system          | `qas`, `qa`, `quality`, `test system`, `q01` | _(replace with real SID)_ |
| PRD            | Production system       | `prd`, `prod`, `production`, `live`, `p01`   | _(replace with real SID)_ |
| EDE            | EDE system (client 200) | `ede`, `ede/200`, `ede 200`                  | active                    |

## Vendors & Partners

| Canonical Slug | Display Name | Aliases            | Status                                                                                       |
| -------------- | ------------ | ------------------ | -------------------------------------------------------------------------------------------- |
| SAP            | SAP SE       | `sap`, `sap se`    | active                                                                                       |
| Sonepar        | Sonepar      | `sonepar`          | active                                                                                       |
| Geposit        | Geposit      | `geposit`          | active                                                                                       |
| CGI            | CGI          | `cgi`              | active                                                                                       |
| ES             | ES           | `es`               | active                                                                                       |
| Veda           | Veda         | `veda`, `vedakala` | _(verify — author of the formal ABAP Development Standards document; performs code reviews)_ |

_(Sonepar is the client organization; Geposit is the external valid-address register provider; CGI and ES are implementation partners. Veda authored the ABAP Development Standards document.)_

## Tag Vocabulary

The controlled vocabulary for the `tags:` frontmatter field. **Tags MUST come from this registry** — a needed-but-missing tag is added here first (with its category), then used. Same rule as entity slugs: never invent a second spelling; new variant spotted → add it to Aliases.

Tags are **domain tags only** — they say what a page is _about_. Do not tag what other frontmatter fields already say: never echo the page's `type:` (`spec`, `gotcha`, `stakeholder`, …) or its `workstream:` (`otc`, `int`, …) into `tags:`.

### technology

| Tag         | Covers / aliases                                              |
| ----------- | ------------------------------------------------------------- |
| bapi        | BAPI calls, `BAPI_*` function modules, commit handling        |
| idoc        | IDocs, ALE, change pointers                                   |
| cds         | CDS views, AMDP                                               |
| open-sql    | New Open SQL, SQL tuning constructs                           |
| hana        | HANA-specific behavior, code pushdown                         |
| enhancement | user exits, BAdIs, enhancement spots                          |
| batch-job   | background jobs, SM36/SM37, `sm36`, `background-job`, `batch` |
| report      | executable reports / ABAP programs                            |
| integration | interfaces, middleware, cross-system flows, `identity`        |
| fscm        | SAP Financial Supply Chain Management (credit mgmt config)    |

### business-object

| Tag                | Covers / aliases                           |
| ------------------ | ------------------------------------------ |
| sales-order        | order processing, VA01/VA02, `sales`       |
| credit-management  | credit blocks, exposure, VKM*              |
| master-data        | customer/vendor/material/BP master         |
| business-partner   | BP-specific master data                    |
| address-validation | address checks against reference data      |
| user-provisioning  | user accounts, AD sync, identity lifecycle |

### quality

| Tag                | Covers / aliases                  |
| ------------------ | --------------------------------- |
| performance        | runtime behavior, SQL tuning      |
| locking            | enqueue/dequeue, lock contention  |
| authorization      | auth checks, roles                |
| naming-conventions | object and variable naming rules  |
| documentation      | header/change documentation rules |

### process

| Tag           | Covers / aliases                               |
| ------------- | ---------------------------------------------- |
| code-review   | review findings, quality gates, `quality-gate` |
| transport     | TR handling, cutover, `process-and-transport`  |
| design-review | design review sessions and outcomes            |
| estimation    | effort figures, calibration data               |
| testing       | test planning, defect triage                   |

### role (stakeholder pages)

| Tag       | Covers / aliases                       |
| --------- | -------------------------------------- |
| client    | client-side stakeholder                |
| our-team  | our delivery team                      |
| developer | hands-on developer                     |
| tech-lead | technical lead                         |
| reviewer  | code/spec reviewer                     |
| it        | client IT (non-functional) stakeholder |

### phase

| Tag    | Covers / aliases      |
| ------ | --------------------- |
| wave-2 | Wave 2 delivery scope |

### artifact-kind

| Tag    | Covers / aliases                 |
| ------ | -------------------------------- |
| wricef | WRICEF-classified custom objects |

### governance

| Tag          | Covers / aliases                                          |
| ------------ | --------------------------------------------------------- |
| ai-generated | page not yet SME-validated (see CLAUDE.md; existing rule) |
