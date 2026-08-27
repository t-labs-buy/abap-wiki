#!/usr/bin/env python3
"""Write meta/communities.md — the vault's global-search layer.

The wikilink graph is already clustered (vault_communities.py) and graph-health
already reports the clusters. This turns each cluster into something readable:
one LLM-written title and summary per community, so a question about the corpus
("what recurs across workstreams?", "what should I know before touching OTC?")
can be answered by orienting on a dozen summaries instead of grepping hundreds
of pages for words the answer may not contain.

Summaries are written at every level of the clustering hierarchy, and written
bottom-up: the finest level is summarised from the member pages, and every
coarser level from its children's summaries rather than from the pages again.
That is what keeps the cost near-flat — a coarse cluster reads a few hundred
words per child instead of the whole 40 KB budget — and it means a reader can
start at "what is this vault about" and zoom until the question is answered.

Three properties the output has to keep, because the vault depends on all three:

  1. It lives in meta/, never in zones 01-04. vault_model.Vault only scans the
     four content zones, so a file here is invisible to the graph. Anywhere else
     and graph-health reports it as a floating page and --strict fails.
  2. It contains no [[wikilinks]]. Page names are code spans. Generated
     scaffolding must not mint graph edges that graph-health then demands
     backlinks for — the same reason question-gen.py rewrites its links.
  3. Only the title and the prose come from the model. Member lists, sizes,
     workstreams, types, levels and hashes are computed here. A generated
     member list can drift from the vault; a computed one cannot.

Summaries are navigation, not evidence. The abap-wiki skill cites pages, never
communities: a summary points at which pages to open, and the answer is sourced
from those pages.

Incremental by default: a community whose membership and page bodies are
unchanged keeps its existing summary and costs nothing. Invalidation cascades
upward — a re-summarised child changes its parent's hash, so the coarse level
never describes a branch that has since been rewritten.

Usage:
    python3 .github/scripts/community-summarize.py [--root .] [--out FILE]
                                                   [--dry-run] [--force]

Needs ANTHROPIC_API_KEY to write prose. Without it the file is still generated
with its computed scaffolding and every summary marked pending, so the script
stays usable locally and in read-only contexts.
"""

import argparse
import datetime
import hashlib
import os
import re
import sys
import time

from vault_communities import MAX_COMMUNITY_SIZE, hierarchy, walk
from vault_model import Vault

OUT_REL = os.path.join("meta", "communities.md")

SUMMARY_MODEL = "claude-sonnet-5"
MAX_OUTPUT_TOKENS = 1_500
API_RETRIES = 3

# Characters of member-page text sent per community. Hubs go in full first, so
# an oversized community still describes its centre properly and thins at
# the edges rather than truncating mid-page.
COMMUNITY_CHAR_BUDGET = 40_000
EXCERPT_CHARS = 600

SUMMARY_WORD_CAP = 150

# A cached section: heading, marker, then the delimited prose. The middle is
# bounded so a pending section (no prose block) cannot swallow the next one.
CACHE_RE = re.compile(
    r"^#{3,6} [\d.]+ — (?P<title>.+?)\n"
    r"<!-- sig: (?P<sig>[0-9a-f]+) body: (?P<body>[0-9a-f]+)[^>]*-->\n"
    r"(?:(?!\n#{3,6} )[\s\S])*?"
    r"<!-- summary: begin -->\n(?P<prose>[\s\S]*?)\n<!-- summary: end -->",
    re.MULTILINE)

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

def strip_frontmatter(text):
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text if end == -1 else text[end + 4:]


def no_wikilinks(text):
    """Rewrite any [[link]] as a code span.

    Belt and braces: the prompt forbids them, but a model that emits one anyway
    would create a graph edge from a meta file, and the constitution is explicit
    that meta pages do not generate backlinks.
    """
    return WIKILINK_RE.sub(lambda m: f"`{m.group(1).strip()}`", text)


def one_paragraph(text, word_cap=SUMMARY_WORD_CAP):
    """Collapse to a single paragraph and enforce the word cap."""
    words = " ".join(text.split()).split(" ")
    if len(words) <= word_cap:
        return " ".join(words)
    return " ".join(words[:word_cap]).rstrip(",;:") + " …"


def page_line(vault, path):
    page = vault.by_path[path]
    return f"`{page.name}` ({page.type or '?'})"


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------

def read_cache(path):
    """signature -> (body_hash, title, prose) from a previous run."""
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    return {m.group("sig"): (m.group("body"), m.group("title").strip(),
                             m.group("prose").strip())
            for m in CACHE_RE.finditer(text)}


