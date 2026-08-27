#!/usr/bin/env python3
"""Gate for embed-index.py — the vault's committed vector index.

The index is unusual for this repo: it is a binary blob a reader cannot
inspect, produced by a paid API, and consumed on machines that have neither
the API key nor any way to tell a good vector from a bad one. So the
properties that matter are mostly about what happens when something is wrong.

  - Absent is a normal state. No key, no package, no network, no index: every
    one of these must exit 0 and leave search working. The reader's laptop is
    in this state by default and always will be.
  - Never a half-written index. A failed provider call in the middle of a
    batch must leave the committed index exactly as it was, because a manifest
    that disagrees with its blob returns confidently wrong neighbours.
  - Never two embedding spaces in one file. A changed model rebuilds from
    scratch rather than mixing dimensions or, worse, mixing meanings.
  - Honest entries. Every path named in the manifest is a page that exists —
    the same promise prompt_suggest_test.py and community_test.py enforce for
    everything else generated into meta/.
  - Incremental. A one-page ingest re-embeds one page, or the index costs real
    money on every run and someone turns it off.

The provider is stubbed throughout: deterministic pseudo-vectors derived from
the text, so the same text always embeds the same way and a test can assert on
ordering. No network, no key, no dependencies.
"""
import hashlib
import importlib.util
import json
import math
import os
import random
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)

sys.path.insert(0, SCRIPTS)
import vault_search as vs                               # noqa: E402
from vault_model import Vault                           # noqa: E402

spec = importlib.util.spec_from_file_location(
    "embed_index", os.path.join(SCRIPTS, "embed-index.py"))
ei = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ei)

DIM = 32
RESULTS = []
CALLS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    line = f"  {'PASS' if cond else 'FAIL'}  {name}"
    if detail and not cond:
        line += f"  — {detail}"
    print(line)


# --------------------------------------------------------------------------
# Stub provider
# --------------------------------------------------------------------------

def stub_embed(texts, input_type=None, timeout=60, dim=DIM, fail_at=None):
    """Deterministic pseudo-embeddings: same text, same vector, every run."""
    out = []
    for i, text in enumerate(texts):
        if fail_at is not None and len(CALLS) + i >= fail_at:
            return None
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)
        rng = random.Random(seed)
        out.append([rng.gauss(0.0, 1.0) for _ in range(dim)])
    CALLS.extend(texts)
    return out


def install_stub(**kwargs):
    CALLS.clear()
    vs.embed_texts = lambda texts, input_type=None, timeout=60: stub_embed(
        texts, input_type, timeout, **kwargs)
    ei.vault_search.embed_texts = vs.embed_texts


def run_index(root, *args):
    argv = sys.argv
    try:
        sys.argv = ["embed-index.py", "--root", root, *args]
        return ei.main()
    finally:
        sys.argv = argv


# --------------------------------------------------------------------------
# Fixture
# --------------------------------------------------------------------------

def page(front, body):
    lines = ["---"]
    for key, val in front.items():
        lines.append(f"{key}: {val}")
    lines += ["---", "", body]
    return "\n".join(lines) + "\n"


def fm(title, ptype, ws=""):
    return {
        "title": f'"{title}"', "type": ptype, "zone": "02-workstreams",
        "status": "active", "owner": '"Curator"', "created": "2026-07-01",
        "updated": "2026-07-20", "workstream": ws, "tags": "[]",
        "source_files": "[]",
    }


SHORT = "A short page. It says one thing and links onward.\n\n[[OTC]]\n"

LONG_SECTION = ("Each step is written out so the reader can follow it without "
                "asking anyone. The transport is released only after the "
                "checks below have all passed. ") * 6

LONG = ("# Runbook\n\n"
        + "".join(f"## Step {i}\n\n{LONG_SECTION}\n\n" for i in range(1, 5))
        + "[[OTC]]\n")

FIXTURE = {
    "02-workstreams/Workstreams/OTC.md": page(
        fm("OTC", "workstream", "OTC"), "# OTC\n\n[[OTC - Short note]]\n" + SHORT),
    "02-workstreams/Specs/OTC/OTC - Short note.md": page(
        fm("Short note", "spec", "OTC"), "# Short note\n\n" + SHORT),
    "02-workstreams/Specs/OTC/OTC - Long runbook.md": page(
        fm("Long runbook", "spec", "OTC"), LONG),
}


def build(root):
    for rel, text in FIXTURE.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    os.makedirs(os.path.join(root, "meta"), exist_ok=True)


def manifest_of(root):
    with open(os.path.join(root, vs.EMBED_MANIFEST), encoding="utf-8") as fh:
        return json.load(fh)


def index_exists(root):
    return os.path.isfile(os.path.join(root, vs.EMBED_MANIFEST))


# --------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------

