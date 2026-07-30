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

Read-only: writes no vault pages. Standard library only, no third-party deps.

Usage:
    python3 .github/scripts/graph-health.py [--out REPORT.md] [--strict]

--strict exits non-zero when a hard violation is found (floating pages, dead
ends, backlink asymmetry). Unresolved links never fail the run: the constitution
explicitly allows forward links to pages that do not exist yet.
"""

import argparse
import collections
import sys

from vault_model import Vault

# Clustering resolution. 1.0 is standard modularity; higher splits more finely.
RESOLUTION = 1.0


# --------------------------------------------------------------------------
# Community detection (Louvain modularity optimisation)
# --------------------------------------------------------------------------
#
# GraphRAG uses hierarchical Leiden. Leiden adds a refinement phase that
# guarantees every community is internally well-connected; on a graph this size
# the two agree, so this is plain Louvain — deterministic node ordering, no
# randomness, no third-party dependency.

def louvain_one_level(adj, resolution=RESOLUTION):
    """One pass of local moving. adj: {node: {neighbour: weight}} with self
    loops allowed. Returns {node: community_id}."""
    nodes = sorted(adj)
    degree = {n: sum(adj[n].values()) + adj[n].get(n, 0) for n in nodes}
    total = sum(degree.values()) / 2.0
    if total == 0:
        return {n: i for i, n in enumerate(nodes)}

    node2com = {n: i for i, n in enumerate(nodes)}
    com_tot = {i: degree[n] for i, n in enumerate(nodes)}

    improved = True
    while improved:
        improved = False
        for n in nodes:
            own = node2com[n]
            k_n = degree[n]

            # weight from n into each neighbouring community, self loop excluded
            weights = collections.defaultdict(float)
            for nbr, w in adj[n].items():
                if nbr != n:
                    weights[node2com[nbr]] += w

            com_tot[own] -= k_n
            best_com = own
            best_gain = weights.get(own, 0.0) - resolution * com_tot[own] * k_n / (2.0 * total)
            for com in sorted(weights):
                gain = weights[com] - resolution * com_tot[com] * k_n / (2.0 * total)
                if gain > best_gain + 1e-12:
                    best_com, best_gain = com, gain
            com_tot[best_com] += k_n

            if best_com != own:
                node2com[n] = best_com
                improved = True

    return node2com


def louvain(adj):
    """Full hierarchical Louvain. Returns a list of levels, each a
    {original_node: community_id} mapping, coarsest last."""
    levels = []
    membership = {n: n for n in adj}
    current = {n: dict(nbrs) for n, nbrs in adj.items()}

    while True:
        partition = louvain_one_level(current)
        n_before, n_after = len(current), len(set(partition.values()))
        membership = {orig: partition[com] for orig, com in membership.items()}
        levels.append(dict(membership))
        if n_after == n_before or n_after == 1:
            break

        aggregated = collections.defaultdict(lambda: collections.defaultdict(float))
        for u, nbrs in current.items():
            for v, w in nbrs.items():
                aggregated[partition[u]][partition[v]] += w
        current = {u: dict(nbrs) for u, nbrs in aggregated.items()}

    return levels


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
    adj = collections.defaultdict(dict)
    for p in v.pages:
        adj[p.path] = {}
    for src, dests in v.forward_edges.items():
        for dest in dests:
            # reciprocal links weigh double
            adj[src][dest] = adj[src].get(dest, 0.0) + 1.0
            adj[dest][src] = adj[dest].get(src, 0.0) + 1.0

    connected = {n: nbrs for n, nbrs in adj.items() if nbrs}
    levels = louvain(connected) if connected else []
    partition = levels[0] if levels else {}

    communities = collections.defaultdict(list)
    for node, com in partition.items():
        communities[com].append(node)

    def workstreams_of(paths_):
        return {by_path[p].workstream for p in paths_ if by_path[p].workstream}

    ranked = sorted(communities.values(),
                    key=lambda members: (-len(members), sorted(members)[0]))
    cross_ws = [m for m in ranked if len(workstreams_of(m)) > 1]

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
    w(f"- Communities (finest level): **{len(communities)}**"
      + (f", hierarchy depth {len(levels)}" if levels else ""))
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
    for members in ranked:
        ws = workstreams_of(members)
        label = ", ".join(sorted(ws)) if ws else "no workstream"
        flag = "  **← spans 2+ workstreams**" if len(ws) > 1 else ""
        w(f"- **{len(members)} pages** ({label}){flag}")
        for path in sorted(members):
            w(f"    - {by_path[path].name} _({by_path[path].type or '?'})_")
    w("")

    if cross_ws:
        w(f"**{len(cross_ws)} community/communities span more than one workstream** — "
          "the Pattern Promotion Rule threshold. Review for a Zone 03 pattern page.")
    else:
        w("No community spans more than one workstream yet.")
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
