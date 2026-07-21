# CLAUDE.md — ABAP Vault Operating Constitution

**Version:** 1.0 **Status:** Draft for Review
**Maintained By:** Vault Curator (TBD — assign one named owner)

---

## Purpose

This vault is the canonical memory of the ABAP delivery project: its standards, decisions, meeting outcomes, developments, and lessons learned.

It exists to:

- keep every workstream's decisions and open questions findable in seconds
- prevent the same question being answered twice in different ways
- compound reusable patterns, gotchas, and runbooks across workstreams
- preserve durable team knowledge through staffing changes and handovers
- reduce repeated rework across modules, developments, and releases

**This vault is not a dumping ground for raw notes. It is a curated, linked, durable knowledge system.**

---

## Complete Folder Structure

```
abap-vault/
│
├── 01-standards/                    [Stable reference — changes rarely]
│   ├── coding/
│   │   ├── _Template-Standard.md
│   │   └── Standard - ABAP Naming Conventions.md
│   ├── architecture/
│   │   ├── _Template-Architecture.md
│   │   └── Architecture - Clean Core Principles.md
│   └── landscape/
│       ├── _Template-Landscape.md
│       └── Landscape - System Overview.md
│
├── 02-workstreams/                  [Active work — artifact-type folders with workstream subfolders]
│   ├── Workstreams/
│   │   ├── _Template-Workstream.md
│   │   ├── OTC.md
│   │   └── [more workstreams]
│   ├── Stakeholders/
│   │   ├── _Template-Stakeholder.md
│   │   ├── OTC/
│   │   │   └── OTC - Firstname Lastname.md
│   │   └── [more workstreams]
│   ├── Meetings/
│   │   ├── _Template-Meeting.md
│   │   ├── OTC/
│   │   │   └── OTC - Design Review - 2026-07-15.md
│   │   └── [more workstreams]
│   ├── Decisions/
│   │   ├── _Template-Decision.md
│   │   ├── OTC/
│   │   │   └── Decision - OTC - Custom BAPI approach - 2026-07-15.md
│   │   └── [more workstreams]
│   ├── Specs/
│   │   ├── _Template-Spec.md
│   │   ├── OTC/
│   │   │   └── OTC - Spec - Sales Order Enhancement.md
│   │   └── [more workstreams]
│   ├── Developments/
│   │   ├── _Template-Development.md
│   │   ├── OTC/
│   │   │   └── OTC - E-001 - Sales Order User Exit.md
│   │   ├── SD/                      [Module slug — legacy objects not tied to a workstream]
│   │   │   └── SD - ZSD_ORDER_CHECK.md
│   │   └── [more workstreams]
│   ├── Estimations/
│   │   ├── _Template-Estimation.md
│   │   ├── OTC/
│   │   │   └── OTC - Estimation - Wave 2 WRICEF list - 2026-07-20.md
│   │   └── [more workstreams]
│   ├── Issues/
│   │   ├── _Template-Issue.md
│   │   ├── OTC/
│   │   │   └── OTC - Issue - IDoc failures in QAS - 2026-07-20.md
│   │   └── [more workstreams]
│   └── Open-Questions/
│       ├── _Template-OpenQuestions.md
│       ├── OTC.md                   [One rolling page per workstream]
│       └── [more workstreams]
│
├── 03-intelligence/                 [Reusable learnings — what we've seen twice or more]
│   ├── patterns/
│   │   ├── _Template-Pattern.md
│   │   └── Pattern - IDoc error handling.md
│   ├── lessons-learned/
│   │   ├── _Template-LessonsLearned.md
│   │   └── Lessons - OTC Go-Live - 2026.md
│   ├── gotchas/
│   │   ├── _Template-Gotcha.md
│   │   └── Gotcha - BAPI_TRANSACTION_COMMIT wait flag.md
│   ├── troubleshooting/
│   │   ├── _Template-Troubleshooting.md
│   │   └── Troubleshooting - IDoc failures.md
│   └── faqs/
│       ├── technical/
│       │   └── _Template-FAQ.md
│       ├── process-and-transport/
│       │   └── _Template-FAQ.md
│       ├── landscape-and-access/
│       │   └── _Template-FAQ.md
│       └── testing/
│           └── _Template-FAQ.md
│
├── 04-internal/                     [Team operations — internal only]
│   ├── contacts/
│   │   ├── _Template-Contact.md
│   │   └── POC - Workstream Leads.md
│   ├── onboarding/
│   │   └── Onboarding - New Team Member.md
│   ├── processes/
│   │   ├── _Template-Process.md
│   │   └── Process - Code Review.md
│   └── runbooks/
│       ├── _Template-Runbook.md
│       └── Runbook - Transport release.md
│
├── meta/                            [System files — pipeline depends on these]
│   ├── index.md                     [Master navigation, updated every ingest]
│   ├── log.md                       [Append-only ingest history]
│   ├── inbox.md                     [Dedup table of processed files]
│   ├── entities.md                  [Canonical names + aliases registry]
│   └── conventions.md               [Human-readable conventions reference]
│
├── raw/                             [Processing pipeline — pipeline depends on these]
│   ├── inbox/                       [Unprocessed drops land here]
│   └── processed/                   [Archive after ingestion]
│
└── CLAUDE.md                        [This file]
```

