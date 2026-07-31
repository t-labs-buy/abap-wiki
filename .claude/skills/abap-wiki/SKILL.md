---
name: abap-wiki
description: "Answer questions from the ABAP knowledge vault (t-labs-buy/abap-wiki) — the team's canonical memory of ABAP delivery: standards, workstreams (OTC, INT), decisions, specs, developments/WRICEF objects, estimations, issues, open questions, patterns, gotchas, troubleshooting, FAQs, runbooks and onboarding. Use whenever someone asks what the team decided, what a custom object does, who owns something, what the standard or convention is, what's still open, or anything else answerable from project knowledge rather than general SAP knowledge. Syncs the latest vault from GitHub first, then answers with page citations. Invoked bare, or asked what's in the vault / what can be asked of it, it suggests domain-adapted questions derived from the vault's own content."
---

# ABAP Knowledge Vault

Answer the user's question from the ABAP vault — never from general SAP
knowledge and never from memory of past sessions.

The vault is the **public** GitHub repo `t-labs-buy/abap-wiki`. No token, no
authentication and no MCP server are needed: this skill keeps a local clone and
refreshes it on every run.

## Step 1 — Sync the vault (always do this first)

Run **one** of these, matching the shell you are in.

macOS / Linux (bash or zsh):

```bash
for d in ~/.claude/skills/abap-wiki ~/.gemini/config/skills/abap-wiki \
         ~/.copilot/skills/abap-wiki ~/.agents/skills/abap-wiki \
         .claude/skills/abap-wiki .agents/skills/abap-wiki .github/skills/abap-wiki; do
  [ -f "$d/scripts/sync-vault.sh" ] && bash "$d/scripts/sync-vault.sh" t-labs-buy/abap-wiki && break
done
```

Windows (PowerShell):

```powershell
foreach ($d in "$HOME\.claude\skills\abap-wiki", "$HOME\.gemini\config\skills\abap-wiki",
               "$HOME\.copilot\skills\abap-wiki", "$HOME\.agents\skills\abap-wiki",
               ".claude\skills\abap-wiki", ".agents\skills\abap-wiki", ".github\skills\abap-wiki") {
  if (Test-Path "$d\scripts\sync-vault.ps1") {
    powershell -ExecutionPolicy Bypass -File "$d\scripts\sync-vault.ps1" t-labs-buy/abap-wiki; break
  }
}
```

Both produce identical output. The loop finds the script wherever this skill is
installed — Claude Code, VS Code and Antigravity each use a different folder —
so run it exactly as written. Do not hand-write a `git clone` or `git pull`: the
script checks the remote's HEAD before transferring anything, skips the pull
when nothing has changed, repairs a damaged copy, and degrades safely when
offline.

It prints five lines:

| Line            | Meaning                                                                        |
| --------------- | ------------------------------------------------------------------------------ |
| `VAULT_PATH=`   | absolute path of the local clone — normally `~/.cache/claude-vaults/abap-wiki` |
| `STATUS=`       | `current`, `updated`, `cloned`, `repaired`, or `offline (using cached copy)`   |
| `LATEST=`       | newest commit in the copy you are about to read                                |
| `PAGES=`        | number of vault pages available                                                |
| `SKILL_STATUS=` | whether this skill file itself is up to date — see below                       |

**Use the absolute `VAULT_PATH` value literally in every later command and file
read.** Each command runs in a fresh shell, so a variable you set in one step is
empty in the next, and `~` is not expanded by the file-reading tools. Paste the
real path instead.

Handle the status:

- `current` — the remote had nothing new, so no pull was needed. The cache is
  verified up to date. Answer normally; no staleness caveat.
- `updated` / `cloned` / `repaired` — fresh content was just fetched. Answer
  normally.
- `offline (using cached copy)` — the remote could not be reached, or it had
  changes that failed to transfer. Answer anyway, but tell the user the vault
  may be out of date and quote the `LATEST` date.
- The script exits non-zero only when there is no usable copy at all. If that
  happens, report the error rather than answering from general knowledge.

Handle `SKILL_STATUS` — this skill file ships inside the vault repo, so every
sync fetches the canonical copy and compares it with the one you are running:

- `current` — the installed skill matches what is published. Nothing to do.
- `stale (update with: cp …)` — the installed copy has fallen behind. Answer the
  question normally, then tell the user their skill is outdated and show them
  the `cp` command. Never run it yourself: overwriting a file under the user's
  home directory is their call, not a side effect of asking a question.
- `ahead (git checkout …)` — the skill is installed from a repo checkout with
  local changes. Expected during development; mention it only if relevant.
- `unknown (nothing to compare)` — no published copy found. Ignore it.

