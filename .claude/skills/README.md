# Vault skill — ask this vault from your AI tool

`abap-wiki/` is an [Agent Skill](https://agentskills.io): a small folder that
teaches an AI assistant how to answer questions from this vault.

It needs **no GitHub token, no sign-in and no MCP server**. The vault repo is
public, so the skill keeps its own copy on your machine (in
`~/.cache/claude-vaults/abap-wiki`) and refreshes it from GitHub every time you
ask a question. The only requirement is `git` — check with `git --version`.

## If you cloned this repo

Nothing to do. Claude Code and VS Code both read `.claude/skills/` from the
project you have open. Just ask your question in plain English.

## If you have not cloned this repo

Copy the `abap-wiki` folder into the location your tool reads:

| Tool              | Where the folder goes                 |
| ----------------- | ------------------------------------- |
| Claude Code       | `~/.claude/skills/abap-wiki/`        |
| VS Code (Copilot) | `~/.claude/skills/abap-wiki/` — same |
| Antigravity       | `~/.gemini/config/skills/abap-wiki/` |

On Windows, `~` means `C:\Users\{your name}\`. Restart your tool afterwards.

```bash
# Claude Code and VS Code
mkdir -p ~/.claude/skills && cp -R abap-wiki ~/.claude/skills/

# Antigravity
mkdir -p ~/.gemini/config/skills && cp -R abap-wiki ~/.gemini/config/skills/
```

Antigravity also reads `.agents/skills/` inside a workspace, if you prefer to
keep it with the project.

## How to ask

Ask normally — the AI recognises vault questions on its own:

> What did we decide about the credit auto-release job?
> Which custom objects exist in the OTC workstream?
> What's still open on integrations, and who owns it?

To force it, say "use the abap-wiki skill", or type `/abap-wiki {question}`
in Claude Code.

Answers come only from the synthesized pages in `01-standards/`,
`02-workstreams/`, `03-intelligence/` and `04-internal/` — never from `raw/` —
and always cite the page they came from. If the vault doesn't cover something,
the skill says so instead of guessing.

## What is in the folder

| File                     | Purpose                                |
| ------------------------ | -------------------------------------- |
| `SKILL.md`               | the instructions the AI follows        |
| `scripts/sync-vault.sh`  | pulls the latest vault (macOS / Linux) |
| `scripts/sync-vault.ps1` | the same, for Windows PowerShell       |

Both scripts do the identical job; the skill picks the right one for your
operating system. They clone on first use, pull afterwards, rebuild the copy if
it is ever damaged, and fall back to the cached copy when you are offline.

The skill is **read-only** — it never writes to the vault. New material enters
only through the OneDrive drop-zone and the ingest pipeline.
