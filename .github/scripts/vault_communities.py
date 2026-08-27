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

Clustering is hierarchical: hierarchy() clusters the whole graph, then splits
any community too large to describe as one thing, recursively. A root answers
"what is this vault about"; a leaf answers "what is going on with our IDoc
work" — the same question shape at two different zoom settings.

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


# --------------------------------------------------------------------------
# The hierarchy
# --------------------------------------------------------------------------

MAX_COMMUNITY_SIZE = 10

# How deep the recursive split may go. A guard, not a target: four levels of
# nesting is already more than a reader will walk.
MAX_DEPTH = 4


class Node:
    """One community in the hierarchy, with the communities it splits into."""

    __slots__ = ("community", "children", "level", "number")

    def __init__(self, community, children, level, number):
        self.community = community
        self.children = children
        self.level = level
        # Dotted path through the tree ("2", "2.1"), the reader's address for
        # this cluster and stable for as long as the tree shape is.
        self.number = number

    @property
    def signature(self):
        return self.community.signature

    def __iter__(self):
        """Depth-first, self first: the order the report is written in."""
        yield self
        for child in self.children:
            yield from child


def induced(adj, members):
    """The subgraph among `members`, outside edges dropped."""
    inside = set(members)
    return {n: {m: w for m, w in adj[n].items() if m in inside} for n in members}


def split_once(adj, members):
    """Members grouped into sub-communities, or None when they do not split.

    Pages with no edge to any other member (they were held in this community
    by a link that leaves it) join the largest sub-group rather than becoming
    singleton communities of their own: a cluster of one tells a reader
    nothing, and the page is already reported as a hub or a floating page
    elsewhere.
    """
    sub = induced(adj, members)
    connected = {n: nbrs for n, nbrs in sub.items() if nbrs}
    if len(connected) < 2:
        return None

    assignment = louvain_one_level(connected)
    grouped = collections.defaultdict(list)
    for node, com in assignment.items():
        grouped[com].append(node)
    groups = sorted((sorted(g) for g in grouped.values()),
                    key=lambda g: (-len(g), g[0]))
    if len(groups) < 2:
        return None

    stranded = [n for n in members if n not in connected]
    if stranded:
        groups[0] = sorted(groups[0] + stranded)
        groups.sort(key=lambda g: (-len(g), g[0]))
    return groups


def build_nodes(vault, adj, groups, level, prefix, max_size):
    """Nodes for one set of sibling groups, split recursively."""
    ranked = sorted(groups, key=lambda g: (-len(g), g[0]))
    nodes = []
    for i, members in enumerate(ranked, 1):
        number = f"{prefix}.{i}" if prefix else str(i)
        children = []
        if len(members) > max_size and level + 1 < MAX_DEPTH:
            sub = split_once(adj, members)
            if sub:
                children = build_nodes(vault, adj, sub, level + 1, number, max_size)
        nodes.append(Node(Community(vault, members), children, level, number))
    return nodes


def hierarchy(vault, max_size=MAX_COMMUNITY_SIZE):
    """The community tree, broadest first.

    Plain Louvain's aggregation ladder is not a usable hierarchy here: on a
    graph of a few hundred pages it converges after one pass and every level
    above the first is the same partition under different ids. So the tree is
    built the way GraphRAG builds its own — cluster, then recursively split any
    community too large to summarise as one thing — which produces real levels
    at any vault size and makes containment true by construction rather than by
    a subset test after the fact.

    Returns the roots. Iterate a root to walk its subtree depth-first.
    """
    adj = adjacency(vault)
    connected = {n: nbrs for n, nbrs in adj.items() if nbrs}
    if not connected:
        return []

    assignment = louvain_one_level(connected)
    grouped = collections.defaultdict(list)
    for node, com in assignment.items():
        grouped[com].append(node)

    return build_nodes(vault, adj, [sorted(g) for g in grouped.values()],
                       0, "", max_size)


def walk(roots):
    """Every node in the tree, depth-first, roots in report order."""
    for root in roots:
        yield from root


def leaves(roots):
    """The finest communities — the ones that name pages rather than clusters."""
    return [node.community for node in walk(roots) if not node.children]


def disconnected_communities(vault, communities):
    """Communities whose members do not all reach each other from inside.

    This is the one guarantee Louvain does not make and Leiden does: a node
    that was the only bridge between two halves can move away and leave them
    merged under a label that no longer describes a connected thing. Reported
    rather than fixed — if this stays empty on the real vault, Leiden's
    refinement phase buys nothing and should not be written.
    """
    adj = adjacency(vault)
    broken = []
    for com in communities:
        members = set(com.members)
        if len(members) < 2:
            continue
        seen, stack = set(), [com.members[0]]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(n for n in adj[node] if n in members and n not in seen)
        if len(seen) != len(members):
            broken.append((com, sorted(members - seen)))
    return broken