---

## Zones (4 Operating Zones + Point-of-Use Templates)

1. **`01-standards/`** — Stable reference. Coding standards, naming conventions, architecture principles, system landscape documentation. Changes rarely; treated as evergreen.

2. **`02-workstreams/`** — Active delivery work. Everything tied to a specific workstream: workstream overview, stakeholders, meetings, decisions, specs (FS + TS), developments (WRICEF objects), effort estimations, issues, and open questions. Each artifact-type folder contains a location-specific template.

3. **`03-intelligence/`** — Reusable learnings. Patterns seen twice or more, lessons learned, gotchas, troubleshooting guides, and FAQs. What the team has learned that outlives any single workstream.

4. **`04-internal/`** — Team operations: contacts, onboarding, processes, runbooks. Internal-only.

Shared support folders:

- **`raw/`** — Unprocessed source material (`inbox/` for drops, `processed/` for the archive)
- **`meta/`** — Index, log, dedup table, entity registry, conventions

Keep `meta/` and `raw/` exactly as-is — the ingestion pipeline code depends on them.

---

## Core Behavior Rules

1. **Update existing pages over creating duplicates.** Always check first.
2. **Prefer linked durable notes over standalone summaries.**
3. **Treat meetings as source material, not final artifacts.**
4. **Every meaningful meeting must update at least one durable page.**
5. **Repeated learnings from workstreams push into `03-intelligence/`.**
6. **Internal knowledge is written for reuse, not only for the original context.**
7. **Avoid vague notes, vague titles, vague summaries.**
8. **This vault remains hostile to dead notes.**
9. **Never create floating pages.** Every new page links upward to a parent.
10. **Update order matters.** See Ingestion Workflow.
11. **Frontmatter is mandatory and fixed.** Every page uses exactly the schema defined below. No new fields. No omissions.
12. **Wikilinks are mandatory.** Every page links to at least one related page using `[[wikilinks]]`.

---

## What Counts as Durable Knowledge

**Durable knowledge includes:**

- Decisions with rationale (why we chose a custom BAPI over a standard one)
- Standards and conventions the team has agreed to follow
- Stakeholder context: who owns what, concerns, escalation paths
- Functional and technical spec content that survives the meeting it came from
- Development records: what was built, why, where it lives, known limitations
- Effort estimates AND actuals with variance reasons — the calibration loop that makes future estimates quotable
- Object dependencies: what a development depends on and what depends on it
- Functional summaries of legacy code (marked `ai-generated` until SME-validated)
- Architecture tradeoffs and constraints (landscape, clean core, performance)
- Root causes of issues, and how they were resolved
- Diagnostic paths that resolved the same problem class more than once
- Reusable patterns (anything appearing a 2nd time)
- Gotchas: non-obvious SAP behavior that cost someone hours
- Questions clients or the team ask repeatedly

**Non-durable material includes:**

- Temporary brainstorm fragments with no synthesis
- One-off logistical chatter (scheduling, availability)
- Raw meeting transcripts with no extraction
- Duplicate versions of the same conclusion
- Generic "meeting notes" with no linked updates
- Unvalidated approaches (wait until proven on 2+ objects or workstreams)

---

## Page Types

### Zone 01: Standards

- **`standard`** — A coding or naming standard the team follows. **Folder:** `coding/`
- **`architecture`** — An architecture principle or documented tradeoff. **Folder:** `architecture/`
- **`landscape`** — System landscape documentation: systems, clients, transport routes. **Folder:** `landscape/`

### Zone 02: Workstreams (9 Artifact Types with Workstream Subfolders)

- **`workstream`** — Workstream overview: scope, status, key objects, active threads, next actions. **Folder:** `Workstreams/`
- **`stakeholder`** — Individual: role, responsibilities, concerns, how they respond, current asks. **Folder:** `Stakeholders/{WS}/`
- **`meeting`** — Touchpoint: what we learned, decisions, asks, open questions. **Folder:** `Meetings/{WS}/`
- **`decision`** — Design/scope/approach decision with rationale and date. **Folder:** `Decisions/{WS}/`
- **`spec`** — Functional or technical specification content in durable form. **Folder:** `Specs/{WS}/`
- **`development`** — A WRICEF object record: what it does, where it lives, dependencies, complexity, effort (estimated vs actual), status. **Folder:** `Developments/{WS}/`
- **`estimation`** — A dated effort-estimation exercise: scope, assumptions, per-object estimates, and (later) actuals. **Folder:** `Estimations/{WS}/`
- **`issue`** — Defect or blocker: symptom, root cause, resolution, affected objects. **Folder:** `Issues/{WS}/`
- **`open-questions`** — One rolling page per workstream tracking unresolved questions with owners. **Folder:** `Open-Questions/`

