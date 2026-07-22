---
title: "Standard - ABAP Performance Guidelines"
type: standard
zone: 01-standards
status: evergreen
owner: "TBD"
created: 2026-07-20
updated: 2026-07-21
workstream: ""
tags: [performance, hana, cds, open-sql]
source_files: ["ABAP Dev standards.pdf"]
---

# Standard — ABAP Performance Guidelines

Performance rules for custom ABAP, covering both ECC (non-HANA) and S/4HANA (ABAP on HANA). Source: *ABAP Development Standards* (author: Veda; v0.2 added the ABAP-on-HANA content). Companion to [[Standard - ABAP Programming Guidelines]] and [[Standard - ABAP Naming Conventions]].

## ECC (non-HANA database)

- Use **ABAP in-line declarations** (7.4) and the new Open SQL syntax.
- Use **primary key or secondary index** fields in the `WHERE` clause.
- **No `SELECT *`** — list field names explicitly, in table-defined order.
- Prefer `SELECT SINGLE`; avoid `SELECT … ENDSELECT` — use `SELECT INTO TABLE`.
- Check `SY-SUBRC = 0` after every table select.
- Avoid `INTO CORRESPONDING`; define table fields in selection sequence (unnecessary with New Open SQL).
- Prefer **INNER JOIN** over `FOR ALL ENTRIES` where possible.
- **No `SELECT` inside a LOOP** — use `FOR ALL ENTRIES`. Before `FOR ALL ENTRIES`: (a) ensure the driver table is **not empty** (empty → selects everything); (b) sort it by the `WHERE`-clause fields.
- Do **not** use `SELECT DISTINCT` — select into table, sort, `DELETE ADJACENT DUPLICATES`.
- **No aggregate functions** in the select on ECC — do the math on the application server.
- No `ORDER BY` / `GROUP BY` in the select query (ECC).
- Avoid `OR` in `WHERE` (optimizer stops). Rewrite so each branch lists all key/index fields, e.g. `(carrid = 'LH' AND cityfrom = 'FRANKFURT') OR (carrid = 'LH' AND cityfrom = 'NEWYORK')`.
- Delete from internal table with `DELETE <itab> WHERE …` — not a LOOP+DELETE.
- Prefer **method calls over function modules** — use/create classes.
- Use **field symbols** rather than work areas (memory pointers, faster).
- Single-record read: sort by key and use `READ TABLE … WITH KEY … BINARY SEARCH`.
- Copy tables with `itab1[] = itab2[]`.
- `SORT table BY <field1> <field2>` — not bare `SORT`.
- Count lines with `DESCRIBE TABLE <itab> LINES n` — not a LOOP counter.
- **Avoid nested loops** — use the **parallel cursor** technique (READ to find the index, then loop from that index, EXIT inner loop when the key no longer matches).
- Use `CASE` instead of multiple `IF` (clearer and faster).
- **FREE** internal tables/work areas/variables no longer used; `CLEAR` the work area at the end of each LOOP pass.
- **Remove dead code** (commented code), unused constants, variables, work areas, internal tables.
- Avoid looping the same internal table more than once.
- Internal tables **with header line are not allowed**.

## S/4HANA — ABAP on HANA (Code Push-Down / Code-to-Data)

From SAP ABAP 7.4 SP04+ CDS views are supported — adopt the **code push-down** paradigm. CDS is database-independent.

- **Transparent optimization** — improvements in the ABAP stack (FDA); benefit without adjustments.
- **New Open SQL** — move logic and calculations to the database.
- **CDS (Core Data Services) views** — database views for data access.
- **AMDP (ABAP Managed Database Procedures)** — stored procedures.

### New Open SQL features (examples)

- `CASE` expressions (simple and searched, nesting possible) with `AS <alias>` and inline `INTO TABLE @DATA(...)`.
- Aggregates with `GROUP BY` / `HAVING`: `COUNT( DISTINCT … )`, `SUM`, `AVG`, `MIN`, `MAX`.
- Math: `ceil`, `abs`, `floor`, `round`, `division( a, b, dec )`.
- `COALESCE( arg1, arg2 )` — returns `arg1` unless NULL, else `arg2`.
- String expressions: concatenation with `&&`; `concat`, `replace`, `substring`, `length`.

### ABAP CDS

- Build CDS views in the **Eclipse ADT** (ABAP Development Tools).
- CDS supports **read only** — no INSERT/UPDATE/DELETE.
- DDL source name = CDS entity name; the **SQL view name must be different**.
- Annotations add semantic meaning (expressions, associations replacing joins with path expressions, domain metadata).
- **DDIC-based CDS view** creates a SQL/dictionary view on activation → `@AbapCatalog.sqlViewName` is mandatory. **CDS view entity** (from 7.55) does **not** create a dictionary view → `@AbapCatalog.sqlViewName` not required.
- **VDM (Virtual Data Models)** — primarily for analytics.

## Analysis Tools

Most useful with production-like data volumes.

- **SAT** — Runtime Analysis for specific ABAP code.
- **ST05** — Performance/SQL trace (DB access, locking, RFC).
- **SLIN** — Extended syntax check; must show **no errors** before releasing a transport.
- **ATC (ABAP Test Cockpit)** — run before releasing so issues are fixed before the Central run.

## Related

- [[Standard - ABAP Programming Guidelines]]
- [[Standard - ABAP Naming Conventions]]
- [[Process - Code Review]]

## Linked from

- [[INT - Vedakala]] (stakeholder)
- [[INT - ZADUSR_SYNC]] (development)
- [[Process - Code Review]] (process)
- [[Standard - ABAP Naming Conventions]] (standard)
- [[Standard - ABAP Programming Guidelines]] (standard)