**Do not read the vault from anywhere else.** If the current working directory
happens to be a clone of the same repo, ignore it — it may hold unpushed or
half-edited work. Read only from `VAULT_PATH`. (If the user explicitly asks
about their own working copy, that's the exception.)

## Step 2 — If no question was asked, offer prompts the vault can answer

When the skill is invoked bare (`/abap-wiki` with nothing after it), or the
user asks some form of "what's in here?" / "what can I ask?", do not guess at a
question and do not list folder names. Show them prompts derived from what the
vault actually holds:

```bash
python3 /ABSOLUTE/VAULT_PATH/.github/scripts/prompt-suggest.py \
  --root /ABSOLUTE/VAULT_PATH --top 8
```

Windows: same command with `python` instead of `python3`.

The script is deterministic, reads only the vault, and writes nothing. Every
question it emits names the page(s) that answer it — so anything it prints can
be answered immediately by going to Step 3 with that question. It prints a
one-line vault profile (page count, workstreams, coverage) followed by prompts
grouped by theme.

Present the profile line, then the questions grouped as printed. Keep the
`answered by` page names out of the message unless the user asks — they are
there so you can jump straight to the right page when one is picked. Repeat any
flag the script prints (`draft`, `unvalidated`, `thin`, `unresolved conflict`)
next to that question: a reader choosing what to ask deserves to know the answer
is provisional before they ask it.

Useful variants:

| Situation                                         | Command                                  |
| ------------------------------------------------- | ---------------------------------------- |
| User named a workstream ("what's in OTC?")        | `--workstream OTC`                       |
| User named a topic ("anything on credit blocks?") | `--about credit`                         |
| Follow-ups after an answer                        | `--near "<page you cited>"` (repeatable) |
| You only need the questions, cheapest output      | `--format compact`                       |

If `python3` is missing or the script errors, say so in one line and fall back
to reading `meta/index.md` and describing the vault's coverage from it. Never
invent suggested questions: a prompt the vault cannot answer wastes the reader's
next turn.

This script only suggests questions the vault **can** answer. Its counterpart,
`question-gen.py`, lists what the vault **cannot** answer yet — gaps for the
curator. If the user is asking what's missing rather than what's known, that's
the one to run (`--root` the same way).

## Step 3 — Orient

Read `<VAULT_PATH>/meta/index.md` — the master navigation catalog, organised by
zone, listing every page with a one-line description. Choose the pages worth
reading from there.

**Normalise names before searching.** The vault uses canonical slugs, and
people rarely use them: "Order-to-Cash", "O2C" and "the OTC stream" are all
`OTC`. Check `<VAULT_PATH>/meta/entities.md` — the registry of canonical
workstream, module, system and vendor names with their aliases — whenever the
question names something that might have variants. Searching for the user's
wording alone will miss pages.

To find pages the index doesn't obviously cover, search content directly. Use
the real path and keep `raw/` out of scope:

```bash
grep -ril "search term" /ABSOLUTE/VAULT_PATH/0*/
```

(The `0*/` glob covers exactly the four content zones and excludes `raw/`,
`meta/` and `.git`.)

Structure:

| Path               | Holds                                                                                         |
| ------------------ | --------------------------------------------------------------------------------------------- |
| `01-standards/`    | coding standards, architecture principles, landscape docs                                     |
| `02-workstreams/`  | per workstream: meetings, decisions, specs, developments, issues, estimations, open questions |
| `03-intelligence/` | patterns, lessons learned, gotchas, troubleshooting guides, FAQs                              |
| `04-internal/`     | contacts, onboarding, processes, runbooks                                                     |
| `meta/`            | index, entity registry, ingest log — navigation aids, not answers                             |

Pages link to each other with `[[wikilinks]]` and end with a `## Linked from`
section — follow both directions when an answer spans several pages.

## Step 4 — Read the relevant pages

Read whole pages rather than grep fragments. Frontmatter carries `status`,
`owner`, `updated` and `workstream`, which often matter to the answer.

## Step 5 — Answer

- Answer **only** from pages in `01-standards/`, `02-workstreams/`,
  `03-intelligence/`, `04-internal/`.
- **Never** answer from anything under `raw/` — unprocessed source material
  (transcripts, drops), not vault knowledge. Do not quote it.
- **Cite every page** you drew on, using the structured format below. Every
  claim that comes from the vault carries a citation marker; a sentence without
  one must be your own framing, never vault content presented as unsourced fact.
- **Do not include information whose supporting evidence is not in the vault.**
- Note staleness when it matters: an old `updated:` date, or `status:` of
  `draft` / `parked`.
- Flag `ai-generated` pages as **unvalidated** — reconstructed from source
  code, not yet confirmed by an SME.
- Surface `> [!warning] CONFLICT` blocks if you hit one: the vault has recorded
  contradictory claims and a human owes a decision. Don't silently pick a side.
- If the vault does not answer the question, say so plainly: "The vault doesn't
  have this yet — consider ingesting [X]." Do not fill the gap with general SAP
  knowledge, and do not guess.

## Citation format

Citations are structured so they can be checked, not just read. A citation that
names a page which does not exist is a fabrication, and the format must make
that catchable by a script rather than only by a reader who knows the vault.

**Page names never appear in the body of the answer.** They clutter the prose
they are meant to support. Instead the body carries a small numbered marker, and
the page names live in a `Sources` list at the end.

### In the body — a superscript marker

Put a superscript digit immediately after the sentence's closing punctuation,
with no space:

```
… that is not replicated into FSCM.¹
```

- Use the superscript characters `¹²³⁴⁵⁶⁷⁸⁹`, combining them past nine (`¹⁰`,
  `¹¹`). Never write a bare `[1]` — a bracketed number is parsed as a markdown
  shortcut reference link and terminal renderers drop it silently, leaving the
  claim looking uncited.
- Number sources in the order they are first cited, starting at 1.
- **Reuse a number** when a later claim rests on the same page or page set. Do
  not mint a new number for a source already listed.
- One marker per claim, not per page: a claim supported by three pages gets one
  marker whose Sources entry names all three.
- Markers attach to claims, not to headings, table rows' every cell, or bullet
  fragments that share a source with the bullet above them.

### At the end — the Sources list

Close the answer with a `---` rule, a bold `**Sources**` line, and a numbered
list. Each entry is a **backtick-wrapped code span** grouping that entry's pages
by their `type:` frontmatter value:

```
<n>. `<type> (<Page Name>, <Page Name>); <type> (<Page Name>)`
```

Rules:

- **Always wrap each entry in backticks.** This is not cosmetic. A code span
  cannot be parsed as a link, renders literally everywhere (terminal, Obsidian,
  GitHub), and keeps page names intact even when the entry wraps onto a new
  line.
- **Never use square brackets around page names.**
- **Use the page name exactly as it appears in the filename, without `.md`** —
  not the `title:` field, not a paraphrase, not a shortened form. This is what
  makes a citation verifiable.
- `<type>` is the page's `type:` value (`decision`, `development`, `spec`,
  `gotcha`, `standard`, `stakeholder`, …) — the same controlled vocabulary the
  vault uses.