### Zone 03: Intelligence (5 Subfolders)

- **`pattern`** — Repeated insight/approach appearing in 2+ workstreams or objects. **Folder:** `patterns/`
- **`lessons-learned`** — Distilled learnings from a phase, go-live, or workstream. **Folder:** `lessons-learned/`
- **`gotcha`** — Non-obvious behavior that cost real time; written so nobody pays twice. **Folder:** `gotchas/`
- **`troubleshooting`** — Curated diagnostic guide for a recurring problem area: symptoms → checks → causes → fixes. The layer above individual Issues and gotchas. **Folder:** `troubleshooting/`
- **`faq`** — Questions asked repeatedly, answered and unanswered, organized by topic. **Folder:** `faqs/{topic}/`

### Zone 04: Internal Operations

- **`contact`** — POC directory: who owns what workstream, module, or system. **Folder:** `contacts/`
- **`onboarding`** — How a new team member gets productive. **Folder:** `onboarding/`
- **`process`** — Step-by-step team process with checklist and quality gates. **Folder:** `processes/`
- **`runbook`** — Operational step-by-step for recurring moments (transport release, cutover, hypercare). **Folder:** `runbooks/`

### Templates (Location-Specific, Not Centralized)

**Templates are embedded in every folder where pages get created**, named `_Template-{Type}.md`. They are visible at the point of use — both humans and the AI see them when entering the folder. Do not create a centralized template zone.

---

## Naming Rules (Strict — Deduplication depends on these)

### Zone 01 — Standards

| Type           | Pattern                                 | Example                                                |
| -------------- | --------------------------------------- | ------------------------------------------------------ |
| `standard`     | `coding/Standard - {Name}.md`           | `coding/Standard - ABAP Naming Conventions.md`         |
| `architecture` | `architecture/Architecture - {Name}.md` | `architecture/Architecture - Clean Core Principles.md` |
| `landscape`    | `landscape/Landscape - {Name}.md`       | `landscape/Landscape - System Overview.md`             |

### Zone 02 — Workstreams (Artifact-type folders with workstream subfolders)

`{WS}` is the canonical workstream slug from `meta/entities.md` (e.g. `OTC`, `P2P`, `RTR`).

**Module-slug rule for legacy objects:** For objects not tied to any active workstream (typically legacy custom developments being documented after the fact), `{WS}` may instead be a canonical **module slug** from the registry (e.g. `SD`, `MM`, `FI`). Example: `Developments/SD/SD - ZSD_ORDER_CHECK.md` with `workstream: SD` in the frontmatter. Never invent a third kind of slug — workstream or module, both from `meta/entities.md`.

| Type                   | Pattern                                                          | Example                                                                 |
| ---------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `workstream`           | `Workstreams/{WS}.md`                                            | `Workstreams/OTC.md`                                                    |
| `stakeholder`          | `Stakeholders/{WS}/{WS} - {Full Name}.md`                        | `Stakeholders/OTC/OTC - Anna Larsen.md`                                 |
| `meeting`              | `Meetings/{WS}/{WS} - {Topic} - {YYYY-MM-DD}.md`                 | `Meetings/OTC/OTC - Design Review - 2026-07-15.md`                      |
| `decision`             | `Decisions/{WS}/Decision - {WS} - {Topic} - {YYYY-MM-DD}.md`     | `Decisions/OTC/Decision - OTC - Custom BAPI approach - 2026-07-15.md`   |
| `spec`                 | `Specs/{WS}/{WS} - Spec - {Object or Topic}.md`                  | `Specs/OTC/OTC - Spec - Sales Order Enhancement.md`                     |
| `development`          | `Developments/{WS}/{WS} - {ID} - {Object Name}.md`               | `Developments/OTC/OTC - E-001 - Sales Order User Exit.md`               |
| `development` (legacy) | `Developments/{Module}/{Module} - {Object Name}.md`              | `Developments/SD/SD - ZSD_ORDER_CHECK.md`                               |
| `estimation`           | `Estimations/{WS}/{WS} - Estimation - {Topic} - {YYYY-MM-DD}.md` | `Estimations/OTC/OTC - Estimation - Wave 2 WRICEF list - 2026-07-20.md` |
| `issue`                | `Issues/{WS}/{WS} - Issue - {Topic} - {YYYY-MM-DD}.md`           | `Issues/OTC/OTC - Issue - IDoc failures in QAS - 2026-07-20.md`         |
| `open-questions`       | `Open-Questions/{WS}.md`                                         | `Open-Questions/OTC.md`                                                 |

