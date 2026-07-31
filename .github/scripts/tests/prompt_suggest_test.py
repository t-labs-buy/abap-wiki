#!/usr/bin/env python3
"""Gate for prompt-suggest.py — the starter prompts the abap-wiki skill shows.

The promise the skill makes to a reader is narrow and checkable: every question
it offers is answered by a page that exists. This asserts that promise, plus
the filters that keep it honest — archived pages excluded, draft and
unvalidated pages flagged, role tags kept out of cross-workstream questions,
and identical output on identical input.

Runs against a synthetic vault built in a temp directory, so it does not drift
when the real vault gains or loses pages. No third-party dependencies.

Exits non-zero on regression.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
SCRIPT = os.path.join(SCRIPTS, "prompt-suggest.py")

sys.path.insert(0, SCRIPTS)
spec = importlib.util.spec_from_file_location("prompt_suggest", SCRIPT)
ps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ps)

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    line = f"  {'PASS' if cond else 'FAIL'}  {name}"
    if detail and not cond:
        line += f"  — {detail}"
    print(line)


# --------------------------------------------------------------------------
# Fixture vault
# --------------------------------------------------------------------------

TODAY = "2026-07-31"
PROSE = ("The job re-checks open exposure against the insured limit held in a "
         "legacy broker table and releases the order when the limit covers it. "
         "It writes an application-log entry for every release, runs every "
         "thirty minutes, and skips orders outside the key-account customer "
         "group. Failures are retried on the next cycle rather than escalated, "
         "which keeps the operations queue quiet during month-end peaks. ") * 2


def page(front, body):
    lines = ["---"]
    for k, val in front.items():
        lines.append(f"{k}: {val}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    return "\n".join(lines) + "\n"


def fm(title, ptype, zone, ws="", status="active", tags="[]",
       updated="2026-07-20"):
    return {
        "title": f'"{title}"', "type": ptype, "zone": zone, "status": status,
        "owner": '"Curator"', "created": "2026-07-01", "updated": updated,
        "workstream": ws, "tags": tags, "source_files": "[]",
    }


FIXTURE = {
    "02-workstreams/Workstreams/OTC.md": page(
        fm("OTC", "workstream", "02-workstreams", "OTC", tags="[credit-management]"),
        "# OTC\n\nScope and status.\n\n[[OTC - E-001 - Credit Auto-Release Job]]\n"
        "[[Decision - OTC - Custom credit auto-release job - 2026-07-14]]\n" + PROSE),

    "02-workstreams/Workstreams/INT.md": page(
        fm("INT", "workstream", "02-workstreams", "INT", tags="[integration]"),
        "# INT\n\n[[INT - ZADUSR_SYNC]]\n" + PROSE),

    "02-workstreams/Decisions/OTC/Decision - OTC - Custom credit auto-release job - 2026-07-14.md": page(
        fm("Decision", "decision", "02-workstreams", "OTC",
           tags="[credit-management, batch-job]"),
        "# Decision\n\n[[OTC]]\n[[OTC - E-001 - Credit Auto-Release Job]]\n" + PROSE),

    "02-workstreams/Developments/OTC/OTC - E-001 - Credit Auto-Release Job.md": page(
        fm("Dev", "development", "02-workstreams", "OTC",
           tags="[credit-management, batch-job]"),
        "# Dev\n\n[[OTC]]\n[[Standard - ABAP Naming Conventions]]\n" + PROSE),

    # Draft + ai-generated: must be offered with both flags, never silently.
    "02-workstreams/Developments/INT/INT - ZADUSR_SYNC.md": page(
        fm("ZADUSR_SYNC", "development", "02-workstreams", "INT",
           status="draft", tags="[integration, ai-generated]"),
        "# ZADUSR_SYNC\n\n[[INT]]\n" + PROSE),

    # Archived: must never be offered at all.
    "02-workstreams/Specs/OTC/OTC - Spec - Retired Interface.md": page(
        fm("Retired", "spec", "02-workstreams", "OTC", status="archived",
           tags="[integration]"),
        "# Retired\n\n[[OTC]]\n" + PROSE),

    # Near-empty: dropped entirely — there is no answer behind it to offer.
    "02-workstreams/Stakeholders/OTC/OTC - Anna Larsen.md": page(
        fm("Anna Larsen", "stakeholder", "02-workstreams", "OTC", tags="[client]"),
        "# Anna Larsen\n\nFinance lead.\n\n[[OTC]]\n"),

    # Thin but not empty: offered, and flagged so the reader knows it is slight.
    "02-workstreams/Stakeholders/OTC/OTC - Jonas Weber.md": page(
        fm("Jonas Weber", "stakeholder", "02-workstreams", "OTC", tags="[client]"),
        "# Jonas Weber\n\nCredit manager on the client side. Owns the credit "
        "policy and signs off release rules. Prefers standard configuration and "
        "asks for the effort figures before agreeing to a custom object.\n\n"
        "[[OTC]]\n"),

    "02-workstreams/Stakeholders/INT/INT - Ravi Kumar.md": page(
        fm("Ravi Kumar", "stakeholder", "02-workstreams", "INT", tags="[developer]"),
        "# Ravi Kumar\n\nDeveloper.\n\n[[INT]]\n"),

    "01-standards/coding/Standard - ABAP Naming Conventions.md": page(
        fm("Naming", "standard", "01-standards", tags="[naming-conventions]",
           status="evergreen"),
        "# Naming\n\n[[OTC - E-001 - Credit Auto-Release Job]]\n" + PROSE),

    "03-intelligence/gotchas/Gotcha - BAPI_TRANSACTION_COMMIT wait flag.md": page(
        fm("Gotcha", "gotcha", "03-intelligence", "OTC", tags="[bapi]",
           status="evergreen"),
        "# Gotcha\n\n[[OTC - E-001 - Credit Auto-Release Job]]\n" + PROSE),

    "03-intelligence/faqs/technical/FAQ - Credit Auto-Release Integration.md": page(
        fm("FAQ", "faq", "03-intelligence", "OTC", tags="[credit-management]"),
        "# FAQ\n\n[[OTC]]\n\n## Answered Questions\n\n"
        "- Does the job need FSCM configuration to run in QAS?\n"
        "  Answer: no, it reads the legacy table directly.\n\n"
        "## Unanswered Questions\n\n"
        "| Question | Asked by | Owner | Due |\n| --- | --- | --- | --- |\n"
        "| Can we transport the SM36 job definition? | Anna Larsen | Unassigned | — |\n"),
}

ENTITIES = """# Entity Registry

