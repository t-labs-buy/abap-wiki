#!/usr/bin/env python3
"""Gate for vault_communities.py and community-summarize.py — the vault's
global-search layer.

meta/communities.md is read by the abap-wiki skill to decide which pages to
open for a question about the corpus. Four properties have to hold or it does
damage rather than good:

  - Stable identity. A community's signature is its cache key. If signatures
    churn between runs, every ingest re-summarises the whole vault.
  - No graph pollution. The file must contain no [[wikilinks]] and must not
    change what graph-health sees. A generated file that creates edges makes
    the checker demand backlinks for pages nobody wrote.
  - Honest page names. Every page named in the file must exist — the same
    promise prompt_suggest_test.py enforces for suggested prompts, for the same
    reason: a name that resolves to nothing is a fabrication.
  - Graceful degradation. No API key, or no anthropic package, must still exit
    0 with usable scaffolding.

Builds a synthetic vault in a temp directory, so it does not drift when the
real vault gains or loses pages. No third-party dependencies.

Exits non-zero on regression.
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
SUMMARIZE = os.path.join(SCRIPTS, "community-summarize.py")
GRAPH_HEALTH = os.path.join(SCRIPTS, "graph-health.py")

sys.path.insert(0, SCRIPTS)
from vault_communities import partition, signature_of   # noqa: E402
from vault_model import Vault                           # noqa: E402

spec = importlib.util.spec_from_file_location("community_summarize", SUMMARIZE)
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

TODAY = "2026-08-25"
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    line = f"  {'PASS' if cond else 'FAIL'}  {name}"
    if detail and not cond:
        line += f"  — {detail}"
    print(line)


# --------------------------------------------------------------------------
# Fixture vault: two workstream clusters plus a pattern that bridges them, so
# the cross-workstream flag is exercised rather than assumed.
# --------------------------------------------------------------------------

PROSE = ("The job re-checks open exposure against the insured limit held in a "
         "legacy broker table and releases the order when the limit covers it. "
         "It writes an application-log entry for every release and runs every "
         "thirty minutes. ") * 3


def page(front, body):
    lines = ["---"]
    for k, val in front.items():
        lines.append(f"{k}: {val}")
    lines += ["---", "", body]
    return "\n".join(lines) + "\n"


def fm(title, ptype, zone, ws="", status="active", tags="[]"):
    return {
        "title": f'"{title}"', "type": ptype, "zone": zone, "status": status,
        "owner": '"Curator"', "created": "2026-07-01", "updated": "2026-07-20",
        "workstream": ws, "tags": tags, "source_files": "[]",
    }


FIXTURE = {
    "02-workstreams/Workstreams/OTC.md": page(
        fm("OTC", "workstream", "02-workstreams", "OTC"),
        "# OTC\n\n[[Decision - OTC - Custom credit auto-release job - 2026-07-14]]\n"
        "[[OTC - Anna Larsen]]\n" + PROSE),

    "02-workstreams/Workstreams/INT.md": page(
        fm("INT", "workstream", "02-workstreams", "INT"),
        "# INT\n\n[[INT - ZADUSR_SYNC]]\n[[INT - Ravi Kumar]]\n" + PROSE),

    "02-workstreams/Decisions/OTC/Decision - OTC - Custom credit auto-release job - 2026-07-14.md": page(
        fm("Decision", "decision", "02-workstreams", "OTC"),
        "# Decision\n\n[[OTC]]\n[[OTC - Anna Larsen]]\n" + PROSE),

    "02-workstreams/Developments/OTC/OTC - E-001 - Credit Auto-Release Job.md": page(
        fm("Dev", "development", "02-workstreams", "OTC"),
        "# Dev\n\n[[Pattern - IDoc error handling]]\n[[INT - ZADUSR_SYNC]]\n" + PROSE),

    "02-workstreams/Developments/INT/INT - ZADUSR_SYNC.md": page(
        fm("ZADUSR_SYNC", "development", "02-workstreams", "INT",
           status="draft", tags="[ai-generated]"),
        "# ZADUSR_SYNC\n\n[[Pattern - IDoc error handling]]\n"
        "[[OTC - E-001 - Credit Auto-Release Job]]\n" + PROSE),

    "02-workstreams/Stakeholders/OTC/OTC - Anna Larsen.md": page(
        fm("Anna Larsen", "stakeholder", "02-workstreams", "OTC"),
        "# Anna Larsen\n\nFinance lead.\n\n[[OTC]]\n" + PROSE),

    "02-workstreams/Stakeholders/INT/INT - Ravi Kumar.md": page(
        fm("Ravi Kumar", "stakeholder", "02-workstreams", "INT"),
        "# Ravi Kumar\n\nDeveloper.\n\n[[INT]]\n" + PROSE),

    # Bridges OTC and INT: the cluster containing it should span 2 workstreams.
    "03-intelligence/patterns/Pattern - IDoc error handling.md": page(
        fm("Pattern", "pattern", "03-intelligence", status="evergreen"),
        "# Pattern\n\n[[OTC - E-001 - Credit Auto-Release Job]]\n"
        "[[INT - ZADUSR_SYNC]]\n" + PROSE),
}

# Linked to by nobody and linking nowhere: a floating page. It must never
# appear in a community — that is a graph-health violation, not a cluster.
ISOLATED = ("04-internal/runbooks/Runbook - Transport release.md", page(
    fm("Runbook", "runbook", "04-internal", status="evergreen"),
    "# Runbook\n\nSteps.\n" + PROSE))


def build_vault(root, extra=None):
    for rel, text in list(FIXTURE.items()) + list(extra or []):
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    os.makedirs(os.path.join(root, "meta"), exist_ok=True)


def run(script, root, *args, keep_key=False):
    env = dict(os.environ)
    if not keep_key:
        env.pop("ANTHROPIC_API_KEY", None)
    return subprocess.run([sys.executable, script, "--root", root] + list(args),
                          capture_output=True, text=True, env=env)


def out_path(root):
    return os.path.join(root, "meta", "communities.md")


# --------------------------------------------------------------------------
# Clustering
# --------------------------------------------------------------------------

def test_clustering(root):
    print("\nClustering")
    v = Vault(root)
    a = partition(v)
    b = partition(Vault(root))

    check("signatures are deterministic",
          [c.signature for c in a] == [c.signature for c in b])
    check("ordering is deterministic",
          [c.members for c in a] == [c.members for c in b])
    check("signature depends only on the member set",
          all(c.signature == signature_of(c.members) for c in a))
    check("every clustered page is a real page",
          all(m in v.by_path for c in a for m in c.members))
    check("a community spans 2+ workstreams",
          any(c.spans_workstreams for c in a),
          "the bridging pattern page should merge OTC and INT work")
    check("hubs are members, highest degree first",
          all(set(c.hubs) <= set(c.members)
              and c.hubs == sorted(c.hubs, key=lambda p: (-v.degree(p), p))
              for c in a))

    # A page with no links at all is a floating page, not a community of one.
    with tempfile.TemporaryDirectory() as tmp:
        build_vault(tmp, extra=[ISOLATED])
        v2 = Vault(tmp)
        p2 = partition(v2)
        clustered = {m for c in p2 for m in c.members}
        check("an isolated page joins no community", ISOLATED[0] not in clustered)
        check("an isolated page is reported as unclustered",
              ISOLATED[0] in p2.unclustered)
        check("adding an isolated page does not churn signatures",
              [c.signature for c in p2] == [c.signature for c in a],
              "signatures must survive unrelated vault growth, or every "
              "ingest re-summarises everything")


# --------------------------------------------------------------------------
# Generated file
# --------------------------------------------------------------------------

def test_output(root):
    print("\nGenerated file")
    proc = run(SUMMARIZE, root, "--today", TODAY)
    check("exits 0 without an API key", proc.returncode == 0, proc.stderr)
    check("writes the file anyway", os.path.isfile(out_path(root)))

    text = open(out_path(root), encoding="utf-8").read()
    v = Vault(root)
    part = partition(v)

    check("no wikilinks in the output", "[[" not in text,
          "a generated meta file must not create graph edges")
    check("every community has a signature marker",
          all(f"sig: {c.signature}" in text for c in part))
    check("unsummarised communities are marked pending",
          text.count("body: pending") == len(part))
    check("says not to cite it", "Never cite a community" in text)

    named = set(re.findall(r"`([^`]+)`", text))
    real = {p.name for p in v.pages}
    unknown = {n for n in named if " " in n or "-" in n} - real - {
        "meta/communities.md", ".github/scripts/community-summarize.py"}
    check("every page name in the file exists", not unknown, f"unknown: {sorted(unknown)}")

    check("every member page is listed",
          all(v.by_path[m].name in text for c in part for m in c.members))


def test_graph_untouched(root):
    print("\nGraph is unaffected")
    before = Vault(root)
    n_before = len(before.pages)
    run(SUMMARIZE, root, "--today", TODAY)
    after = Vault(root)
    check("the generated file is not a vault page", len(after.pages) == n_before,
          "meta/ must stay outside the four content zones")

    proc = run(GRAPH_HEALTH, root)
    check("graph-health still runs", proc.returncode == 0, proc.stderr)
    listed = re.findall(r"^- \*\*(\d+) pages\*\*", proc.stdout, re.MULTILINE)
    part = partition(after)
    check("graph-health reports the shared partition",
          [int(n) for n in listed] == [len(c.members) for c in part],
          "graph-health must not re-implement clustering")
    check("graph-health reports summary coverage", "### Summary coverage" in proc.stdout)


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------

def fake_summaries(root):
    """Stand in for a successful API run so the cache path is testable."""
    v = Vault(root)
    text = open(out_path(root), encoding="utf-8").read()
    for i, com in enumerate(partition(v), 1):
        text = text.replace(f"<!-- sig: {com.signature} body: pending -->",
                            f"<!-- sig: {com.signature} body: {com.body_hash(v)} -->")
        text = text.replace(f"## {i} — ", f"## {i} — Cached title {i} ", 1)
    text = text.replace("_No summary yet — the next run with an API key writes one._",
                        "<!-- summary: begin -->\nCached prose.\n<!-- summary: end -->")
    with open(out_path(root), "w", encoding="utf-8") as fh:
        fh.write(text)


def test_cache(root):
    print("\nCache")
    run(SUMMARIZE, root, "--today", TODAY)
    fake_summaries(root)

    cache = cs.read_cache(out_path(root))
    part = partition(Vault(root))
    check("cached summaries are read back",
          set(cache) == {c.signature for c in part})
    check("cached prose survives a rerun",
          all(cache[c.signature][2] == "Cached prose." for c in part))

    proc = run(SUMMARIZE, root, "--today", TODAY)
    check("an unchanged vault reuses everything",
          f"{len(part)} reused, 0 new, 0 pending" in proc.stdout, proc.stdout)
    check("titles survive the rerun",
          "Cached title 1" in open(out_path(root), encoding="utf-8").read())

    # Edit one page body without touching its links: membership is unchanged,
    # so only the body hash can catch it.
    target = os.path.join(root, "02-workstreams/Developments/INT/INT - ZADUSR_SYNC.md")
    with open(target, "a", encoding="utf-8") as fh:
        fh.write("\nA sentence added after the summary was written.\n")

    edited = partition(Vault(root))
    owner = next(c for c in edited
                 if "02-workstreams/Developments/INT/INT - ZADUSR_SYNC.md" in c.members)
    proc = run(SUMMARIZE, root, "--dry-run")
    check("an edited page invalidates its own community",
          f"would reuse {len(edited) - 1}, would summarise 1" in proc.stdout
          and owner.signature in proc.stdout, proc.stdout)

    before = open(out_path(root), encoding="utf-8").read()
    run(SUMMARIZE, root, "--dry-run")
    check("--dry-run writes nothing",
          open(out_path(root), encoding="utf-8").read() == before)

    proc = run(SUMMARIZE, root, "--force", "--dry-run")
    check("--force ignores the cache",
          f"would reuse 0, would summarise {len(part)}" in proc.stdout, proc.stdout)


def test_response_parsing():
    print("\nResponse parsing")
    title, prose = cs.parse_response(
        "TITLE: Credit release and FSCM gaps\n"
        "SUMMARY: The job releases key-account orders against a legacy limit table.")
    check("a well-formed response parses", title == "Credit release and FSCM gaps"
          and prose.startswith("The job releases"))

    check("a malformed response is rejected",
          cs.parse_response("I could not summarise these pages.") == (None, None),
          "an unparseable response must leave the community pending, not "
          "write half a summary")

    _, prose = cs.parse_response(
        "TITLE: A\nSUMMARY: See [[OTC - E-001 - Credit Auto-Release Job]] for detail.")
    check("wikilinks in a response are defused", "[[" not in prose and "`OTC" in prose,
          "the prompt forbids them; this is the guard for when the model does it anyway")

    _, prose = cs.parse_response("TITLE: A\nSUMMARY: " + "word " * 400)
    check("the word cap is enforced", len(prose.split()) <= cs.SUMMARY_WORD_CAP + 1)

    _, prose = cs.parse_response("TITLE: A\nSUMMARY: one\n\ntwo\n\nthree")
    check("the summary is collapsed to one paragraph", "\n" not in prose)


def test_model_path():
    """The prose path, with the model stubbed — the real API is not reachable
    from a test, but everything downstream of the response must still be
    covered: hashes stop reading pending, prose lands in the file, and the
    result round-trips through the cache."""
    print("\nModel path (stubbed)")
    tmp = tempfile.mkdtemp()
    try:
        build_vault(tmp)
        real_client, real_call = cs.get_client, cs.call_api_with_retry
        calls = []
        cs.get_client = lambda: ("stub", "stub")
        cs.call_api_with_retry = lambda client, mod, prompt: (
            calls.append(prompt) or
            "TITLE: Stubbed cluster title\nSUMMARY: Stubbed summary prose.")
        argv = sys.argv
        try:
            sys.argv = ["community-summarize.py", "--root", tmp, "--today", TODAY]
            rc = cs.main()
        finally:
            sys.argv = argv
            cs.get_client, cs.call_api_with_retry = real_client, real_call

        text = open(out_path(tmp), encoding="utf-8").read()
        part = partition(Vault(tmp))
        check("exits 0", rc == 0)
        check("one call per community", len(calls) == len(part))
        check("the prompt carries the member pages",
              all("### " in c for c in calls) and
              any("Credit Auto-Release" in c for c in calls))
        check("the prompt forbids wikilinks",
              all("Never write [[double brackets]]" in c for c in calls))
        check("nothing is left pending", "body: pending" not in text)
        check("prose is written", text.count("Stubbed summary prose.") == len(part))
        check("titles reach the index", "| Stubbed cluster title |" in text)

        proc = run(SUMMARIZE, tmp, "--today", TODAY)
        check("model output round-trips through the cache",
              f"{len(part)} reused, 0 new, 0 pending" in proc.stdout, proc.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_empty_vault():
    print("\nEmpty vault")
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "02-workstreams"))
        proc = run(SUMMARIZE, tmp, "--today", TODAY)
        check("exits 0 on a vault with no pages", proc.returncode == 0, proc.stderr)
        text = open(out_path(tmp), encoding="utf-8").read()
        check("says there is nothing yet", "no communities yet" in text)
        check("no wikilinks in the empty file", "[[" not in text)


# --------------------------------------------------------------------------

def main():
    tmp = tempfile.mkdtemp()
    try:
        build_vault(tmp)
        test_clustering(tmp)
        test_output(tmp)
        test_graph_untouched(tmp)
        test_cache(tmp)
        test_response_parsing()
        test_model_path()
        test_empty_vault()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