### Zone 03 — Intelligence

| Type              | Pattern                                           | Example                                                 |
| ----------------- | ------------------------------------------------- | ------------------------------------------------------- |
| `pattern`         | `patterns/Pattern - {Name}.md`                    | `patterns/Pattern - IDoc error handling.md`             |
| `lessons-learned` | `lessons-learned/Lessons - {Context} - {Year}.md` | `lessons-learned/Lessons - OTC Go-Live - 2026.md`       |
| `gotcha`          | `gotchas/Gotcha - {Name}.md`                      | `gotchas/Gotcha - BAPI_TRANSACTION_COMMIT wait flag.md` |
| `troubleshooting` | `troubleshooting/Troubleshooting - {Area}.md`     | `troubleshooting/Troubleshooting - IDoc failures.md`    |
| `faq`             | `faqs/{topic}/FAQ - {Topic}.md`                   | `faqs/technical/FAQ - RFC vs OData for integrations.md` |

### Zone 04 — Internal Operations

| Type         | Pattern                              | Example                                      |
| ------------ | ------------------------------------ | -------------------------------------------- |
| `contact`    | `contacts/POC - {Scope}.md`          | `contacts/POC - Workstream Leads.md`         |
| `onboarding` | `onboarding/Onboarding - {Topic}.md` | `onboarding/Onboarding - New Team Member.md` |
| `process`    | `processes/Process - {Name}.md`      | `processes/Process - Code Review.md`         |
| `runbook`    | `runbooks/Runbook - {Name}.md`       | `runbooks/Runbook - Transport release.md`    |

---

## Frontmatter Schema (Mandatory, Fixed)

Every page MUST use exactly this schema. No exceptions.

```yaml
---
title: ""
type:
  "" # standard, architecture, landscape, workstream, stakeholder,
  # meeting, decision, spec, development, estimation, issue, open-questions,
  # pattern, lessons-learned, gotcha, troubleshooting, faq,
  # contact, onboarding, process, runbook
zone: "" # 01-standards, 02-workstreams, 03-intelligence, 04-internal
status: active # active | draft | parked | archived | resolved | evergreen
owner: "" # Person responsible
created: YYYY-MM-DD
updated: YYYY-MM-DD
workstream: "" # Canonical workstream OR module slug if applicable (OTC, P2P, SD, ...)
tags: [] # Controlled vocabulary — see Tag Discipline below. Pages generated from source code MUST carry the ai-generated tag
source_files: [] # Raw files ingested into this page
---
```

### Tag Discipline (Controlled Vocabulary)

Every value in `tags:` MUST exist in the **Tag Vocabulary** section of `meta/entities.md`. A needed-but-missing tag is added to the registry first (with its category), then used. Free-form tags are treated like invented entity slugs — a normalization failure.

Tags are **domain tags only**: they ground the page in what it is _about_ (technology, business object, quality concern, process, role, phase). Never echo into `tags:` what other frontmatter fields already say — no `type:` echoes (`spec`, `gotcha`, `stakeholder`, …) and no `workstream:` echoes (`otc`, `int`, …). Retrieval filters on `type:` and `workstream:` directly; tags carry the dimension those fields don't.

### Status Values

- **`active`** — Current, being worked on
- **`draft`** — Not yet ready for team reference
- **`parked`** — Paused, may resume
- **`archived`** — No longer relevant, kept for reference (never delete pages — archive them)
- **`resolved`** — For issues and decisions that are closed
- **`evergreen`** — Reference material (standards, patterns, runbooks)

---

## Path Discipline (Strict Enforcement)

**Every page starts with its zone folder. No exceptions.**

| Zone            | Path Pattern                                   | Example                                                                              |
| --------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------ |
| 01-standards    | `01-standards/{Category}/{File}.md`            | `01-standards/coding/Standard - ABAP Naming Conventions.md`                          |
| 02-workstreams  | `02-workstreams/{ArtifactType}/{WS}/{File}.md` | `02-workstreams/Decisions/OTC/Decision - OTC - Custom BAPI approach - 2026-07-15.md` |
| 03-intelligence | `03-intelligence/{Subfolder}/{File}.md`        | `03-intelligence/patterns/Pattern - IDoc error handling.md`                          |
| 04-internal     | `04-internal/{Subfolder}/{File}.md`            | `04-internal/runbooks/Runbook - Transport release.md`                                |

**Why this structure:**

- **Artifact-type browsing:** "Show me all decisions" = `02-workstreams/Decisions/`
- **Workstream-specific browsing:** "Show me all OTC work" = `Decisions/OTC/`, `Meetings/OTC/`, `Developments/OTC/`
- **Path discipline prevents duplicates** — one legal home per page type
- **Natural linking:** Development pages in `Developments/OTC/` link to their spec in `Specs/OTC/` and decisions in `Decisions/OTC/`

