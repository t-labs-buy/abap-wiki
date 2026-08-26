"""Community detection over the vault wikilink graph.

One definition of what a community is, so graph-health.py (which reports them)
and community-summarize.py (which summarises them) cannot drift apart — the
same reason vault_model.py exists for pages and edges.

A community is a cluster of pages that link to each other more than they link
to the rest of the vault. Two things consume that:

  - graph-health.py flags a community spanning 2+ workstreams as a Pattern
    Promotion candidate.
  - community-summarize.py writes one summary per community into
    meta/communities.md, the vault's global-search layer.

Standard library only. Never writes.
"""

import collections
import hashlib

# Clustering resolution. 1.0 is standard modularity; higher splits more finely.
RESOLUTION = 1.0

# How many top-degree members a community nominates as its entry points.
HUB_COUNT = 3


# --------------------------------------------------------------------------
# Louvain modularity optimisation
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


def adjacency(vault):
    """Undirected weighted adjacency over the resolved wikilink graph.

    Direction is dropped: a decision linking to a development and the
    development linking back describe the same association twice, so
    reciprocal links weigh double.
    """
    adj = collections.defaultdict(dict)
    for p in vault.pages:
        adj[p.path] = {}
    for src, dests in vault.forward_edges.items():
        for dest in dests:
            adj[src][dest] = adj[src].get(dest, 0.0) + 1.0
            adj[dest][src] = adj[dest].get(src, 0.0) + 1.0
    return adj


# --------------------------------------------------------------------------
# Communities
# --------------------------------------------------------------------------

class Community:
    """One cluster, with everything a report or a summary needs about it.

    `signature` is the identity that survives across runs. Louvain community
    ids renumber whenever the graph changes, so they are useless as a cache
    key; a hash of the member set is stable — an untouched community keeps its
    summary and costs nothing to regenerate.
    """

    __slots__ = ("members", "signature", "workstreams", "types", "hubs")

    def __init__(self, vault, members):
        self.members = sorted(members)
        self.signature = signature_of(self.members)
        self.workstreams = sorted({vault.by_path[p].workstream
                                   for p in self.members
                                   if vault.by_path[p].workstream})
        self.types = collections.Counter(vault.by_path[p].type or "?"
                                         for p in self.members)
        self.hubs = sorted(self.members,
                           key=lambda p: (-vault.degree(p), p))[:HUB_COUNT]

    def __len__(self):
        return len(self.members)

    @property
    def spans_workstreams(self):
        """The Pattern Promotion Rule threshold: one cluster, 2+ workstreams."""
        return len(self.workstreams) > 1

    def dominant_type(self):
        """Most common page type, ties broken alphabetically."""
        if not self.types:
            return "?"
        return min(self.types.items(), key=lambda kv: (-kv[1], kv[0]))[0]

    def body_hash(self, vault):
        """Hash of the member bodies, for cache invalidation.

        The signature alone only catches membership changes. This catches an
        edit inside a community whose membership did not move — without it a
        rewritten decision page keeps a summary describing the old decision.
        """
        h = hashlib.sha256()
        for path in self.members:
            h.update(path.encode("utf-8"))
            h.update(b"\0")
            h.update(vault.by_path[path].body.encode("utf-8"))
            h.update(b"\0")
        return h.hexdigest()[:8]


class Partition:
    """The communities at one level, in stable report order."""

    __slots__ = ("communities", "depth", "clustered", "unclustered")

    def __init__(self, communities, depth, clustered, unclustered):
        self.communities = communities
        self.depth = depth
        self.clustered = clustered
        self.unclustered = unclustered

    def __iter__(self):
        return iter(self.communities)

    def __len__(self):
        return len(self.communities)

    def signatures(self):
        return {c.signature for c in self.communities}


def signature_of(members):
    """Stable identity for a member set. 12 hex chars: short enough to read in
    a generated comment, wide enough that a collision is not a real risk."""
    joined = "\n".join(sorted(members))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


def partition(vault, level=0):
    """Cluster the vault. `level` indexes the Louvain hierarchy, 0 = finest.

    Pages with no links either way are left out entirely: an isolated page is
    not a community of one, it is a floating page, and graph-health reports it
    as a violation rather than as a cluster.
    """
    adj = adjacency(vault)
    connected = {n: nbrs for n, nbrs in adj.items() if nbrs}
    levels = louvain(connected) if connected else []
    if not levels:
        return Partition([], 0, [], sorted(adj))

    membership = levels[min(level, len(levels) - 1)]

    grouped = collections.defaultdict(list)
    for node, com in membership.items():
        grouped[com].append(node)

    ranked = sorted((Community(vault, m) for m in grouped.values()),
                    key=lambda c: (-len(c.members), c.members[0]))

    return Partition(ranked, len(levels),
                     sorted(connected),
                     sorted(n for n in adj if n not in connected))
