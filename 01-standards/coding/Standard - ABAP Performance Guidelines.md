---
title: "Standard - ABAP Performance Guidelines"
type: standard
zone: 01-standards
status: evergreen
owner: ""
created: 2026-08-27
updated: 2026-08-27
workstream: ""
tags: [performance, open-sql, hana, cds]
source_files: [ABAP_dev_standards.pdf]
---

# Standard - ABAP Performance Guidelines

Performance rules for custom ABAP, split into ECC (non-HANA database) guidance and S/4HANA (ABAP-on-HANA) guidance, plus the analysis tools used to verify performance. Analysis tools are most useful when run with production-like data volumes — development data may not surface bottlenecks.

## ECC Systems (Non-HANA database)

- Use ABAP inline declarations (ABAP 7.4).
- Use a primary key or secondary index in the database `SELECT` `WHERE` clause.
- Do not use `SELECT *` — mention field names explicitly and in the right order as defined in the table.
- Use `SELECT SINGLE`, not `SELECT ... ENDSELECT`.
- Check `SY-SUBRC = 0` after every table select.
- Avoid `SELECT ... ENDSELECT` — use `SELECT ... INTO TABLE`.
- Avoid `INTO CORRESPONDING` — define the table fields in the right sequence of selection (not needed if New Open SQL is used).
- In most cases inner joins are better than `FOR ALL ENTRIES` — use `INNER JOIN` wherever possible.
- Do not write `SELECT` statements inside a loop — use `FOR ALL ENTRIES`. Before using `FOR ALL ENTRIES`, check that (a) the driver internal table is **not empty** — if empty the statement selects ALL DB entries; and (b) the internal table is sorted by the fields used in the `WHERE` clause (faster selection).
- Do not use `SELECT DISTINCT` — instead select into an internal table, sort, and use `DELETE ADJACENT DUPLICATES`.
- No aggregate functions in the `SELECT` query — do all math on the application server (ECC guidance).
- No `ORDER BY` / `GROUP BY` in the `SELECT` query (ECC guidance).
- Avoid `OR` in the `WHERE` clause — even with key/index fields, the optimizer stops if the condition contains an `OR`. Repeat the key/index fields inside each `OR` branch instead.
- Delete from an internal table with `DELETE <itab> WHERE <field> = '0001'.` rather than looping and deleting.
- Method calls are more efficient than function modules — use or create classes wherever possible.
- Strictly try to use field symbols instead of work areas — field symbols are memory pointers and are faster to access.
- When reading a single record in an internal table, `READ TABLE WITH KEY` is not a direct read — sort by the key fields and use `READ TABLE WITH KEY ... BINARY SEARCH`.
- Moving data between internal tables: use `itab1[] = itab2[]`.
- Use `SORT <table> BY <field1> <field2>` instead of a bare `SORT <table>`.
- Count lines with `DESCRIBE TABLE <itab> LINES n` instead of a counter loop.
- Avoid nested loops — use the **parallel cursor** technique (find the index with a `READ ... BINARY SEARCH`, then loop the inner table `FROM l_index` and `EXIT` when the key no longer matches).
- Use `CASE` statements instead of multiple `IF` conditions — clearer and faster.
- Free internal tables / work areas / variables no longer used; clear the work area at the end of every `LOOP` pass.
- **Code cleanup** — remove dead (commented) code, unused constants, variables, work areas, and internal tables.
- Avoid looping over the same internal table more than once.
- Internal tables with header line are not allowed.

> ECC systems with ABAP 7.4 SP04 and above support ABAP CDS views — start using the code pushdown paradigm. ABAP CDS are database-independent and can be used irrespective of the database.

## S/4HANA Systems — ABAP on HANA

Code-to-data / code pushdown paradigm:

- **Transparent optimization** — improvements in the ABAP stack (FDA); direct benefit without adjustments.
- **New Open SQL (Code Push Down / Code-to-Data)** — move logic and calculations to the database.
- **CDS (Core Data Services) Views (ABAP CDS)** — database views used for data access.
- **ABAP Managed Database Procedures (AMDP)** — stored procedures.

New Open SQL supports: `CASE` expressions (simple and searched, nesting possible); aggregate functions with `GROUP BY` / `HAVING`; math/aggregate functions (`CEIL`, `ABS`, `FLOOR`, `ROUND`, `MIN`, `MAX`, `DIVISION`); `COALESCE( arg1, arg2 )` (returns arg1 unless null, else arg2); string expressions (`&&` concatenation, `CONCAT`, `REPLACE`, `SUBSTRING`, `LENGTH`); inline declarations (`INTO TABLE @DATA(...)`).

### ABAP CDS

- The Eclipse IDE with ABAP Development Tools (ADT) should be used to create ABAP CDS views.
- ABAP CDS views only support data **read**, not write/DML — only `SELECT`, no update/insert/delete on the table.
- The DDL Source name and the CDS Entity name should be the same; the SQL View name must be different from the CDS Entity/View.
- Annotations add semantic meaning to the data definition/metadata. CDS enhancements include expressions for calculations/queries, associations (path expressions replacing joins), and annotations enriching the model with domain-specific metadata.
- CDS is supported natively in both the ABAP and HANA platforms.

### Classic DDIC-based CDS Views vs CDS View Entity

- With ABAP release 7.55 a new type of CDS view exists: the **CDS view entity**.
- DDIC-based CDS views create a SQL/ABAP dictionary view in the backend upon activation — the annotation `@AbapCatalog.sqlViewName` is mandatory.
- In CDS view entities, an ABAP dictionary view is not created, so `@AbapCatalog.sqlViewName` is not required. Syntax is improved and some unused features are removed.
- **VDM (Virtual Data Models)** are primarily used in analytics.

## Analysis Tools

- **Runtime Analysis — transaction SAT** — analyze the performance of specific ABAP code.
- **ST05 — Performance Trace** — records database access, locking activities, and remote calls in a trace file; the SQL trace is particularly useful for analyzing database-access performance of a program/transaction.
- **Extended Syntax Check — transaction SLIN** — all developments must be checked with extended syntax check before releasing the transport; before transport to production it should display at least no errors.
- **Code Inspection / ABAP Test Cockpit (ATC)** — produces findings (errors and warnings to be corrected). Before releasing the transport, developers are encouraged to perform an ATC run to find and correct problems before the central run does.

## Related

- [[Standard - ABAP Programming Guidelines]]
- [[Process - Code Review]] — SLIN/ATC and runtime performance are review gates

## Linked from

- [[Process - Code Review]] (process)
- [[Standard - ABAP Naming Conventions]] (standard)
- [[Standard - ABAP Programming Guidelines]] (standard)