- Separate pages of the same type with `,`; separate type groups with `;`.
- **Never list more than 5 page names in one group.** List the 5 most relevant
  and add `+more`.
- Every marker in the body has exactly one matching entry, and every entry has
  at least one marker pointing at it. No orphans in either direction.

### Example

```
Credit-blocked key-account orders are released by a custom periodic job rather
than by standard FSCM configuration, because the insured-limit data lives in a
legacy table that is not replicated into FSCM.¹

Wave 2 is estimated at 41 person-days across 12 objects.²

---

**Sources**

1. `decision (Decision - OTC - Custom credit auto-release job - 2026-07-14); development (OTC - E-001 - Credit Auto-Release Job)`
2. `estimation (OTC - Estimation - Wave 2 WRICEF list - 2026-07-20)`
```

Before sending an answer, check that every Sources entry opens and closes with a
backtick, and that the marker numbers and entry numbers line up. An uncited
claim and an invisibly-cited claim look identical to the reader.

For a one-line answer drawn from a single page, the rule still holds — one
marker, one Sources entry. Do not fall back to an inline page name.

Flags stay in the prose of the answer, not in the Sources list: say plainly, at
the claim itself, when a page is `draft`, `ai-generated` (unvalidated), stale,
or carries a CONFLICT block. A reader who never scrolls to Sources must still
see the caveat.

## Step 6 — Offer follow-ups

After the Sources list, offer up to three related questions drawn from the
pages around the ones you just cited:

```bash
python3 /ABSOLUTE/VAULT_PATH/.github/scripts/prompt-suggest.py \
  --root /ABSOLUTE/VAULT_PATH --format compact --top 3 \
  --near "<page you cited>" --near "<another page you cited>"
```

`--near` walks the link graph out from those pages, so the follow-ups are
neighbours of the answer rather than generic vault highlights. Print them under
a **You could also ask** heading, below the Sources list, verbatim and without
citation markers — they are questions, not claims, and markers must keep
pointing only at what you actually asserted.

Skip the follow-ups when the script returns nothing, when the user asked a
narrow factual question they clearly wanted closed, or when they are working
through a list of their own. Three is a ceiling, not a target.

When the vault did **not** answer the question, this step earns its keep: run
the same script with `--about <the key term>` instead of `--near`, and offer
what the vault does hold nearby. "The vault doesn't have this yet" plus two
things it does have beats a dead end.

## Scope

Read-only. This skill answers questions; it never writes to the vault. New
material enters the vault only through the OneDrive drop-zone and the ingest
pipeline.