def test_units(root):
    print("\nUnits")
    vault = Vault(root)
    short = vault.by_path["02-workstreams/Specs/OTC/OTC - Short note.md"]
    long_page = vault.by_path["02-workstreams/Specs/OTC/OTC - Long runbook.md"]

    check("a short page is one unit", len(ei.units_for(short)) == 1)
    units = ei.units_for(long_page)
    check("a long page also gets section units", len(units) > 1,
          "a twelve-step runbook must be findable by the step somebody needs")
    check("the page unit comes first", units[0][0] == "page")
    check("sections carry their heading",
          all(u[1] for u in units[1:]) and units[1][1].startswith("Step"))
    check("every unit names its page",
          all(long_page.name in u[2] for u in units),
          "the name is the most compressed statement of what a page is")
    check("frontmatter is not embedded",
          all("source_files" not in u[2] for u in units))
    check("a unit is capped", all(len(u[2]) <= ei.PAGE_CHAR_BUDGET for u in units))


# --------------------------------------------------------------------------
# Degradation
# --------------------------------------------------------------------------

def test_no_key(root):
    print("\nNo key")
    vs.embed_texts = lambda *a, **k: None      # what happens with no credentials
    ei.vault_search.embed_texts = vs.embed_texts
    for var in ("VOYAGE_API_KEY", "OPENAI_API_KEY"):
        os.environ.pop(var, None)

    check("exits 0 with no key", run_index(root) == 0)
    check("writes no index", not index_exists(root),
          "a manifest with no vectors behind it is worse than none")

    hits, meta = vs.search(root, "short page")
    check("search still works", bool(hits) and meta["semantic"] is False)


def test_dry_run(root):
    print("\nDry run")
    os.environ["VOYAGE_API_KEY"] = "stub"
    install_stub()
    check("exits 0", run_index(root, "--dry-run") == 0)
    check("calls the provider not at all", not CALLS)
    check("writes nothing", not index_exists(root))


# --------------------------------------------------------------------------
# Building
# --------------------------------------------------------------------------

def test_build(root):
    print("\nBuild")
    install_stub()
    check("exits 0", run_index(root) == 0)
    check("writes both files", index_exists(root)
          and os.path.isfile(os.path.join(root, vs.EMBED_BIN)))

    manifest = manifest_of(root)
    blob = os.path.getsize(os.path.join(root, vs.EMBED_BIN))
    check("the blob matches the manifest",
          blob == manifest["dim"] * len(manifest["entries"]),
          f"{blob} bytes vs {manifest['dim']}×{len(manifest['entries'])}")
    check("the model is recorded", manifest["model"] and manifest["provider"])
    check("quantisation is recorded", manifest["quantisation"] == "int8")

    vault = Vault(root)
    named = {e["path"] for e in manifest["entries"]}
    check("every path in the manifest exists",
          named <= set(vault.by_path), sorted(named - set(vault.by_path)))
    check("every page is covered",
          {p.path for p in vault.pages} <= named)
    check("nothing outside the content zones is embedded",
          not any(p.startswith(("raw/", "meta/")) for p in named))

    check("the index loads back",
          vs.load_embeddings(root)[0] is not None)
    check("vectors are int8",
          all(-127 <= x <= 127 for x in vs.load_embeddings(root)[1]))


def test_incremental(root):
    print("\nIncremental")
    install_stub()
    run_index(root)
    check("an unchanged vault re-embeds nothing", not CALLS, f"{len(CALLS)} calls")

    target = os.path.join(root, "02-workstreams/Specs/OTC/OTC - Short note.md")
    with open(target, "a", encoding="utf-8") as fh:
        fh.write("\nA sentence added after the index was built.\n")

    install_stub()
    run_index(root)
    check("an edited page re-embeds only its own units", len(CALLS) == 1,
          f"{len(CALLS)} units re-embedded")

    install_stub()
    run_index(root, "--force")
    check("--force re-embeds everything",
          len(CALLS) == len(manifest_of(root)["entries"]))

    os.remove(target)
    install_stub()
    run_index(root)
    named = {e["path"] for e in manifest_of(root)["entries"]}
    check("a deleted page loses its vectors",
          "02-workstreams/Specs/OTC/OTC - Short note.md" not in named)
    check("and nothing is re-embedded to do it", not CALLS)

    with open(target, "w", encoding="utf-8") as fh:
        fh.write(FIXTURE["02-workstreams/Specs/OTC/OTC - Short note.md"])
    install_stub()
    run_index(root)


