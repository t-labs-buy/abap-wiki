#!/usr/bin/env python3
"""Graph health check for the ABAP vault.

Builds the wikilink graph from every content page in zones 01-04 and reports:

  - floating pages: no inbound and no outbound links     -> Core Behavior Rule 9
  - dead ends: no forward links at all                   -> Core Behavior Rule 12
  - backlink asymmetry: forward link with no matching
    entry in the target's "## Linked from" section       -> Linking Rules
  - unresolved wikilinks: targets with no page yet       -> allowed (Code Ingestion
                                                            Rule), reported for info
  - communities found by modularity clustering, flagged
    when one spans 2+ workstreams                        -> Pattern Promotion Rule
  - whether meta/communities.md still describes the
    graph as it now stands                               -> global-search layer

Read-only: writes no vault pages. Standard library only, no third-party deps.

Usage:
    python3 .github/scripts/graph-health.py [--out REPORT.md] [--strict]

--strict exits non-zero when a hard violation is found (floating pages, dead
ends, backlink asymmetry). Unresolved links never fail the run: the constitution
explicitly allows forward links to pages that do not exist yet. Nor do stale
community summaries: they mean the next ingest has work to do, not that the
vault is broken.
"""

import argparse
import collections
import os
import re
import sys

from vault_communities import partition
from vault_model import Vault

COMMUNITIES_MD = os.path.join("meta", "communities.md")
SIG_MARKER_RE = re.compile(r"<!--\s*sig:\s*([0-9a-f]+)\s+body:\s*([0-9a-f]+)\s*-->")