# --------------------------------------------------------------------------
# The model call
# --------------------------------------------------------------------------

def community_context(vault, com):
    """Member page text, hubs first, thinned to fit the budget."""
    rest = [p for p in com.members if p not in com.hubs]
    blocks, used = [], 0
    for path in com.hubs + rest:
        page = vault.by_path[path]
        body = strip_frontmatter(page.body).strip()
        if used + len(body) > COMMUNITY_CHAR_BUDGET:
            body = body[:EXCERPT_CHARS].rstrip() + "\n… (excerpt)"
        used += len(body)
        blocks.append(
            f"### {page.name}\n"
            f"(type: {page.type or '?'} · workstream: {page.workstream or '—'} · "
            f"status: {page.status or '?'})\n\n{body}")
    return "\n\n".join(blocks)


def rollup_hash(children, summaries):
    """Cache key for a coarse community: what its children currently say.

    A parent describes its children's summaries, not the pages, so the pages'
    body hash is the wrong invalidation signal — it would miss a child whose
    prose was rewritten and fire on an edit the parent's text never mentioned.
    Hashing the children's signatures, titles and prose makes invalidation
    cascade exactly one level at a time.
    """
    h = hashlib.sha256()
    for sig in sorted(node.signature for node in children):
        title, prose = summaries.get(sig, (None, None))
        h.update(sig.encode("utf-8"))
        h.update(b"\0")
        h.update((title or "").encode("utf-8"))
        h.update(b"\0")
        h.update((prose or "pending").encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:8]


def build_rollup_prompt(com, children, summaries):
    """The prompt for a coarse community: its children, already summarised."""
    blocks = []
    for child in children:
        title, prose = summaries.get(child.signature, (None, None))
        ws = ", ".join(child.community.workstreams) or "none recorded"
        blocks.append(f"### {title or 'untitled cluster'}\n"
                      f"({len(child.community.members)} pages · workstreams: {ws})\n\n"
                      f"{prose or 'No summary available for this sub-cluster.'}")

    return f"""You are summarising one broad area of an SAP ABAP delivery team's knowledge vault.

This area contains {len(children)} sub-clusters covering {len(com.members)} pages in total. Workstreams: {', '.join(com.workstreams) or 'none recorded'}. Each sub-cluster has already been summarised below; you are writing the level above them.

Your summary is read by a teammate orienting on the vault as a whole, before they know which sub-area they need. It is navigation, not evidence.

Return exactly this, nothing else:

TITLE: a 3-7 word name for what this whole area is ABOUT
SUMMARY: one paragraph, at most {SUMMARY_WORD_CAP} words

Rules:
- The title names the subject matter at the level of the whole area, not one of its parts, and not the page types it contains.
- Say what connects these sub-clusters — the shared business process, object family, or problem area — and where the weight of the work sits. Name specifics.
- Assert nothing that is not in the sub-cluster summaries below. They are your only source.
- Never write [[double brackets]]. Refer to pages and clusters by name in plain text.
- Carry forward any warning the sub-summaries raise about draft, unvalidated or conflicting content.

## Sub-clusters

{chr(10).join(blocks)}
"""


def build_prompt(vault, com):
    types = ", ".join(f"{t}×{n}" for t, n in sorted(com.types.items()))
    return f"""You are summarising one cluster of pages from an SAP ABAP delivery team's knowledge vault.

These {len(com.members)} pages were grouped together because they link to each other far more than they link to the rest of the vault. Types present: {types}. Workstreams: {', '.join(com.workstreams) or 'none recorded'}.

Your summary is read by a teammate deciding which pages to open. It is navigation, not evidence — they will read the actual pages before relying on anything.

Return exactly this, nothing else:

TITLE: a 3-7 word name for what this cluster is ABOUT
SUMMARY: one paragraph, at most {SUMMARY_WORD_CAP} words

Rules:
- The title names the subject matter, not the page types. "Credit release and FSCM gaps" is right; "Decisions and developments" is wrong — every cluster has decisions and developments, so that tells a reader nothing.
- The summary says what this area covers, what was decided, and what is still open or unresolved. Name the specific objects, decisions and constraints — a summary that would fit any cluster is useless.
- Assert nothing that is not in the pages below. No general SAP knowledge, no inference beyond what is written.
- Never write [[double brackets]]. Refer to pages by name in plain text.
- Where pages are marked draft, ai-generated or carry a CONFLICT block, say so — the reader needs to know the area is provisional before they trust it.

## Pages

{community_context(vault, com)}
"""


RESPONSE_RE = re.compile(r"TITLE:\s*(?P<title>.+?)\s*\n+SUMMARY:\s*(?P<summary>[\s\S]+)",
                         re.IGNORECASE)


