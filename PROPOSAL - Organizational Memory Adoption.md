# Change Proposal — Adopting Organizational-Memory Strategies

**Status:** Draft for curator review
**Date:** 2026-07-21
**Author:** Claude (session with Senthil Palanivelu)
**Decision owner:** Vault Curator
**Source:** Kirchdorfer et al., _Organizational Memory for Agentic Business Process Execution_, SAP Signavio, arXiv:2607.03228 (2026)

---

## Why this proposal

The paper defines an _organizational memory_ for LLM agents — "a shared, governed, and agent-consumable reference layer" — and derives nine architecture requirements (R1–R9). Its proof-of-concept measured policy-compliant agent behavior at **95% with curated structured memory vs. 80% with plain RAG over raw documents vs. 30% with no memory**. This vault already follows the winning design (curated typed pages, not document chunks). The paper's value to us is in the gaps it exposes and one failure mode it measured.

This vault's stated aim — a centralized knowledge base that coding agents and LLMs consume across delivery, pre-sales, modernization, and AI-assisted development — makes three requirements load-bearing: **R2** (agent-consumable units), **R3** (conflict detection), and **R5** (context-specific retrieval).

### Requirement coverage today

| Req | Meaning                            | Vault today                                                    | This proposal           |
| --- | ---------------------------------- | -------------------------------------------------------------- | ----------------------- |
| R1  | Integrate heterogeneous sources    | ✅ Ingest pipeline (PDF/DOCX/XLSX/VTT/ABAP/images)             | —                       |
| R2  | Agent-consumable, decomposed units | ⚠️ Page-granular; rules inside pages not addressable           | **CP-2**                |
| R3  | Conflict detection & consistency   | ❌ Dedup only; contradictions go undetected                    | **CP-4**                |
| R4  | Traceability to sources            | ✅ `source_files` + `raw/processed/` archive                   | —                       |
| R5  | Context-specific retrieval         | ⚠️ Index + folders; free-form tags limit precision             | **CP-1**                |
| R6  | Low-latency runtime access         | ✅ Query Mode: index first, smallest sufficient set            | —                       |
| R7  | Adaptive memory over time          | ⚠️ Update-over-create + promotion exist; no change propagation | **CP-5**                |
| R8  | Human governance & ownership       | ✅ Curator, `owner`, `ai-generated` + SME validation           | —                       |
| R9  | Scale across agents/processes      | ✅ One shared repo, multiple consumer types                    | **CP-6** widens content |

Each CP below contains the exact text to adopt, so items can be approved or struck individually.

---

## CP-1 — Controlled tag vocabulary (R5)

**Problem.** `tags:` is free-form (`[gotcha, bapi, commit, locking]`). Tag-based retrieval — "everything touching IDocs" — is unreliable because nothing prevents `bapi` / `bapis` / `BAPI-call` drift. The paper grounds every memory unit in a tag-based _Enterprise Domain Model_, deliberately chosen over a formal ontology because tags can grow incrementally (their §5.1).

**Change.** Extend `meta/entities.md` with a **Tag Vocabulary** section; tags used in frontmatter MUST come from it (same discipline as entity slugs: new tag → registry first, then use).

**Text to add to `meta/entities.md`:**

```markdown
## Tag Vocabulary

Tags in page frontmatter MUST come from this registry. New tag needed →
add it here first (with its category), then use it. Same rule as entity
slugs: never invent a second spelling.

| Tag               | Category        | Covers / aliases                           |
| ----------------- | --------------- | ------------------------------------------ |
| idoc              | technology      | IDocs, ALE, change pointers                |
| bapi              | technology      | BAPI calls, BAPI_* function modules        |
| cds               | technology      | CDS views, AMDP                            |
| enhancement       | technology      | user exits, BAdIs, enhancement spots       |
| batch-job         | technology      | SM36/SM37 background jobs                  |
| credit-management | business-object | credit blocks, exposure, VKM*              |
| sales-order       | business-object | VA01/VA02, order processing                |
| master-data       | business-object | BP, customer/vendor/material master        |
| performance       | quality         | runtime, SQL tuning                        |
| locking           | quality         | enqueue/dequeue, lock contention           |
| authorization     | quality         | auth checks, roles                         |
| estimation        | artifact-kind   | effort figures, calibration data           |
| code-review       | process         | review findings, quality gates             |
| transport         | process         | TR handling, cutover                       |
| wricef            | artifact-kind   | WRICEF-classified objects                  |
| ai-generated      | governance      | page not yet SME-validated (existing rule) |
```

Seed rows come from tags already in use; the curator prunes/extends at setup.

**Text to add to CLAUDE.md** (Frontmatter Schema section, after the schema block):

> **Tag discipline:** every value in `tags:` must exist in the Tag Vocabulary in `meta/entities.md`. A needed-but-missing tag is added to the registry first, then used. Free-form tags are treated like invented entity slugs — a normalization failure.

**Migration:** one pass over the ~30 existing pages to align tags (≈30 min). Low risk.

---

## CP-2 — Atomic rule structure in rule-like pages (R2)