def test_model_change(root):
    print("\nModel change")
    before = manifest_of(root)
    os.environ["VAULT_EMBED_MODEL"] = "some-other-model"
    install_stub(dim=DIM * 2)
    try:
        run_index(root)
        after = manifest_of(root)
        check("a new model rebuilds from scratch",
              len(CALLS) == len(after["entries"]),
              "reusing vectors across models mixes two meaning spaces")
        check("the new dimension is recorded", after["dim"] == DIM * 2
              and after["dim"] != before["dim"])
        check("the blob was rewritten to match",
              os.path.getsize(os.path.join(root, vs.EMBED_BIN))
              == after["dim"] * len(after["entries"]))
    finally:
        os.environ.pop("VAULT_EMBED_MODEL", None)
        install_stub()
        run_index(root, "--force")


def test_provider_failure(root):
    print("\nProvider failure")
    before_manifest = manifest_of(root)
    before_blob = open(os.path.join(root, vs.EMBED_BIN), "rb").read()

    with open(os.path.join(root, "02-workstreams/Specs/OTC/OTC - New page.md"),
              "w", encoding="utf-8") as fh:
        fh.write(page(fm("New page", "spec", "OTC"), "# New page\n\n" + SHORT))

    install_stub(fail_at=0)
    check("a failed call still exits 0", run_index(root) == 0)
    check("the committed manifest is untouched",
          manifest_of(root) == before_manifest,
          "a half-written index returns confidently wrong neighbours")
    check("the committed blob is untouched",
          open(os.path.join(root, vs.EMBED_BIN), "rb").read() == before_blob)

    os.remove(os.path.join(root, "02-workstreams/Specs/OTC/OTC - New page.md"))
    install_stub()
    run_index(root)


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def test_quantisation():
    print("\nQuantisation")
    rng = random.Random(11)
    query = vs.normalise([rng.gauss(0, 1) for _ in range(256)])
    docs = [vs.normalise([rng.gauss(0, 1) for _ in range(256)])
            for _ in range(60)]

    exact = sorted(range(len(docs)),
                   key=lambda i: -sum(q * d for q, d in zip(query, docs[i])))
    quantised = sorted(
        range(len(docs)),
        key=lambda i: -sum(q * v for q, v in zip(query, vs.quantise(docs[i]))))

    check("int8 preserves the top-5 ordering", exact[:5] == quantised[:5],
          f"{exact[:5]} vs {quantised[:5]}")
    check("a unit vector round-trips within tolerance",
          all(abs(x / vs.QUANT_SCALE - y) < 0.01
              for x, y in zip(vs.quantise(docs[0]), docs[0])))


def test_corrupt(root):
    print("\nCorrupt index")
    bin_path = os.path.join(root, vs.EMBED_BIN)
    manifest_path = os.path.join(root, vs.EMBED_MANIFEST)
    good_blob = open(bin_path, "rb").read()
    good_manifest = open(manifest_path, encoding="utf-8").read()

    with open(bin_path, "wb") as fh:
        fh.write(good_blob[:-5])
    check("a truncated blob reads as absent",
          vs.load_embeddings(root)[0] is None,
          "a blob that disagrees with its manifest must never be used")
    hits, meta = vs.search(root, "short page")
    check("and search falls back to lexical", bool(hits) and not meta["semantic"])

    with open(bin_path, "wb") as fh:
        fh.write(good_blob)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        fh.write("{not json")
    check("an unparseable manifest reads as absent",
          vs.load_embeddings(root)[0] is None)

    with open(manifest_path, "w", encoding="utf-8") as fh:
        fh.write(good_manifest)
    check("the good index loads again", vs.load_embeddings(root)[0] is not None)


def test_fusion(root):
    print("\nFusion")
    install_stub()
    hits, meta = vs.search(root, "short page")
    check("the semantic tier runs when the index is there", meta["semantic"] is True)
    check("results still come back", bool(hits))
    check("every result is a real page",
          all(h.path in Vault(root).by_path for h in hits))

    lexical_only, _ = vs.search(root, "short page", semantic=False)
    check("turning it off changes nothing about validity", bool(lexical_only))

    fused = vs.fuse({"a": 10.0, "b": 1.0}, {"b": 0.9, "c": 0.8})
    check("fusion is by rank, not by score",
          fused["b"] > fused["a"] and fused["b"] > fused["c"],
          "b is ranked in both lists; a wins one list on an incomparable scale")

    check("a page missing from one tier still ranks", "c" in fused)


# --------------------------------------------------------------------------

def main():
    tmp = tempfile.mkdtemp()
    real_embed = vs.embed_texts
    try:
        build(tmp)
        test_units(tmp)
        test_no_key(tmp)
        test_dry_run(tmp)
        test_build(tmp)
        test_incremental(tmp)
        test_model_change(tmp)
        test_provider_failure(tmp)
        test_quantisation()
        test_corrupt(tmp)
        test_fusion(tmp)
    finally:
        vs.embed_texts = real_embed
        shutil.rmtree(tmp, ignore_errors=True)

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
