# 02-workstreams — Active Delivery Work

Everything tied to a specific workstream, organized by **artifact type first, workstream second** (e.g. `Decisions/OTC/…`).

| Subfolder            | Holds                                                   | Naming                                          |
| -------------------- | ------------------------------------------------------- | ----------------------------------------------- |
| `Workstreams/`       | One overview page per workstream                        | `{WS}.md`                                       |
| `Stakeholders/{WS}/` | People: role, concerns, current asks                    | `{WS} - {Full Name}.md`                         |
| `Meetings/{WS}/`     | Meeting extracts (source material, not final artifacts) | `{WS} - {Topic} - {YYYY-MM-DD}.md`              |
| `Decisions/{WS}/`    | Design/scope/approach decisions with rationale          | `Decision - {WS} - {Topic} - {YYYY-MM-DD}.md`   |
| `Specs/{WS}/`        | Functional/technical spec content in durable form       | `{WS} - Spec - {Object or Topic}.md`            |
| `Developments/{WS}/` | WRICEF object records (incl. complexity + effort)       | `{WS} - {ID} - {Object Name}.md`                |
| `Estimations/{WS}/`  | Dated effort estimations, estimates vs actuals          | `{WS} - Estimation - {Topic} - {YYYY-MM-DD}.md` |
| `Issues/{WS}/`       | Defects and blockers with root cause                    | `{WS} - Issue - {Topic} - {YYYY-MM-DD}.md`      |
| `Open-Questions/`    | One rolling page per workstream                         | `{WS}.md`                                       |

`{WS}` is always the canonical workstream slug from `meta/entities.md`. For legacy objects not tied to any workstream, a canonical **module slug** (SD, MM, …) from the same registry is used instead — e.g. `Developments/SD/SD - ZSD_ORDER_CHECK.md`. Check the registry **before** creating any new folder — see the Pre-Create Normalization Check in `CLAUDE.md`.

Pages generated from ABAP source code (auto-documented legacy developments) carry `status: draft` and `tags: [ai-generated]` until an SME validates them.