Never write into a folder that is not listed above. If a page doesn't fit any legal path, it probably isn't durable knowledge — append to an existing page instead.

---

## Linking Rules

Every durable page links:

- **Upward** to its parent (stakeholder → workstream, development → spec, issue → development)
- **Sideways** to related pages (decision → pattern, development → standard it follows)
- **Forward** to next actions or dependent notes (decision → affected developments, issue → resulting gotcha)

Use `[[wikilinks]]` for all internal references.

### Mandatory Link Patterns

- **Everything in Zone 02 → its workstream page.** Every meeting, decision, spec, development, and issue links to `[[{WS}]]`.
- **Zone 02 → Zone 01:** Developments and specs link to the standards they follow.
- **Zone 02 → Zone 03:** Decisions and issues link to relevant patterns and gotchas.
- **Zone 03 ↔ Zone 02:** Patterns link to every workstream/object where they were observed. Lessons link back to the workstream they came from.
- **Decision → what it affects:** Every decision links to the specs and developments it changes.
- **Issue → root cause artifacts:** Resolved issues link to the gotcha or pattern they produced, if any.

---

## Ingestion Workflow

When new raw material appears in `raw/inbox/`:

### A. Capture

Files land in `raw/inbox/`. After processing they move to `raw/processed/`.

### B. Triage

For each item, decide:

- **Workstream-specific?** (meeting, spec, decision, defect) → Zone 02
- **Reusable learning?** (pattern, gotcha, lesson) → Zone 03
- **Standard or landscape documentation?** → Zone 01
- **Team operations?** (process, runbook, contacts) → Zone 04
- **System/process chatter with no durable content?** → Log only, do not create pages

### C. Extract

Pull only these from any file:

- Durable facts
- Decisions with rationale
- Open questions (with owner if determinable)
- Technical constraints and tradeoffs
- Stakeholder signals (concerns, asks, escalations)
- Development details (objects, transports, dependencies)
- Root causes and resolutions
- Reusable patterns (anything appearing a 2nd time)
- Applicable standards (which conventions the content touches)

**FAQ Extraction Rule (mandatory for meeting transcripts and email chains):**
Scan for any question asked by the client, a functional consultant, or a team member. For each question found:

- Classify into one of the 4 FAQ subfolders: `technical/`, `process-and-transport/`, `landscape-and-access/`, or `testing/`
- If the question was **answered in-session** → append to the relevant FAQ page under `## Answered Questions` with attribution (asker, date, source meeting link)
- If the question was **not answered** → append to `## Unanswered Questions` table with the same attribution and an owner if determinable, AND add it to that workstream's `Open-Questions/{WS}.md`
- If the same question already exists → add the new asker/context to the `Also asked by` field (repeat signal — candidate for promotion)

### C2. Conflict Check (Before Any Update)

Deduplication catches duplicates; this step catches **contradictions**. Before creating or updating a page, compare each extracted decision, rule, or constraint against the standing pages it touches (the target page, its linked decisions, and applicable standards):

- **Consistent** → proceed with the update.
- **Refines** (narrows scope, adds a case) → update the existing page; note the refinement.
- **Contradicts** → do NOT silently overwrite. Keep the standing page authoritative, add a conflict block to it directly below the contradicted statement, log the conflict in `meta/log.md`, and add it to the workstream's `Open-Questions/{WS}.md` with the curator as owner:

```markdown
> [!warning] CONFLICT — unresolved
> {New source, date} states: {claim}.
> This contradicts the standing text above.
> Resolution owner: curator. Logged {date} in meta/log.md.
```

A conflict is resolved only by a human decision — recorded as a Decision page (or a revision to the existing one), after which the conflict block is removed. The losing claim is noted in the Decision's rationale, not deleted from history.

### D. Update — Order Matters (Non-Negotiable)

**For Zone 02 (Workstreams):**

1. **Workstream** — Does `Workstreams/{WS}.md` exist? Update or create it first.
2. **Stakeholder** — Any people mentioned? Create/update their pages.
3. **Meeting/Spec** — Extract as a specific artifact if it contains new information.
4. **Decision** — Any approach, scope, or design decision? Create a decision page.
5. **Development** — Any object built or changed? Create/update its record (including complexity and effort fields).
6. **Estimation** — Any effort estimate given or actuals confirmed? Create/update the estimation page and sync the effort fields on the affected Development records.
7. **Issue** — Any defect or blocker? Create/update, link to affected developments.
8. **Open Questions** — Update the workstream's rolling `Open-Questions/{WS}.md`.
9. **Promote to Intelligence** — Anything reusable across 2+ contexts goes to Zone 03.

**For Zone 03 (Intelligence):**