**Problem.** The unit of storage is the page; the unit of _use_ by a coding agent is the rule. `Standard - ABAP Naming Conventions` holds many rules, but none can be individually linked, retrieved, superseded, or checked for conflicts. The paper's core design choice is the _process atom_: one rule per unit with **Applicability**, **Action**, and **Purpose** separated — explicitly because "without decomposition into self-contained units, individual rules cannot be addressed, compared, updated, or selectively retrieved" (R2). We adopt the structure _within_ pages — the page stays the file, rules become addressable heading-blocks — keeping governance page-granular (their reason for not decomposing further, §5.1).

**Change.** Rule-like page types (`standard`, `pattern`, `gotcha`, `troubleshooting`) structure each rule as its own `##` block:

```markdown
## {Short imperative rule name}

- **Applies to:** {scope: object types, module, release, conditions}
- **Does not apply to:** {explicit exclusions, if any}
- **Rule:** {the single concrete rule, constraint, or required behavior}
- **Why:** {rationale — what breaks or degrades without it}
- **Source:** {document / decision / incident it came from, if known}
```

One rule per block. Wikilinks may then target rules directly: `[[Standard - ABAP Naming Conventions#Global classes use ZCL_ prefix]]`.

**Text to add to CLAUDE.md** (new subsection under Page Types, after the Templates paragraph):

> ### Atomic Rule Structure (Rule-Like Pages)
>
> Pages of type `standard`, `pattern`, `gotcha`, and `troubleshooting` hold _rules_, and each rule must be individually addressable. Structure every rule as its own `##` heading with the fields **Applies to / Does not apply to / Rule / Why / Source** — one rule per block, never several rules prose-merged into one section. Wikilinks reference individual rules as `[[Page#Rule heading]]`. When a rule changes, edit its block and the page's `updated` date; when it is withdrawn, mark the block **Superseded** with a link to its replacement — do not silently delete it.

**Template impact:** `_Template-Standard.md`, `_Template-Pattern.md`, `_Template-Gotcha.md`, `_Template-Troubleshooting.md` gain the block structure above.

**Migration:** restructure the 3 existing standards pages (the largest is the ABAP Programming Guidelines) plus 1 pattern, 1 gotcha. Suggest doing this on next touch of each page rather than big-bang; the ingest pipeline applies the structure to all new pages immediately.

---

## CP-3 — Mandatory applicability scoping (paper's measured failure mode)

**Problem.** The paper's Memory agent's _remaining_ errors were over-restrictions "caused by an imprecisely extracted atom whose applicability scope is too broad" (§6.2). Our equivalent: a gotcha written scope-free ("always pass WAIT='X'") gets applied by an agent where it doesn't hold, or a pattern from ECC gets applied to S/4.

**Change.** Already embedded in CP-2's block format (**Applies to / Does not apply to**). This CP makes the field _mandatory rather than optional_ for Zone 03 pages, because intelligence pages travel furthest from their original context.

**Text to add to CLAUDE.md** (Quality Bar section, as test 5):

> 5. **Is the scope explicit?** Zone 03 pages (patterns, gotchas, troubleshooting) must state where the learning applies — system/release, module, and conditions — and, where known, where it does **not**. A scope-free rule is worse than no rule: an agent will apply it everywhere.

**Migration:** add scope lines to the existing gotcha and pattern (~10 min).

---

## CP-4 — Conflict detection at ingest (R3)

**Problem.** Deduplication Logic catches _duplicates_ ("decision page exists → update it") but not _contradictions_ ("new spec assumes RFC; standing decision mandates OData"). The paper's Global Curator explicitly checks each candidate against existing memory for conflicts and routes them to a human (§5.2). As pre-sales, delivery, and modernization all write into the vault, silent contradiction is the main consistency risk.

**Change.** Add a conflict check to the Ingestion Workflow between Extract (C) and Update (D), and a conflict-flag convention that needs no schema change.

**Text to add to CLAUDE.md** (new subsection in Ingestion Workflow, between C and D):

> ### C2. Conflict Check (before any update)
>
> Before creating or updating a page, compare each extracted decision, rule, or constraint against the standing pages it touches (the target page, its linked decisions, and applicable standards):
>
> - **Consistent** → proceed with the update.
> - **Refines** (narrows scope, adds a case) → update the existing page; note the refinement.
> - **Contradicts** → do NOT silently overwrite. Keep the standing page authoritative, add a conflict block to it, log the conflict, and add it to the workstream's Open-Questions page assigned to the curator:
>
> ```markdown
> > [!warning] CONFLICT — unresolved
> > {New source, date} states: {claim}.
> > This contradicts the standing text above.
> > Resolution owner: curator. Logged {date} in meta/log.md.
> ```
>
> A conflict is resolved only by a human decision — recorded as a Decision page (or a revision to the existing one), after which the conflict block is removed. The losing claim is noted in the Decision's rationale, not deleted from history.

**Migration:** none (forward-looking behavior).

---

## CP-5 — Change propagation on standards and decisions (R7)

