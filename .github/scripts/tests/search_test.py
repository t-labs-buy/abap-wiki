#!/usr/bin/env python3
"""Gate for vault_search.py and vault-search.py — how the skill finds pages.

This replaced `grep -ril` in the abap-wiki skill, so it inherits grep's
promise (if the words are there, the page is found) and adds one grep never
made: the page is found when the reader's words are not the vault's words.
Both are asserted here, along with the properties that keep the replacement
safe to make.

  - Ranking, not matching. A page named for the subject outranks one that
    mentions it once, or the reader reads the wrong page first.
  - Alias expansion. meta/entities.md is the normalisation the vault already
    does at ingest; a search for "Order-to-Cash" that misses OTC pages wastes
    the work.
  - Identifier parts. ABAP names carry meaning in their segments, and readers
    half-remember them.
  - Zone discipline. Nothing under raw/ or meta/ may ever be returned — the
    constitution forbids answering from unprocessed source material, and a
    search tool that surfaces it invites exactly that.
  - Degradation. No embedding index and no key must still produce results and
    still exit 0, because that is the state on every reader's laptop.

Builds a synthetic vault in a temp directory. No dependencies, no network.
Exits non-zero on regression.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
SEARCH_CLI = os.path.join(SCRIPTS, "vault-search.py")

sys.path.insert(0, SCRIPTS)
import vault_search as vs                              # noqa: E402
from vault_model import Vault                          # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    line = f"  {'PASS' if cond else 'FAIL'}  {name}"
    if detail and not cond:
        line += f"  — {detail}"
    print(line)


# --------------------------------------------------------------------------
# Fixture
# --------------------------------------------------------------------------

def page(front, body):
    lines = ["---"]
    for key, val in front.items():
        lines.append(f"{key}: {val}")
    lines += ["---", "", body]
    return "\n".join(lines) + "\n"


def fm(title, ptype, zone, ws="", status="active", tags="[]"):
    return {
        "title": f'"{title}"', "type": ptype, "zone": zone, "status": status,
        "owner": '"Curator"', "created": "2026-07-01", "updated": "2026-07-20",
        "workstream": ws, "tags": tags, "source_files": "[]",
    }


FILLER = ("The interface runs nightly and writes an application log entry for "
          "each processed record. Failures are retried twice before the run "
          "is marked incomplete. ") * 4

ENTITIES = """# Entity Registry

## Workstreams

| Canonical Slug | Display Name  | Aliases                                    | Status |
| -------------- | ------------- | ------------------------------------------ | ------ |
| OTC            | Order-to-Cash | `otc`, `o2c`, `order to cash`, `sd sales`  | active |
| INT            | Integrations  | `int`, `integration`, `integrations`       | active |

## SAP Modules