## Tag Vocabulary

### technology

| Tag         | Covers                |
| ----------- | --------------------- |
| bapi        | BAPI calls            |
| batch-job   | background jobs       |
| integration | interfaces            |

### business-object

| Tag               | Covers        |
| ----------------- | ------------- |
| credit-management | credit blocks |

### quality

| Tag                | Covers |
| ------------------ | ------ |
| naming-conventions | naming |

### role (stakeholder pages)

| Tag       | Covers               |
| --------- | -------------------- |
| client    | client-side          |
| developer | hands-on developer   |

## Something Else

| Not | A tag |
| --- | ----- |
"""


def build_vault(root):
    for rel, text in FIXTURE.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    os.makedirs(os.path.join(root, "meta"), exist_ok=True)
    with open(os.path.join(root, "meta", "entities.md"), "w", encoding="utf-8") as fh:
        fh.write(ENTITIES)


def run(root, *args):
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--root", root, "--today", TODAY] + list(args),
        capture_output=True, text=True)
    return proc


def run_json(root, *args):
    proc = run(root, "--format", "json", *args)
    if proc.returncode != 0:
        raise AssertionError(f"exit {proc.returncode}: {proc.stderr}")
    return json.loads(proc.stdout)


TMP = tempfile.mkdtemp(prefix="prompt-suggest-test-")
VAULT = os.path.join(TMP, "vault")
build_vault(VAULT)

# --------------------------------------------------------------------------

print("\n=== 1. Every suggestion is answerable ===")
data = run_json(VAULT, "--top", "30")
sugg = data["suggestions"]
check("suggestions produced", len(sugg) >= 8, f"got {len(sugg)}")

missing = [p for s in sugg for p in s["answered_by"]
           if not os.path.isfile(os.path.join(VAULT, p))]
check("every cited page exists on disk", not missing, str(missing[:3]))
check("no suggestion without a page", all(s["answered_by"] for s in sugg))

bad_text = [s["question"] for s in sugg
            if "[[" in s["question"] or ".md" in s["question"]
            or not s["question"].strip().endswith("?")]
check("questions are clean questions", not bad_text, str(bad_text[:2]))

print("\n=== 2. Archived pages are never offered ===")
archived = "02-workstreams/Specs/OTC/OTC - Spec - Retired Interface.md"
hits = [s["question"] for s in sugg if archived in s["answered_by"]]
check("archived spec excluded", not hits, str(hits[:2]))

print("\n=== 3. Provisional pages are offered, but flagged ===")
draft = [s for s in sugg
         if "02-workstreams/Developments/INT/INT - ZADUSR_SYNC.md" in s["answered_by"]
         and s["kind"] == "page:development"]
check("draft development still offered", bool(draft))
if draft:
    flags = draft[0]["flags"]
    check("flagged draft", "draft" in flags, str(flags))
    check("flagged unvalidated", "unvalidated" in flags, str(flags))

thin = [s for s in sugg
        if s["answered_by"] == ["02-workstreams/Stakeholders/OTC/OTC - Jonas Weber.md"]]
check("thin page offered with a thin flag",
      thin and "thin" in thin[0]["flags"],
      str(thin[0]["flags"]) if thin else "not offered")

empty_page = "02-workstreams/Stakeholders/OTC/OTC - Anna Larsen.md"
check("near-empty page is not offered at all",
      not any(s["answered_by"] == [empty_page] for s in sugg))

substantial = [s for s in sugg
               if s["answered_by"] == ["02-workstreams/Developments/OTC/"
                                       "OTC - E-001 - Credit Auto-Release Job.md"]]
check("substantial page carries no flags",
      substantial and not substantial[0]["flags"],
      str(substantial[0]["flags"]) if substantial else "not offered")

print("\n=== 4. Filename scaffolding is stripped from the subject ===")


class FakePage:
    def __init__(self, name, ws=""):
        self.name = name
        self.workstream = ws


slugs = {"OTC", "INT", "SD"}
for name, ws, want in [
    ("Decision - OTC - Custom credit auto-release job - 2026-07-14", "OTC",
     "Custom credit auto-release job"),
    ("OTC - CR045 - BP Address Validation", "OTC", "BP Address Validation"),
    ("OTC - E-001 - Credit Auto-Release Job", "OTC", "Credit Auto-Release Job"),
    ("INT - ZADUSR_SYNC", "INT", "ZADUSR_SYNC"),
    ("OTC - Estimation - Wave 2 WRICEF list - 2026-07-20", "OTC", "Wave 2 WRICEF list"),
    ("Gotcha - BAPI_TRANSACTION_COMMIT wait flag", "", "BAPI_TRANSACTION_COMMIT wait flag"),
    ("Standard - ABAP Naming Conventions", "", "ABAP Naming Conventions"),
    ("Lessons - OTC Go-Live - 2026", "OTC", "OTC Go-Live"),
    ("Runbook - Transport release", "", "Transport release"),
    ("OTC - Anna Larsen", "OTC", "Anna Larsen"),
    ("OTC", "OTC", "OTC"),
]:
    got = ps.subject_of(FakePage(name, ws), slugs)
    check(f"subject of {name!r}", got == want, f"got {got!r}, want {want!r}")

print("\n=== 5. Cross-cutting questions use topical tags only ===")
cross = [s for s in sugg if s["kind"].startswith("cross:")]
check("cross-cutting questions produced", bool(cross))
role_leak = [s["question"] for s in cross
             if any(t in s["question"].lower() for t in ("developer", "client"))]
check("role tags never become a topic", not role_leak, str(role_leak[:2]))
check("registry categories parsed",
      ps.topical_tags(VAULT) == {"bapi", "batch-job", "integration",
                                 "credit-management", "naming-conventions"},
      str(ps.topical_tags(VAULT)))
check("unparseable registry falls back to None",
      ps.topical_tags(TMP) is None)

print("\n=== 6. A real asked question is reused verbatim ===")
faq = [s for s in sugg if s["kind"] == "faq:asked"]
check("answered FAQ question picked up",
      any("FSCM configuration" in s["question"] for s in faq),
      str([s["question"] for s in faq]))
check("unanswered FAQ question not offered as answerable",
      not any("SM36" in s["question"] for s in sugg))

print("\n=== 7. Filters ===")
int_only = run_json(VAULT, "--workstream", "INT", "--top", "10")["suggestions"]
leaked = [s["question"] for s in int_only
          if s["kind"].startswith("page:") and s["workstream"] != "INT"]
check("--workstream keeps page prompts to that slug", not leaked, str(leaked[:2]))

near = run_json(VAULT, "--near", "OTC - E-001 - Credit Auto-Release Job",
                "--top", "10")["suggestions"]
check("--near returns neighbours", bool(near))
self_only = [s["question"] for s in near
             if s["answered_by"] == ["02-workstreams/Developments/OTC/"
                                     "OTC - E-001 - Credit Auto-Release Job.md"]]
check("--near excludes the page already read", not self_only, str(self_only))
far = [s["question"] for s in near
       if all("INT" in p or "Ravi" in p for p in s["answered_by"])]
check("--near excludes the far side of the graph", not far, str(far[:2]))

about = run_json(VAULT, "--about", "naming", "--top", "5")["suggestions"]
check("--about ranks the on-topic page first",
      about and "Naming Conventions" in about[0]["question"],
      about[0]["question"] if about else "nothing returned")

unknown = run(VAULT, "--near", "No Such Page", "--format", "compact")
check("--near on an unknown page warns and still runs",
      unknown.returncode == 0 and "no page named" in unknown.stderr)

print("\n=== 8. Determinism and degradation ===")
a = run(VAULT, "--top", "12").stdout
b = run(VAULT, "--top", "12").stdout
check("identical input gives identical output", a == b)

empty = os.path.join(TMP, "empty")
os.makedirs(empty, exist_ok=True)
proc = run(empty, "--format", "compact")
check("empty vault exits 0", proc.returncode == 0, proc.stderr)
check("empty vault says so", "0 pages" in proc.stdout, proc.stdout[:120])

proc = run(VAULT, "--today", "not-a-date")
check("bad --today is rejected", proc.returncode == 2)

print("\n=== 9. Recency and support affect rank ===")
stale_root = os.path.join(TMP, "stale")
shutil.copytree(VAULT, stale_root)
target = os.path.join(stale_root, "03-intelligence", "gotchas",
                      "Gotcha - BAPI_TRANSACTION_COMMIT wait flag.md")
with open(target, encoding="utf-8") as fh:
    text = fh.read()
with open(target, "w", encoding="utf-8") as fh:
    fh.write(text.replace("updated: 2026-07-20", "updated: 2023-01-05"))

fresh_rank = [s["question"] for s in run_json(VAULT, "--top", "30")["suggestions"]]
stale = run_json(stale_root, "--top", "30")["suggestions"]
stale_gotcha = [s for s in stale if s["kind"] == "page:gotcha"]
check("stale page is flagged with its date",
      stale_gotcha and any("2023-01-05" in f for f in stale_gotcha[0]["flags"]),
      str(stale_gotcha[0]["flags"]) if stale_gotcha else "not offered")
stale_rank = [s["question"] for s in stale]
gotcha_q = next((q for q in fresh_rank if "catch with" in q), None)
check("stale page ranks below its fresh self",
      gotcha_q and gotcha_q in stale_rank
      and stale_rank.index(gotcha_q) >= fresh_rank.index(gotcha_q))

# --------------------------------------------------------------------------

shutil.rmtree(TMP, ignore_errors=True)

failed = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
if failed:
    print("FAILED: " + "; ".join(failed))
sys.exit(1 if failed else 0)