def recorded_summaries(root):
    """Signature -> body hash, as recorded in meta/communities.md.

    Returns None when the file does not exist — "never generated" and
    "generated but empty" are different states and the report says so.
    """
    path = os.path.join(root, COMMUNITIES_MD)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    return {sig: body for sig, body in SIG_MARKER_RE.findall(text)}


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def build_report(root):
    v = Vault(root)
    by_path = v.by_path

    floating = [p.path for p in v.pages
                if not v.forward_edges[p.path] and not v.inbound[p.path]]
    dead_ends = [p.path for p in v.pages
                 if not v.forward_edges[p.path] and v.inbound[p.path]]

    missing_backlinks = []   # (target, source) — target should list source
    for src, dests in sorted(v.forward_edges.items()):
        for dest in sorted(dests):
            if src not in v.declared_back[dest]:
                missing_backlinks.append((dest, src))

    stale_backlinks = []     # (page, claimed_source) — no such forward link
    for p in v.pages:
        for claimed in sorted(v.declared_back[p.path]):
            if p.path not in v.forward_edges[claimed]:
                stale_backlinks.append((p.path, claimed))

    # --- clustering ---------------------------------------------------------
    part = partition(v)
    cross_ws = [c for c in part if c.spans_workstreams]

    hubs = sorted(((p.path, v.degree(p.path)) for p in v.pages),
                  key=lambda kv: (-kv[1], kv[0]))[:5]
    edge_count = sum(len(d) for d in v.forward_edges.values())

    # --- render -------------------------------------------------------------
    out = []
    w = out.append

    w("# Vault graph health")
    w("")
    w(f"- Pages: **{len(v.pages)}**")
    w(f"- Forward links (resolved): **{edge_count}**")
    w(f"- Pages with no links either way: **{len(floating)}**")
    w(f"- Communities (finest level): **{len(part)}**"
      + (f", hierarchy depth {part.depth}" if part.depth else ""))
    w(f"- Unresolved link targets: **{len(v.unresolved)}** (allowed — pages not written yet)")
    w("")

    w("## Violations")
    w("")

    w("### Floating pages — Core Behavior Rule 9")
    w("")
    if floating:
        w("No inbound and no outbound links. The rule is explicit: never create floating pages.")
        w("")
        for path in floating:
            w(f"- `{path}`")
    else:
        w("None. Every page is attached to the graph.")
    w("")

    w("### Dead ends — Core Behavior Rule 12")
    w("")
    if dead_ends:
        w("Linked to by others, but link nowhere themselves. Every page must link to at least one related page.")
        w("")
        for path in dead_ends:
            w(f"- `{path}`")
    else:
        w("None. Every page links outward.")
    w("")

    w("### Missing backlinks — Linking Rules")
    w("")
    if missing_backlinks:
        w("A forward link exists, but the target's `## Linked from` section does not list the source.")
        w("")
        grouped = collections.defaultdict(list)
        for dest, src in missing_backlinks:
            grouped[dest].append(src)
        for dest in sorted(grouped):
            marker = "" if by_path[dest].has_backlink_section else "  _(no `## Linked from` section at all)_"
            w(f"- `{dest}`{marker}")
            for src in sorted(grouped[dest]):
                w(f"    - missing: `- [[{by_path[src].name}]] ({by_path[src].type or '?'})`")
    else:
        w("None. Every forward link has its reverse entry.")
    w("")

    w("### Stale backlinks")
    w("")
    if stale_backlinks:
        w("Listed under `## Linked from`, but the named page no longer links here.")
        w("")
        for path, claimed in stale_backlinks:
            w(f"- `{path}` claims a link from `{by_path[claimed].name}`")
    else:
        w("None.")
    w("")

    if v.self_links:
        w("### Self-links")
        w("")
        for path, target in v.self_links:
            w(f"- `{path}` links to itself via `[[{target}]]`")
        w("")

    w("## Communities")
    w("")
    w("Modularity clustering over the wikilink graph, finest level. "
      "A community spanning 2+ workstreams is a Pattern Promotion candidate.")
    w("")
    for com in part:
        label = ", ".join(com.workstreams) if com.workstreams else "no workstream"
        flag = "  **← spans 2+ workstreams**" if com.spans_workstreams else ""
        w(f"- **{len(com.members)} pages** ({label}){flag}")
        for path in com.members:
            w(f"    - {by_path[path].name} _({by_path[path].type or '?'})_")
    w("")

    if cross_ws:
        w(f"**{len(cross_ws)} community/communities span more than one workstream** — "
          "the Pattern Promotion Rule threshold. Review for a Zone 03 pattern page.")
    else:
        w("No community spans more than one workstream yet.")
    w("")

    w("### Summary coverage")
    w("")
    w(f"`{COMMUNITIES_MD}` is the vault's global-search layer — one summary per "
      "community, regenerated by the ingest run. Out-of-date summaries are "
      "reported here, never fixed here: this check never writes.")
    w("")
    recorded = recorded_summaries(root)
    if recorded is None:
        w(f"No `{COMMUNITIES_MD}` yet. Run `community-summarize.py` to build it.")
    elif not part:
        w("Nothing to summarise: the graph has no communities yet.")
    else:
        missing = [c for c in part if c.signature not in recorded]
        drifted = [c for c in part if c.signature in recorded
                   and recorded[c.signature] != c.body_hash(v)]
        current = len(part) - len(missing) - len(drifted)
        w(f"- Current: **{current}** of **{len(part)}**")
        w(f"- No summary yet: **{len(missing)}** (membership changed or new)")
        w(f"- Pages edited since the summary was written: **{len(drifted)}**")
        for com, reason in ([(c, "no summary") for c in missing]
                            + [(c, "pages edited") for c in drifted]):
            w(f"    - `{com.signature}` — {len(com.members)} pages "
              f"({', '.join(com.workstreams) or 'no workstream'}) — {reason}")
        if missing or drifted:
            w("")
            w("The next ingest run refreshes these. To do it now: "
              "`python3 .github/scripts/community-summarize.py`")
    w("")

    w("## Hubs")
    w("")
    for path, deg in hubs:
        w(f"- `{by_path[path].name}` — degree {deg}")
    w("")

    w("## Ambiguous page names")
    w("")
    if v.ambiguous:
        w("More than one page shares this basename, so a bare `[[link]]` is "
          "resolved by folder priority rather than by intent. Use the path form "
          "(`[[Open-Questions/OTC]]`) to disambiguate.")
        w("")
        for name in sorted(v.ambiguous):
            w(f"- `[[{name}]]` → resolves to `{v.resolve(name)}`")
            for path in v.ambiguous[name]:
                w(f"    - `{path}`")
    else:
        w("None.")
    w("")

    w("## Unresolved link targets")
    w("")
    if v.unresolved:
        w("Forward links to pages that do not exist yet. Permitted by the Code "
          "Ingestion Rule — listed so gaps stay visible.")
        w("")
        for target in sorted(v.unresolved):
            sources = ", ".join(f"`{by_path[s].name}`" for s in sorted(v.unresolved[target]))
            w(f"- `[[{target}]]` ← from {sources}")
    else:
        w("None.")
    w("")

    violations = len(floating) + len(dead_ends) + len(missing_backlinks) + len(stale_backlinks)
    return "\n".join(out), violations


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="vault root (default: cwd)")
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when a hard violation is found")
    args = ap.parse_args()

    report, violations = build_report(args.root)
    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")

    if args.strict and violations:
        print(f"\n{violations} hard violation(s) found.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