| Canonical Slug | Display Name         | Aliases                       | Status |
| -------------- | -------------------- | ----------------------------- | ------ |
| SD             | Sales & Distribution | `sd`, `sales and distribution`| active |
"""

FIXTURE = {
    # The page a search for "credit release" should reach first: it is named
    # for the subject.
    "02-workstreams/Decisions/OTC/Decision - OTC - Credit release approach - 2026-07-14.md": page(
        fm("Credit release approach", "decision", "02-workstreams", "OTC",
           tags="[sales-order, batch-job]"),
        "# Credit release approach\n\n## Decision\n\nKey-account orders are "
        "released by a custom periodic job rather than by standard FSCM "
        "configuration.\n\n[[OTC]]\n" + FILLER),

    # Mentions credit release once, in passing. Must not outrank the above.
    "02-workstreams/Meetings/OTC/OTC - Weekly sync - 2026-07-21.md": page(
        fm("Weekly sync", "meeting", "02-workstreams", "OTC"),
        "# Weekly sync\n\nStatus round. Credit release was mentioned once.\n\n"
        "[[OTC]]\n" + FILLER),

    "02-workstreams/Workstreams/OTC.md": page(
        fm("OTC", "workstream", "02-workstreams", "OTC"),
        "# OTC\n\n[[Decision - OTC - Credit release approach - 2026-07-14]]\n"
        + FILLER),

    # Reached by "order check" through identifier splitting.
    "02-workstreams/Developments/SD/SD - ZSD_ORDER_CHECK.md": page(
        fm("ZSD_ORDER_CHECK", "development", "02-workstreams", "SD",
           status="draft", tags="[ai-generated, sales-order]"),
        "# ZSD_ORDER_CHECK\n\nValidates incoming documents before pricing.\n\n"
        "[[SD - ZSD_PRICE_HELPER]]\n" + FILLER),

    # Never named by any query below, but one link from ZSD_ORDER_CHECK.
    "02-workstreams/Developments/SD/SD - ZSD_PRICE_HELPER.md": page(
        fm("ZSD_PRICE_HELPER", "development", "02-workstreams", "SD"),
        "# ZSD_PRICE_HELPER\n\nShared pricing routine.\n\n"
        "[[SD - ZSD_ORDER_CHECK]]\n" + FILLER),

    "03-intelligence/gotchas/Gotcha - Enqueue timeout on mass release.md": page(
        fm("Enqueue timeout", "gotcha", "03-intelligence", status="evergreen",
           tags="[locking, performance]"),
        "# Enqueue timeout\n\n> [!warning] CONFLICT — unresolved\n> Two sources "
        "disagree on the timeout value.\n\nMass release runs hit a lock wait.\n\n"
        "[[OTC]]\n" + FILLER),
}

NOISE = {
    "raw/inbox/transcript.md": "# Raw transcript\n\ncredit release credit release\n",
    "meta/index.md": "# Index\n\ncredit release credit release\n",
}


def build(root):
    for rel, text in FIXTURE.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    for rel, text in NOISE.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    with open(os.path.join(root, "meta", "entities.md"), "w", encoding="utf-8") as fh:
        fh.write(ENTITIES)


def names(root, query, **kwargs):
    hits, _ = vs.search(root, query, **kwargs)
    return [h.page.name for h in hits]


def cli(root, *args):
    env = dict(os.environ)
    for var in ("VOYAGE_API_KEY", "OPENAI_API_KEY"):
        env.pop(var, None)
    return subprocess.run([sys.executable, SEARCH_CLI, *args, "--root", root],
                          capture_output=True, text=True, env=env)


# --------------------------------------------------------------------------
# Tokenisation
# --------------------------------------------------------------------------

def test_tokenize():
    print("\nTokenisation")
    toks = vs.tokenize("ZSD_ORDER_CHECK")
    check("a compound identifier keeps its whole form", "zsd_order_check" in toks)
    check("and is also split into parts",
          {"zsd", "order", "check"} <= set(toks),
          "a reader who half-remembers the name must still find the page")
    check("two-letter SAP slugs survive", vs.tokenize("SD MM FI") == ["sd", "mm", "fi"],
          "the token floor is 2, not 3, or every module slug is dropped")
    check("english stopwords are dropped", vs.tokenize("the and of") == [])
    check("camelCase splits", {"sales", "order"} <= set(vs.tokenize("SalesOrder")))
    check("frontmatter is not body text",
          "source_files" not in vs.tokenize(
              vs.strip_frontmatter(FIXTURE[
                  "02-workstreams/Workstreams/OTC.md"])),
          "indexing the YAML block would rank every page for `owner` and "
          "`created`")


# --------------------------------------------------------------------------
# Ranking
# --------------------------------------------------------------------------

def test_ranking(root):
    print("\nRanking")
    ranked = names(root, "credit release")
    check("a page named for the subject ranks first",
          ranked[0] == "Decision - OTC - Credit release approach - 2026-07-14",
          f"got {ranked[:3]}")
    check("a passing mention ranks below it",
          ranked.index("OTC - Weekly sync - 2026-07-21") > 0, f"got {ranked}")

    check("identifier parts find the page",
          "SD - ZSD_ORDER_CHECK" in names(root, "order check"),
          "splitting ZSD_ORDER_CHECK is what makes this reachable")
    check("the full identifier finds it too",
          names(root, "ZSD_ORDER_CHECK")[0] == "SD - ZSD_ORDER_CHECK")

    check("a linked neighbour is pulled in",
          "SD - ZSD_PRICE_HELPER" in names(root, "ZSD_ORDER_CHECK"),
          "the graph boost exists so the object next to the answer comes too")

    check("tags are searchable",
          "Gotcha - Enqueue timeout on mass release" in names(root, "locking"))

    check("ranking is deterministic",
          names(root, "credit release") == names(root, "credit release"))


def test_aliases(root):
    print("\nAlias expansion")
    aliases = vs.load_aliases(root)
    check("the registry parses", aliases.get("order to cash") == "OTC", aliases)
    check("display names are aliases too", aliases.get("order-to-cash") == "OTC")
    check("header rows are not entities", "canonical slug" not in aliases)

    expanded = dict(vs.expand_query("Order-to-Cash credit", aliases))
    check("a multi-word alias expands to its slug", expanded.get("otc") == vs.ALIAS_WEIGHT)
    check("the reader's own words outweigh the expansion",
          expanded.get("credit") == 1.0)

    check("an aliased query reaches the canonical pages",
          any(n.startswith("Decision - OTC") for n in names(root, "order to cash")),
          "this is the whole point of reading meta/entities.md")

    check("literal mode does not expand",
          not any(n.startswith("Decision - OTC")
                  for n in names(root, "order to cash", literal=True))
          or names(root, "order to cash", literal=True)
          != names(root, "order to cash"),
          "literal mode exists for when the exact string is what is wanted")

    with tempfile.TemporaryDirectory() as bare:
        os.makedirs(os.path.join(bare, "meta"))
        check("a missing registry is not an error", vs.load_aliases(bare) == {})


def test_filters(root):
    print("\nFilters")
    check("--workstream restricts",
          set(names(root, "release", workstream="SD"))
          <= {"SD - ZSD_ORDER_CHECK", "SD - ZSD_PRICE_HELPER"})
    check("--type restricts",
          all(h.page.type == "decision"
              for h in vs.search(root, "credit", ptype="decision")[0]))
    check("--zone restricts",
          all(h.path.startswith("03-intelligence")
              for h in vs.search(root, "release", zone="03-intelligence")[0]))
    check("--top caps the result count",
          len(names(root, "release", top=2)) <= 2)


def test_zone_discipline(root):
    print("\nZone discipline")
    every = set()
    for query in ("credit release", "transcript", "index", "release"):
        every.update(h.path for h in vs.search(root, query, top=20)[0])
    check("nothing under raw/ is ever returned",
          not any(p.startswith("raw/") for p in every),
          "answering from unprocessed source material is forbidden")
    check("nothing under meta/ is ever returned",
          not any(p.startswith("meta/") for p in every),
          "meta pages are navigation, not answers")


def test_flags(root):
    print("\nProvisional-content flags")
    hits, _ = vs.search(root, "ZSD_ORDER_CHECK")
    hit = next(h for h in hits if h.page.name == "SD - ZSD_ORDER_CHECK")
    check("ai-generated is flagged unvalidated", "unvalidated" in hit.flags)
    check("draft status is flagged", "draft" in hit.flags)

    hits, _ = vs.search(root, "enqueue timeout")
    hit = next(h for h in hits if h.page.name.startswith("Gotcha"))
    check("an unresolved conflict is flagged first",
          hit.flags and hit.flags[0] == "unresolved conflict",
          "a reader must know the vault contradicts itself before they read it")


def test_degradation(root):
    print("\nDegradation")
    hits, meta = vs.search(root, "credit release")
    check("no vector index still returns results", bool(hits))
    check("and says why the semantic tier is off",
          meta["semantic"] is False and "embeddings.json" in meta["reason"],
          meta)

    hits, meta = vs.search(root, "the and of")
    check("a query of nothing but stopwords is not an error",
          hits == [] and meta["reason"] == "empty query")

    check("a query that matches nothing returns nothing",
          names(root, "kubernetes helm chart") == [])


def test_cli(root):
    print("\nCommand line")
    proc = cli(root, "credit release")
    check("exits 0", proc.returncode == 0, proc.stderr)
    check("names the top page",
          "Decision - OTC - Credit release approach" in proc.stdout, proc.stdout)
    check("says which tier ran", "lexical" in proc.stdout)
    check("shows the path", ".md" in proc.stdout)

    check("output is byte-identical on identical input",
          cli(root, "credit release").stdout == proc.stdout,
          "a search whose order moves between runs cannot be cited")

    paths = cli(root, "credit release", "--format", "paths").stdout.strip().splitlines()
    check("--format paths prints paths only",
          all(p.endswith(".md") for p in paths) and paths)

    proc = cli(root, "kubernetes helm chart")
    check("no match still exits 0", proc.returncode == 0)
    check("and says so in words", "No page scored" in proc.stdout, proc.stdout)

    proc = cli(root, "order to cash", "--explain")
    check("--explain shows the expanded terms", "terms:" in proc.stdout and
          "otc" in proc.stdout, proc.stdout)

    with tempfile.TemporaryDirectory() as bare:
        proc = cli(bare, "anything")
        check("an empty vault exits 0", proc.returncode == 0)
        check("and says it is empty", "no content pages" in proc.stdout)


def test_vault_untouched(root):
    print("\nRead-only")
    before = {p.path: p.raw for p in Vault(root).pages}
    cli(root, "credit release")
    after = {p.path: p.raw for p in Vault(root).pages}
    check("search writes nothing", before == after)


# --------------------------------------------------------------------------

def main():
    tmp = tempfile.mkdtemp()
    try:
        build(tmp)
        test_tokenize()
        test_ranking(tmp)
        test_aliases(tmp)
        test_filters(tmp)
        test_zone_discipline(tmp)
        test_flags(tmp)
        test_degradation(tmp)
        test_cli(tmp)
        test_vault_untouched(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