**Problem.** R7's test case: "if the allowed threshold changes, all affected agents should follow the updated rule after a single change to the memory." The single-change part works here (pages link to standards rather than copying them) — but pages that _paraphrased_ the old rule go stale silently. The mandatory "decision → what it affects" links give us the affected-set for free; nothing mandates walking it.

**Text to add to CLAUDE.md** (Linking Rules section, at the end):

> **Change propagation:** when a `standard` or `decision` page changes materially (rule added, changed, or superseded), enumerate the pages that link to it, review each for staleness in the same session, and record the sweep in `meta/log.md` (`Propagated: [[X]] change → reviewed [[A]], [[B]]; updated [[B]]`). A standards change without a propagation sweep is an incomplete ingest.

**Migration:** none (forward-looking behavior).

---

## CP-6 — Two new page types: Component catalog and Proposals (R1/R9, project aim)

**Problem.** The project aim includes _standard components_ and _pre-sales proposals_; neither has a legal home, so today they'd be forced into ill-fitting types or dropped. A standard-component catalog is the highest-value content for AI-assisted development — it is what stops a coding agent reinventing (or mis-extending) a standard component. Proposals feed the estimation calibration loop from the pre-sales side.

**Change.** Two new types in the fixed schema (this is a schema change — explicitly curator territory):

| Type        | Zone / folder                    | Naming                                        | Purpose                                                                                                                             |
| ----------- | -------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `component` | `01-standards/components/`       | `Component - {Name}.md`                       | Reference record for a standard (SAP/Infor) component: what it does, extension points, known limitations, use-vs-customize guidance |
| `proposal`  | `02-workstreams/Proposals/{WS}/` | `{WS} - Proposal - {Topic} - {YYYY-MM-DD}.md` | Pre-sales artifact: scope, assumptions, per-item estimates; later linked to actuals                                                 |

**Template draft — `01-standards/components/_Template-Component.md`:**

```markdown
---
title: "Component - {Name}"
type: component
zone: 01-standards
status: evergreen
owner: ""
created: YYYY-MM-DD
updated: YYYY-MM-DD
workstream: ""
tags: []
source_files: []
---

# Component - {Name}

## What it does

{Business function in 2–4 sentences.}

## When to use it (vs. customize)

- **Use as-is when:** …
- **Extend when:** … (via which extension points)
- **Do not customize when:** …

## Extension points

| Point | Type | Notes |
| ----- | ---- | ----- |

## Known limitations

{Each limitation as an atomic block per CP-2 if rule-like.}

## Observed in

{[[wikilinks]] to developments/specs that used or extended it.}
```

**Template draft — `02-workstreams/Proposals/_Template-Proposal.md`:** mirrors `_Template-Estimation.md` plus **Assumptions**, **Out of scope**, and **Outcome** (won/lost/changed) sections; links forward to the Estimation and Development pages if the work is won.

**Migration:** none; new content only. Linking rules extend naturally (proposal → workstream; development → component it extends).

---

## Explicitly NOT adopted (with reasons)

- **Vector/embedding retrieval (their Retriever instantiation).** Their own evaluation shows curated structure beating RAG; for a file-tool-equipped LLM, index + controlled tags + wikilinks is sufficient and zero-maintenance. Revisit only if the vault grows to the point where grep-scale retrieval fails (thousands of pages).
- **Atom-granular files.** One file per rule would explode the file count and break page-level governance (`owner`, `status`, review). The paper itself stops decomposition at the level "domain experts rely on to govern memory" (§5.1); CP-2's heading-blocks achieve addressability inside page-granular governance.
- **Formal ontology / knowledge-graph database.** Their argument against it (upfront schema design, continuous ontology engineering) applies to us verbatim; the tag vocabulary + entity registry is the deliberate lightweight substitute.
- **Automated curator (their Global Curator as a service).** The ingest pipeline plays this role at ingest time (CP-4); a continuously-running consistency monitor is out of scope for now.

## Open decision for the curator

**Generalize vs. clone for Infor.** This proposal is written as amendments to the existing ABAP vault. The stated project aim (Infor knowledge repository — components, FS/TS, proposals, modernization) transfers the _architecture_ unchanged, but the taxonomy (WRICEF, IDoc/BAPI tags, module slugs) and the Code Ingestion Rule are SAP-native. Options: (a) generalize this constitution now, (b) keep this vault SAP-scoped and clone the amended constitution as the template for an Infor vault. Recommendation: **(b)** — prove the CP-1…CP-6 mechanics here where content already exists, then clone; a half-generalized constitution serves both audiences badly.

## Suggested rollout

1. **Week 1:** CP-1 (registry + tag pass) and CP-3 (scope lines on existing Zone 03 pages) — small, immediate retrieval gains.
2. **Week 1–2:** CP-4 and CP-5 adopted into CLAUDE.md — forward-looking, zero migration.
3. **On next touch / next ingest:** CP-2 restructuring of the three standards pages.
4. **When first content arrives:** CP-6 folders + templates.

**Acceptance test** (per the paper's method): pick 5 realistic agent questions ("what rules apply when I write a batch job that calls a BAPI?"), answer each from the vault before and after, and check the after-answer retrieves the complete applicable rule set — including cross-cutting rules — with correct scope.
