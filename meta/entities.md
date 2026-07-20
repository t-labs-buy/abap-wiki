# Entity Registry — Canonical Names & Aliases

The single source of truth for names. Before creating **any** new workstream folder, workstream file, stakeholder folder, or development record, run the Pre-Create Normalization Check in `CLAUDE.md` against this registry.

- **Canonical Slug** is what appears in folder names, file names, frontmatter, and `[[wikilinks]]`.
- **Aliases** are lowercase, normalized variants (see the normalization table in `CLAUDE.md`).
- New alias spotted in a document → add it to the row. Genuinely new entity → add the row **first**, then create pages.

> ⚠️ **Seed data below is a starting proposal.** The rows marked _(verify)_ are common SAP workstream/module names — replace them with this project's real workstream list, system SIDs, and vendor names during setup. Delete rows that don't apply.

## Workstreams

| Canonical Slug | Display Name     | Aliases                                                            | Status     |
| -------------- | ---------------- | ------------------------------------------------------------------ | ---------- |
| OTC            | Order-to-Cash    | `otc`, `o2c`, `order to cash`, `order-to-cash`, `sd sales`         | _(verify)_ |
| P2P            | Procure-to-Pay   | `p2p`, `ptp`, `procure to pay`, `purchase to pay`, `mm purchasing` | _(verify)_ |
| RTR            | Record-to-Report | `rtr`, `r2r`, `record to report`, `fi/co`, `finance`               | _(verify)_ |

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

| Canonical Slug | Display Name       | Aliases                                      | Status                    |
| -------------- | ------------------ | -------------------------------------------- | ------------------------- |
| DEV            | Development system | `dev`, `development`, `dev box`, `d01`       | _(replace with real SID)_ |
| QAS            | Quality system     | `qas`, `qa`, `quality`, `test system`, `q01` | _(replace with real SID)_ |
| PRD            | Production system  | `prd`, `prod`, `production`, `live`, `p01`   | _(replace with real SID)_ |

## Vendors & Partners

| Canonical Slug | Display Name | Aliases              | Status |
| -------------- | ------------ | -------------------- | ------ |
| SAP            | SAP SE       | `sap`, `sap se`      | active |
| Sonepar        | Sonepar      | `sonepar`            | active |
| Geposit        | Geposit      | `geposit`            | active |
| CGI            | CGI          | `cgi`                | active |
| ES             | ES           | `es`                 | active |
| Veda           | Veda         | `veda`               | _(verify — author of the formal ABAP Development Standards document)_ |

_(Sonepar is the client organization; Geposit is the external valid-address register provider; CGI and ES are implementation partners. Veda authored the ABAP Development Standards document.)_
