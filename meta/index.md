# Vault Index

Master navigation catalog, organized by zone. **Updated on every ingest** — when a page is created or renamed, its entry here changes too.

_Last updated: 2026-07-15_

## 01-standards

### Coding

- [[Standard - ABAP Naming Conventions]] — custom object prefixes, variable scope/type prefixes, OO and program naming

### Architecture

- _(none yet)_

### Landscape

- _(none yet)_

## 02-workstreams

### Workstreams

- [[OTC]] — Order-to-Cash workstream overview

### Stakeholders

- [[OTC - Anna Larsen]] — OTC
- [[OTC - Jonas Weber]] — OTC
- [[OTC - Priya Nair]] — OTC
- [[OTC - Senthil Palanivelu]] — OTC
- [[OTC - Andreas Kvarnö]] — OTC (Master data, CGI)
- [[OTC - Madeleine Jacobsson]] — OTC (Order-to-Cash, ES)
- [[OTC - Tomas Kuniholm]] — OTC (IT, ES)
- [[OTC - Hashini]] — OTC (Developer, CR044)

### Meetings

- [[OTC - Design Review - 2026-07-14]] — credit-block auto-release design review

### Recent Decisions

- [[Decision - OTC - Custom credit auto-release job - 2026-07-14]] — custom periodic job over FSCM config
- [[Decision - OTC - Address type removed from validation criteria - 2026-01-29]] — v3.0: only relevant address types loaded to ZSD_ADR_VLD

### Specs

- [[OTC - Spec - Credit Block Auto-Release]] — spec (draft)
- [[OTC - Spec - BP Address Validation]] — BP address validation against Geposit reference table ZSD_ADR_VLD (draft)

### Developments

- [[OTC - E-001 - Credit Auto-Release Job]] — ZSD_CREDIT_AUTORELEASE development
- [[OTC - CR045 - BP Address Validation]] — BP address validation enhancement + detection report (draft)

### Estimations

- [[OTC - Estimation - Credit Auto-Release Job - 2026-07-14]] — 8 PD initial estimate

### Open Questions

- [[Open-Questions/OTC|OTC]] — rolling open-questions page for OTC

## 03-intelligence

### Patterns

- [[Pattern - BAPI_TRANSACTION_COMMIT WAIT in batch jobs]] — seen in P2P and OTC

### Lessons Learned

- _(none yet)_

### Gotchas

- [[Gotcha - BAPI_TRANSACTION_COMMIT wait flag]] — WAIT='X' avoids 'order still locked'

### Troubleshooting Guides

- _(none yet)_

### FAQs

- [[FAQ - Credit Auto-Release Integration]] — technical open questions
- [[FAQ - Transporting Background Jobs]] — process & transport open question

## 04-internal

- _(none yet)_
