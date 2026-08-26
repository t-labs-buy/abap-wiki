#!/usr/bin/env python3
"""Write meta/communities.md — the vault's global-search layer.

The wikilink graph is already clustered (vault_communities.py) and graph-health
already reports the clusters. This turns each cluster into something readable:
one LLM-written title and summary per community, so a question about the corpus
("what recurs across workstreams?", "what should I know before touching OTC?")
can be answered by orienting on a dozen summaries instead of grepping hundreds
of pages for words the answer may not contain.

Three properties the output has to keep, because the vault depends on all three:

  1. It lives in meta/, never in zones 01-04. vault_model.Vault only scans the
     four content zones, so a file here is invisible to the graph. Anywhere else
     and graph-health reports it as a floating page and --strict fails.
  2. It contains no [[wikilinks]]. Page names are code spans. Generated
     scaffolding must not mint graph edges that graph-health then demands
     backlinks for — the same reason question-gen.py rewrites its links.
  3. Only the title and the prose come from the model. Member lists, sizes,
     workstreams, types and hashes are computed here. A generated member list
     can drift from the vault; a computed one cannot.

Summaries are navigation, not evidence. The abap-wiki skill cites pages, never
communities: a summary points at which pages to open, and the answer is sourced
from those pages.

Incremental by default: a community whose membership and page bodies are
unchanged keeps its existing summary and costs nothing.

Usage:
    python3 .github/scripts/community-summarize.py [--root .] [--out FILE]
                                                   [--dry-run] [--force]

Needs ANTHROPIC_API_KEY to write prose. Without it the file is still generated
with its computed scaffolding and every summary marked pending, so the script
stays usable locally and in read-only contexts.
"""

import argparse
import datetime
import os
import re
import sys
import time

from vault_communities import partition
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
    r"^## \d+ — (?P<title>.+?)\n"
    r"<!-- sig: (?P<sig>[0-9a-f]+) body: (?P<body>[0-9a-f]+) -->\n"
    r"(?:(?!\n## )[\s\S])*?"
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
> **Never cite a community — cite the pages it names.** A summary is written by
> a model from the pages below it and can fall behind an edit; the pages are the
> source of truth."""


def render(vault, part, summaries, today):
    """summaries: signature -> (title, prose or None)."""
    out = []
    w = out.append

    w(PREAMBLE)
    w("")

    if not part:
        w(f"_Last updated: {today} · no communities yet._")
        w("")
        w("The graph has no clusters: the vault has no linked content pages yet. "
          "This file fills in as pages are ingested.")
        w("")
        return "\n".join(out)

    pages = sum(len(c.members) for c in part)
    w(f"_Last updated: {today} · {len(part)} communities over {pages} linked "
      f"pages · hierarchy depth {part.depth}_")
    if part.unclustered:
        w("")
        w(f"_{len(part.unclustered)} page(s) link nowhere and belong to no "
          "community — see the floating-page section of the graph-health report._")
    w("")

    w("## Index")
    w("")
    w("| # | Community | Pages | Workstreams |")
    w("| - | --------- | ----- | ----------- |")
    for i, com in enumerate(part, 1):
        title = summaries[com.signature][0]
        ws = ", ".join(com.workstreams) or "—"
        w(f"| {i} | {title} | {len(com.members)} | {ws} |")
    w("")

    for i, com in enumerate(part, 1):
        title, prose = summaries[com.signature]
        w("---")
        w("")
        w(f"## {i} — {title}")
        body = com.body_hash(vault) if prose else "pending"
        w(f"<!-- sig: {com.signature} body: {body} -->")
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
        w("**Start here:** " + ", ".join(page_line(vault, p) for p in com.hubs))
        w("")
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
    ap.add_argument("--today", help="override the date stamp (testing)")
    args = ap.parse_args()

    out_path = args.out or os.path.join(args.root, OUT_REL)
    today = args.today or datetime.date.today().isoformat()

    vault = Vault(args.root)
    part = partition(vault)
    cache = {} if args.force else read_cache(out_path)

    print(f"{len(vault.pages)} pages · {len(part)} communities")

    fresh, cached, pending = [], [], []
    for com in part:
        hit = cache.get(com.signature)
        if hit and hit[0] == com.body_hash(vault):
            cached.append(com)
        else:
            fresh.append(com)

    if args.dry_run:
        print(f"  would reuse {len(cached)}, would summarise {len(fresh)}")
        for com in fresh:
            print(f"    - {com.signature}: {len(com.members)} pages "
                  f"({', '.join(com.workstreams) or 'no workstream'})")
        return 0

    summaries = {}
    for com in cached:
        _, title, prose = cache[com.signature]
        summaries[com.signature] = (title, prose)

    client = sdk = None
    if fresh:
        client, sdk = get_client()
        if client is None:
            print(f"  ⚠ {sdk} — writing scaffolding only, "
                  f"{len(fresh)} community/communities left pending")

    for com in fresh:
        label = f"{len(com.members)} pages ({', '.join(com.workstreams) or 'no workstream'})"
        if client is None:
            summaries[com.signature] = (fallback_title(com), None)
            pending.append(com)
            continue
        print(f"  summarising {com.signature}: {label}")
        text = call_api_with_retry(client, sdk, build_prompt(vault, com))
        title, prose = parse_response(text) if text else (None, None)
        if prose is None:
            print(f"    ⚠ no usable summary — left pending")
            summaries[com.signature] = (fallback_title(com), None)
            pending.append(com)
        else:
            summaries[com.signature] = (title, prose)

    report = render(vault, part, summaries, today)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")

    written = len(fresh) - len(pending)
    print(f"  wrote {out_path}: {len(cached)} reused, {written} new, "
          f"{len(pending)} pending")
    return 0


def fallback_title(com):
    """Title when there is no prose: honest about being mechanical."""
    ws = "/".join(com.workstreams) or "unassigned"
    return f"{ws} — {com.dominant_type()} cluster"


if __name__ == "__main__":
    sys.exit(main())