1. **Pattern** (if 2+ occurrences) — Create or update, add the new occurrence.
2. **Gotcha** (if non-obvious behavior cost real time) — Create or update.
3. **Troubleshooting guide** (if 2+ resolved Issues share a diagnostic path) — Create or update, link the source Issues.
4. **Lessons** (at phase end or go-live) — Create with metrics and specifics.
5. Link back to every Zone 02 page where the learning was observed.

**Floating summaries are forbidden.** If you cannot link a new page upward to a parent, do not create it. Append to an existing page instead.

### E. Log

Append one entry to `meta/log.md`:

```
- 2026-07-15: Ingested OTC design review transcript. Updated [[OTC]], [[OTC - Anna Larsen]]. Created [[Decision - OTC - Custom BAPI approach - 2026-07-15]]. Open question: performance impact on VA01 — added to [[Open-Questions/OTC]].
```

### F. Commit

Single commit per ingest:

```
ingest: {Workstream or Theme} - {Document Type} - {date}
```

Examples:

- `ingest: OTC - Design Review Transcript - 2026-07-15`
- `ingest: Pattern - IDoc error handling - 2026-07-20`

---

## Meeting Conversion Rule

A meeting note is only useful if it results in at least one of:

- Updated workstream context
- Updated stakeholder context
- Updated spec or development record
- A new decision page
- An updated open-questions page
- A new issue record
- A new pattern or gotcha

**Otherwise the meeting remains source material only.** Do not create a meeting note that is just a summary. Capture extracts in the parent pages.

---

## Code Ingestion Rule (ABAP Source Files)

When the ingested file is ABAP source code (program, class, function module, CDS view, enhancement — typically `.abap` or `.txt` code exports), the goal is to reconstruct the knowledge the original developer never wrote down:

1. **Create/update a Spec page** — `Specs/{WS}/{WS} - Spec - {Object Name}.md`:
   - **Functional summary** — what the object does in business terms, and the business process it serves
   - **Technical specification** — structure, key logic, selection criteria, error handling
   - **Impacted business processes** — which processes break if this object misbehaves
2. **Create/update a Development record** — `Developments/{WS}/{WS} - {Object Name}.md` with object details and a Dependencies section listing every referenced object (tables, classes, function modules, CDS views, enhancements) as `[[wikilinks]]` — link them even if their pages don't exist yet.
3. **Mark inference as inference.** The business rationale is _reconstructed from code_, not retrieved from the author. Generated pages MUST carry `status: draft` and `tags: [ai-generated]` until a human SME validates them (validation = remove the tag, set status appropriately).
4. **Slug selection:** use the owning workstream if determinable; otherwise the module slug per the module-slug rule (`Developments/SD/…`).
5. **Dependency extracts** (TADIR, where-used lists, CDS dependency exports dropped as CSV/text): update the Dependencies sections of the affected object pages — do not create standalone dependency dump pages.

**A code drop with no extractable purpose (generated code, empty shells) is logged, not paged.**

---

## Pattern Promotion Rule

Whenever the same approach, error, workaround, objection, or tradeoff appears in more than one context, promote it.

**Promotion threshold:**

