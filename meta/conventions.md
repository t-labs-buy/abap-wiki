# Conventions — Quick Human Reference

The short version of `CLAUDE.md` for teammates. When this page and `CLAUDE.md` disagree, `CLAUDE.md` wins.

## The five rules that matter most

1. **Update existing pages, don't create duplicates.** Search first.
2. **Never create a floating page** — every page links upward to a parent with `[[wikilinks]]`.
3. **Never delete a page** — set `status: archived` in the frontmatter.
4. **Meetings are source material** — the extracts go into workstream/decision/spec pages.
5. **Check `meta/entities.md` before naming anything** — one canonical spelling per workstream, module, and system.

## Naming cheat sheet

| Creating a…     | Path                                | Filename                                        |
| --------------- | ----------------------------------- | ----------------------------------------------- |
| Standard        | `01-standards/coding/`              | `Standard - {Name}.md`                          |
| Workstream page | `02-workstreams/Workstreams/`       | `{WS}.md`                                       |
| Stakeholder     | `02-workstreams/Stakeholders/{WS}/` | `{WS} - {Full Name}.md`                         |
| Meeting         | `02-workstreams/Meetings/{WS}/`     | `{WS} - {Topic} - {YYYY-MM-DD}.md`              |
| Decision        | `02-workstreams/Decisions/{WS}/`    | `Decision - {WS} - {Topic} - {YYYY-MM-DD}.md`   |
| Spec            | `02-workstreams/Specs/{WS}/`        | `{WS} - Spec - {Object or Topic}.md`            |
| Development     | `02-workstreams/Developments/{WS}/` | `{WS} - {ID} - {Object Name}.md`                |
| Estimation      | `02-workstreams/Estimations/{WS}/`  | `{WS} - Estimation - {Topic} - {YYYY-MM-DD}.md` |
| Issue           | `02-workstreams/Issues/{WS}/`       | `{WS} - Issue - {Topic} - {YYYY-MM-DD}.md`      |
| Pattern         | `03-intelligence/patterns/`         | `Pattern - {Name}.md`                           |
| Gotcha          | `03-intelligence/gotchas/`          | `Gotcha - {Name}.md`                            |
| Troubleshooting | `03-intelligence/troubleshooting/`  | `Troubleshooting - {Area}.md`                   |
| Lessons         | `03-intelligence/lessons-learned/`  | `Lessons - {Context} - {Year}.md`               |
| FAQ             | `03-intelligence/faqs/{topic}/`     | `FAQ - {Topic}.md`                              |
| Runbook         | `04-internal/runbooks/`             | `Runbook - {Name}.md`                           |

## Frontmatter

Every page carries exactly the schema in `CLAUDE.md` — copy it from the `_Template-*.md` in the folder you're writing into. No extra fields, no omissions.

## Tags

`tags:` values come from the **Tag Vocabulary** in `meta/entities.md` — nothing free-form. Need a tag that isn't there? Add it to the vocabulary first (with its category), then use it. Tags say what a page is _about_ (technology, business object, quality, process, role, phase) — don't repeat the page's `type:` or `workstream:` in them.

## Scope on intelligence pages

Every pattern, gotcha, and troubleshooting page states **Applies to** / **Does not apply to** (system/release, module, conditions). A rule without scope gets applied everywhere — including where it's wrong.

## Conflict blocks

If you see a `> [!warning] CONFLICT — unresolved` block on a page: the standing text above it is still authoritative; a newer source contradicted it and the curator owns the resolution. Don't remove the block or rewrite the claim — resolution happens through a Decision page, which is when the block comes off.

## Status values

`active` · `draft` · `parked` · `archived` · `resolved` (issues/closed decisions) · `evergreen` (standards, patterns, runbooks)
