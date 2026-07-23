---
name: abap-wiki
description: "Answer questions from the ABAP knowledge vault (t-labs-buy/abap-wiki) — the team's canonical memory of ABAP delivery: standards, workstreams (OTC, INT), decisions, specs, developments/WRICEF objects, estimations, issues, open questions, patterns, gotchas, troubleshooting, FAQs, runbooks and onboarding. Use whenever someone asks what the team decided, what a custom object does, who owns something, what the standard or convention is, what's still open, or anything else answerable from project knowledge rather than general SAP knowledge. Syncs the latest vault from GitHub first, then answers with page citations."
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

It prints four lines:

| Line          | Meaning                                                                        |
| ------------- | ------------------------------------------------------------------------------ |
| `VAULT_PATH=` | absolute path of the local clone — normally `~/.cache/claude-vaults/abap-wiki` |
| `STATUS=`     | `current`, `updated`, `cloned`, `repaired`, or `offline (using cached copy)`   |
| `LATEST=`     | newest commit in the copy you are about to read                                |
| `PAGES=`      | number of vault pages available                                                |

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

**Do not read the vault from anywhere else.** If the current working directory
happens to be a clone of the same repo, ignore it — it may hold unpushed or
half-edited work. Read only from `VAULT_PATH`. (If the user explicitly asks
about their own working copy, that's the exception.)

## Step 2 — Orient

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

## Step 3 — Read the relevant pages

Read whole pages rather than grep fragments. Frontmatter carries `status`,
`owner`, `updated` and `workstream`, which often matter to the answer.

## Step 4 — Answer

- Answer **only** from pages in `01-standards/`, `02-workstreams/`,
  `03-intelligence/`, `04-internal/`.
- **Never** answer from anything under `raw/` — unprocessed source material
  (transcripts, drops), not vault knowledge. Do not quote it.
- **Cite every page** you drew on, by page name, e.g.
  "From _Decision - OTC - Custom BAPI approach - 2026-07-15_…".
- Note staleness when it matters: an old `updated:` date, or `status:` of
  `draft` / `parked`.
- Flag `ai-generated` pages as **unvalidated** — reconstructed from source
  code, not yet confirmed by an SME.
- Surface `> [!warning] CONFLICT` blocks if you hit one: the vault has recorded
  contradictory claims and a human owes a decision. Don't silently pick a side.
- If the vault does not answer the question, say so plainly: "The vault doesn't
  have this yet — consider ingesting [X]." Do not fill the gap with general SAP
  knowledge, and do not guess.

## Scope

Read-only. This skill answers questions; it never writes to the vault. New
material enters the vault only through the OneDrive drop-zone and the ingest
pipeline.
