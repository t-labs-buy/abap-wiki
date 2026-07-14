# 03-intelligence — Reusable Learnings

What the team has learned that outlives any single workstream. Pages arrive here mostly by **promotion**: anything appearing in 2+ contexts moves up from Zone 02 (gotchas are the exception — they are written immediately, first occurrence).

| Subfolder          | Holds                                                       | Naming                            |
| ------------------ | ----------------------------------------------------------- | --------------------------------- |
| `patterns/`        | Repeated insight/approach seen in 2+ workstreams or objects | `Pattern - {Name}.md`             |
| `lessons-learned/` | Distilled learnings from a phase, go-live, or workstream    | `Lessons - {Context} - {Year}.md` |
| `gotchas/`         | Non-obvious SAP behavior that cost real time                | `Gotcha - {Name}.md`              |
| `troubleshooting/` | Curated diagnostic guides (symptoms → checks → fixes)       | `Troubleshooting - {Area}.md`     |
| `faqs/{topic}/`    | Repeated questions, answered and unanswered                 | `FAQ - {Topic}.md`                |

FAQ topics: `technical/`, `process-and-transport/`, `landscape-and-access/`, `testing/`.

Troubleshooting guides are promoted when 2+ resolved Issues share the same diagnostic path — they are the curated layer above individual Issues and gotchas.

Every page here must link back to the Zone 02 pages where the learning was observed.