- Across 2+ workstreams → `Pattern - {Name}.md` in Zone 03
- Across 2+ developments in one workstream → `Pattern - {Name}.md` in Zone 03
- A question asked a 2nd time → FAQ entry in Zone 03
- Non-obvious behavior that cost someone hours → `Gotcha - {Name}.md` immediately (gotchas don't wait for a 2nd occurrence)
- 2+ resolved Issues sharing the same diagnostic path → `Troubleshooting - {Area}.md` in Zone 03, linking every source Issue
- Mentioned often enough that someone will ask for it again → promote

**Patterns must link to:** every workstream/development where observed, applicable standards, related gotchas.

---

## Quality Bar

Every durable page must pass this test:

1. **Can another teammate understand it quickly?** No insider context required.
2. **Can the model reuse it without asking for hidden context?** Self-contained.
3. **Does it link to the right neighbors?** Upward to parent, sideways to related.
4. **Is it better than a random meeting summary?** Synthesized, not transcribed.
5. **Is the scope explicit?** Zone 03 pages (patterns, gotchas, troubleshooting) must state where the learning applies — system/release, module, and conditions — and, where known, where it does **not**. A scope-free rule is worse than no rule: an agent will apply it everywhere.

If any answer is no, the page is not ready. Append to an existing page or hold as draft.

---

## Handover Criterion

A workstream is handover-ready only when these exist:

✅ Workstream page with current scope and status
✅ Stakeholder page(s)
✅ All decisions recorded with rationale
✅ Development records for every custom object
✅ Current open-questions page with owners
✅ Latest meeting note (if recent client-facing work)
✅ Clear next actions

Without all of these, the vault is not doing its job for that workstream.

---

## Team Operating Model

### Roles

**1. Curator-Owner** (named person — assign in `04-internal/contacts/`)
Responsible for: schema changes, quality bar, deciding what becomes a pattern, merging duplicates, watching for failed pipeline runs, holding the API key.

**2. Contributors** (whole team)
Drop raw material into the OneDrive inbox. Review pages the AI wrote from their documents. Update pages they own.

**3. Intelligence Lead** (rotates)
Responsible for: moving repeated learnings into Zone 03, promoting FAQs and gotchas, improving template quality.

### Minimum Team Rules

- Every active workstream must have an owner
- Every important meeting must update at least one durable page
- Every reusable learning ends up in Zone 03
- **Every completed development gets its actual effort recorded** — estimates without actuals never become an estimation baseline
- **Every `ai-generated` page gets SME review** — validated pages lose the tag; wrong ones get corrected, not deleted
- Raw material with no follow-through is not "knowledge work"
- The vault is part of the work, not admin after the work
- **Never delete pages** — set `status: archived` instead
- **Don't edit CLAUDE.md casually** — changes affect every future ingestion; they go through the curator
- **Files enter only through the drop-zone** — no pasting raw material straight into wiki folders

### Weekly Rhythm (20 minutes)

- Check the Actions tab for failed ingestion runs
- Tighten stale workstream and open-questions pages
- Ask: "What repeated this week that should become a pattern, gotcha, or FAQ?"

### Monthly Rhythm (45 minutes)

- Archive dead notes
- Merge duplicates, feed name variants into `meta/entities.md`
- Promote top 1–3 patterns
- Review whether the intelligence layer is being used

---

## Deduplication Logic

**File-level dedup:**

- Check filename in `meta/inbox.md`
- If exact match found, skip re-processing
- If similar but different (v1 vs v2), re-process and update existing pages

**Page-level dedup:**

- If a workstream/stakeholder/development page exists, **append or update** — never duplicate
- If a pattern page exists, add the new occurrence and example
- If a decision on the same topic exists, update it and note the revision — don't create a competing decision page
- If an FAQ exists, add the new asker to `Also asked by`

---

## Pre-Create Normalization Check (Mandatory)

**Before creating any new workstream folder, workstream file, stakeholder folder, or development record**, you MUST run this check. Skipping it creates the exact duplicates this vault was designed to prevent.

### Step 1 — Read the Entity Registry

Read `meta/entities.md`. It is the canonical source of truth for workstream names, SAP module names, system names, and vendor/partner names — with their aliases.

### Step 2 — Normalize the name from the document

Apply these transformations to the name found in the source document, then compare against all aliases in the registry:

| Transformation                              | Example                                                    |
| ------------------------------------------- | ---------------------------------------------------------- |
| Lowercase everything                        | `Order To Cash` → `order to cash`                          |
| Replace special chars (ø→o, ü→u, é→e, etc.) | `Müller GmbH` → `muller gmbh`                              |
| Replace `&` with `and`                      | `S&D` → `s and d`                                          |
| Strip punctuation (`.`, `'`, `-`, `/`)      | `O2C / OTC` → `o2c otc`                                    |
| Collapse whitespace                         | `Order  to  Cash` → `order to cash`                        |
| Check abbreviations                         | `O2C`, `OTC`, `SD-Sales` → check if they are known aliases |

### Step 3 — Decision

| Match result                                                            | Action                                                                                   |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Exact alias match**                                                   | Use the canonical slug. Do not create a new file or folder.                              |
| **High-confidence fuzzy match** (same core words, different formatting) | Use the canonical slug. Add the new alias variant to `meta/entities.md` for future runs. |
| **No match found**                                                      | This is a genuinely new entity. Add it to `meta/entities.md` first, then create files.   |
| **Uncertain**                                                           | Err toward matching an existing entity. When in doubt, treat as existing.                |

### Step 4 — File naming after normalization

Once the canonical slug is confirmed, use it everywhere:

- Workstream file: `02-workstreams/Workstreams/{WS}.md`
- Artifact subfolders: `02-workstreams/Meetings/{WS}/`, `02-workstreams/Decisions/{WS}/`, etc.
- Frontmatter: `workstream: {WS}`
- Wikilinks: `[[{WS}]]`

### Examples of what this prevents

| Source text                 | Wrong                      | Right (normalized)                   |
| --------------------------- | -------------------------- | ------------------------------------ |
| "Order-to-Cash stream"      | Creates `Order-to-Cash.md` | Uses `OTC.md`                        |
| "O2C design review"         | Creates folder `O2C/`      | Uses folder `OTC/`                   |
| "the P-2-P team"            | Creates `P-2-P.md`         | Uses `P2P.md`                        |
| "quality system" / "QA box" | Creates a new system entry | Uses the registered SID (e.g. `QAS`) |

**Seed `meta/entities.md` at setup** with every known workstream, SAP module, system SID, and key vendor — so the AI never invents a second spelling.

---

## Query Mode

When a team member asks a question about the vault:

**How to answer:**

1. Read `meta/index.md` first to orient
2. Read relevant pages from the appropriate zone
3. Answer from synthesized vault content only — not from raw files in `raw/`
4. Cite which vault page you are drawing from. Example: "From [[Decision - OTC - Custom BAPI approach - 2026-07-15]]…"
5. If the answer is not in the vault, say so explicitly: "The vault doesn't have this yet — consider ingesting [X]."

**Source of truth:**

- The `.md` pages in `01-standards/`, `02-workstreams/`, `03-intelligence/`, `04-internal/`, and `meta/` are the synthesized knowledge layer. Use these.
- Files in `raw/inbox/` and `raw/processed/` are unprocessed source material. Do not use these to answer questions.

**Tone:**

- Direct, structured, grounded in vault evidence
- Never fabricate context that isn't in the vault
- Never summarize a raw file as if it were vault knowledge

---

## Compounding — Conversation-to-Vault Loop

The vault compounds through two channels:

1. **File ingestion** — automated pipeline (OneDrive → raw/inbox → GitHub Actions → Claude → vault)
2. **Conversation insights** — durable knowledge that emerges during Claude Code sessions

**When compounding should trigger:**

During any conversation, if any of the following emerge:

- A decision made during the conversation
- A technical constraint or tradeoff not yet recorded
- A repeated pattern appearing for the second time
- A gotcha discovered while debugging
- A stakeholder signal not yet captured

…Claude should pause and offer:

> "This looks like durable knowledge — it's not in the vault yet. Should I write this to [suggested page path]?"

If the team member says yes, write/update immediately, then append a log entry to `meta/log.md`.

**Compounding is not automatic for every conversation.** Do not offer to save routine Q&A or exploratory thinking. Only flag genuine durable insights — things valuable to a teammate six months from now.

**After saving:** Always confirm what was written and where:

> "Updated [[page name]]. Logged to meta/log.md."

---

## Collaboration Rules

Multiple team members use this vault simultaneously.

**The vault is the ingest pipeline's territory.** Vault pages in `01-standards/`, `02-workstreams/`, `03-intelligence/`, and `04-internal/` are maintained by the ingest pipeline and compounding conversations. Team members correct mistakes in Obsidian, but new raw material enters only through the drop-zone.

**For direct edits in Claude Code:**

- Always pull latest before starting
- If you update a vault page in a session, commit and push immediately
- Do not accumulate uncommitted edits across sessions
- Use `git status` before starting to check for uncommitted changes

**Concurrent ingestion is safe.** The GitHub Actions workflow queues concurrent runs sequentially, so multiple files uploaded close together process without conflict.

**The compounding convention:** When a teammate updates the vault via conversation, commit immediately. One file, one commit minimizes merge risk.

---

## Meta Files

- **`meta/index.md`** — Master navigation catalog organized by zone. Updated on every ingest.
- **`meta/log.md`** — Append-only chronological log of what was ingested when.
- **`meta/inbox.md`** — Deduplication table for processed files.
- **`meta/entities.md`** — Registry of canonical names (workstreams, modules, systems, vendors) and their aliases.
- **`meta/conventions.md`** — Naming, frontmatter, linking conventions (human-readable reference).

---

## File Processing Pipeline

The ingest pipeline (`raw/inbox/` → GitHub Actions → Claude → vault) handles these formats:

| Format                  | Processing Path                          | Notes                                                                                           |
| ----------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **TXT / MD**            | Direct to Claude                         | Native. No preprocessing.                                                                       |
| **VTT (transcripts)**   | Strip timestamps → text                  | Meeting/call transcripts.                                                                       |
| **PDF (text layer)**    | Extracted text to Claude                 | Large PDFs chunked by page range.                                                               |
| **DOCX**                | Text extraction                          | Headings and tables preserved; formatting lost but irrelevant.                                  |
| **PPTX**                | Text extraction (or PDF conversion)      | Speaker notes included where available.                                                         |
| **XLSX**                | Sheet extraction                         | Simple tables good; formulas and macros lost.                                                   |
| **PNG / JPG**           | Claude vision                            | Architecture diagrams, whiteboards, screenshots.                                                |
| **ABAP source**         | Direct as text → Code Ingestion Rule     | `.abap`/`.txt` code exports. Generates draft FS/TS + Development record, tagged `ai-generated`. |
| **Dependency extracts** | Direct as text/CSV → Code Ingestion Rule | TADIR, where-used, CDS dependency exports. Updates Dependencies sections of object pages.       |

**Cannot handle:** audio/video (transcribe first, drop the VTT/text), password-protected files, Visio (`export to PNG first`), files over ~40 MB via the OneDrive bridge. Unprocessable files are logged and left for the curator.

---

## Final Rule

**Do not optimize for note volume. Optimize for clarity, link density, and reuse.**

The vault compounds through intentional architecture, not busywork.

---

This constitution is the operating manual for the ABAP vault. When in doubt, re-read this document.