def parse_response(text):
    m = RESPONSE_RE.search(text)
    if not m:
        return None, None
    title = one_paragraph(m.group("title"), word_cap=12)
    summary = one_paragraph(m.group("summary"))
    if not title or not summary:
        return None, None
    return no_wikilinks(title), no_wikilinks(summary)


def call_api_with_retry(client, sdk, prompt):
    """One call with backoff, mirroring call_api_with_retry() in abap-ingest.py.

    `sdk` is the anthropic module: the exception classes live on it, and
    importing it at module scope would make this script unusable anywhere the
    package is absent.
    """
    last_err = None
    for attempt in range(API_RETRIES):
        if attempt:
            wait = 15 * (2 ** attempt)
            print(f"    ⚠ API error ({last_err}) — retrying in {wait}s "
                  f"({attempt + 1}/{API_RETRIES})")
            time.sleep(wait)
        try:
            response = client.messages.create(
                model=SUMMARY_MODEL,
                max_tokens=MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""
        except sdk.RateLimitError as e:
            last_err = e
        except sdk.APIStatusError as e:
            if e.status_code < 500:
                print(f"    ⚠ Non-retryable API error {e.status_code}: {e.message}")
                return None
            last_err = e
        except sdk.APIConnectionError as e:
            last_err = e
    print(f"    ⚠ API failed after {API_RETRIES} attempts: {last_err}")
    return None


def get_client():
    """(client, anthropic module) on success, (None, reason) on failure.

    Never raises: no key and no package are ordinary states here, not errors —
    the file is still worth generating without prose.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "ANTHROPIC_API_KEY is not set"
    try:
        import anthropic
    except ImportError:
        return None, "the anthropic package is not installed"
    return (anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]),
            anthropic)


# --------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------

PREAMBLE = """# Vault Communities

_Generated by `.github/scripts/community-summarize.py`. Do not hand-edit — the next ingest run overwrites it._

> Clusters found by modularity over the wikilink graph: pages that link to each
> other far more than to the rest of the vault. This file exists to answer
> questions about the vault as a whole, by pointing at which pages to read.
>
> **It is a tree, broadest first.** The Index is the whole vault in a handful of
> areas — start there when the question is about the corpus. An area too large
> to describe as one thing is written out with its sub-clusters nested beneath
> it. Zoom until the question is answered; the clusters that name individual
> pages are the leaves. Then open those pages.
>
> **Never cite a community — cite the pages it names.** A summary is written by
> a model from the pages below it and can fall behind an edit; the pages are the
> source of truth."""


def heading_for(node):
    """`###` at the top, one deeper per level, capped so markdown stays valid."""
    return "#" * min(3 + node.level, 6)


def render(vault, roots, summaries, hashes, unclustered, today):
    """summaries: signature -> (title, prose or None). Broadest first."""
    out = []
    w = out.append

    w(PREAMBLE)
    w("")

    nodes = list(walk(roots))
    if not nodes:
        w(f"_Last updated: {today} · no communities yet._")
        w("")
        w("The graph has no clusters: the vault has no linked content pages yet. "
          "This file fills in as pages are ingested.")
        w("")
        return "\n".join(out)

    linked = len({m for n in nodes for m in n.community.members})
    depth = max(n.level for n in nodes) + 1
    plural = "level" if depth == 1 else "levels"
    w(f"_Last updated: {today} · {len(nodes)} communities across {depth} "
      f"{plural} · {linked} linked pages_")
    if unclustered:
        w("")
        w(f"_{len(unclustered)} page(s) link nowhere and belong to no "
          "community — see the floating-page section of the graph-health report._")
    w("")

    w("## Index")
    w("")
    w("The broadest areas. Each one is written out below, with its sub-clusters "
      "nested underneath it."
      if depth > 1 else
      "The vault's clusters. None of them is large enough to split further.")
    w("")
    w("| # | Area | Pages | Splits into | Workstreams |")
    w("| - | ---- | ----- | ----------- | ----------- |")
    for root in roots:
        com = root.community
        title = summaries[com.signature][0]
        ws = ", ".join(com.workstreams) or "—"
        w(f"| {root.number} | {title} | {len(com.members)} | "
          f"{len(root.children) or '—'} | {ws} |")
    w("")

    for root in roots:
        w("---")
        w("")
        for node in root:
            com = node.community
            title, prose = summaries[com.signature]
            w(f"{heading_for(node)} {node.number} — {title}")
            w(f"<!-- sig: {com.signature} body: {hashes[com.signature]} "
              f"level: {node.level} -->")
            w("")
            flag = " · **spans 2+ workstreams**" if com.spans_workstreams else ""
            w(f"**Workstreams:** {', '.join(com.workstreams) or '—'} · "
              f"**Pages:** {len(com.members)}{flag}")
            w("")
            if prose:
                w("<!-- summary: begin -->")
                w(prose)
                w("<!-- summary: end -->")
            else:
                w("_No summary yet — the next run with an API key writes one._")
            w("")

            if node.children:
                w("**Splits into:** " + ", ".join(
                    f"{kid.number} `{summaries[kid.signature][0]}` "
                    f"({len(kid.community.members)} pages)"
                    for kid in node.children))
                w("")
            w("**Start here:** " + ", ".join(page_line(vault, p) for p in com.hubs))
            w("")
            if not node.children:
                w("**All pages:** " + ", ".join(page_line(vault, p) for p in com.members))
                w("")

    return "\n".join(out)


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="vault root (default: cwd)")
    ap.add_argument("--out", help=f"output file (default: <root>/{OUT_REL})")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; write nothing, call nothing")
    ap.add_argument("--force", action="store_true",
                    help="re-summarise every community, ignoring the cache")
    ap.add_argument("--max-cluster-size", type=int, default=MAX_COMMUNITY_SIZE,
                    help=f"split any cluster larger than this into sub-clusters "
                         f"(default: {MAX_COMMUNITY_SIZE})")
    ap.add_argument("--today", help="override the date stamp (testing)")
    args = ap.parse_args()

    out_path = args.out or os.path.join(args.root, OUT_REL)
    today = args.today or datetime.date.today().isoformat()

    vault = Vault(args.root)
    roots = hierarchy(vault, max_size=args.max_cluster_size)
    cache = {} if args.force else read_cache(out_path)

    nodes = list(walk(roots))
    linked = {m for n in nodes for m in n.community.members}
    unclustered = sorted(p.path for p in vault.pages if p.path not in linked)
    depth = (max(n.level for n in nodes) + 1) if nodes else 0
    print(f"{len(vault.pages)} pages · {len(nodes)} communities "
          f"across {depth} level(s)")

    client = sdk = None
    summaries, hashes = {}, {}
    reused = written = pending = 0
    planned = []

    # Deepest first, so a parent is always rolled up from children whose prose
    # already exists. Sorting by -level is enough: a child is strictly deeper
    # than its parent, and siblings do not depend on each other.
    for node in sorted(nodes, key=lambda n: (-n.level, n.number)):
        com = node.community
        if node.children:
            want = rollup_hash(node.children, summaries)
        else:
            want = com.body_hash(vault)

        hit = cache.get(com.signature)
        if hit and hit[0] == want:
            summaries[com.signature] = (hit[1], hit[2])
            hashes[com.signature] = want
            reused += 1
            continue

        label = (f"{node.number} {com.signature}: {len(com.members)} pages "
                 f"({', '.join(com.workstreams) or 'no workstream'})")
        planned.append(label)
        if args.dry_run:
            summaries[com.signature] = (fallback_title(com), None)
            hashes[com.signature] = "pending"
            continue

        if client is None and sdk is None:
            client, sdk = get_client()
            if client is None:
                print(f"  ⚠ {sdk} — writing scaffolding only, "
                      f"remaining communities left pending")
        if client is None:
            summaries[com.signature] = (fallback_title(com), None)
            hashes[com.signature] = "pending"
            pending += 1
            continue

        print(f"  summarising {label}")
        prompt = (build_rollup_prompt(com, node.children, summaries)
                  if node.children else build_prompt(vault, com))
        text = call_api_with_retry(client, sdk, prompt)
        title, prose = parse_response(text) if text else (None, None)
        if prose is None:
            print("    ⚠ no usable summary — left pending")
            summaries[com.signature] = (fallback_title(com), None)
            hashes[com.signature] = "pending"
            pending += 1
        else:
            summaries[com.signature] = (title, prose)
            hashes[com.signature] = want
            written += 1

    if args.dry_run:
        print(f"  would reuse {reused}, would summarise {len(planned)}")
        for label in planned:
            print(f"    - {label}")
        return 0

    report = render(vault, roots, summaries, hashes, unclustered, today)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")

    print(f"  wrote {out_path}: {reused} reused, {written} new, "
          f"{pending} pending")
    return 0


def fallback_title(com):
    """Title when there is no prose: honest about being mechanical."""
    ws = "/".join(com.workstreams) or "unassigned"
    return f"{ws} — {com.dominant_type()} cluster"


if __name__ == "__main__":
    sys.exit(main())
