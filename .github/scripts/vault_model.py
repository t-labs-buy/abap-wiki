"""Shared read-only model of the ABAP vault.

One definition of what a page is, what a wikilink means, and what the link
graph looks like — imported by graph-health.py and question-gen.py so the two
cannot drift apart. Link resolution here MUST agree with find_page_path() in
abap-ingest.py; a checker that disagrees with the pipeline about what `[[OTC]]`
points to reports violations that do not exist.

Standard library only. Never writes.
"""

import collections
import os
import re

ZONES = ("01-standards", "02-workstreams", "03-intelligence", "04-internal")
BACKLINK_HEADING = "## Linked from"
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
CONFLICT_RE = re.compile(r">\s*\[!warning\]\s*CONFLICT", re.IGNORECASE)

# Folder priority for resolving an ambiguous bare wikilink, mirroring
# INDEX_SECTIONS in abap-ingest.py. `[[OTC]]` must resolve to
# Workstreams/OTC.md, not Open-Questions/OTC.md.
RESOLUTION_ORDER = (
    "01-standards/coding/",
    "01-standards/architecture/",
    "01-standards/landscape/",
    "02-workstreams/Workstreams/",
    "02-workstreams/Stakeholders/",
    "02-workstreams/Meetings/",
    "02-workstreams/Decisions/",
    "02-workstreams/Specs/",
    "02-workstreams/Developments/",
    "02-workstreams/Estimations/",
    "02-workstreams/Issues/",
    "02-workstreams/Open-Questions/",
    "03-intelligence/patterns/",
    "03-intelligence/lessons-learned/",
    "03-intelligence/gotchas/",
    "03-intelligence/troubleshooting/",
    "03-intelligence/faqs/",
    "04-internal/",
)


def is_content_page(filename):
    return (
        filename.endswith(".md")
        and not filename.startswith("_")
        and filename != "README.md"
    )


def parse_frontmatter(text):
    """Flat scalar frontmatter only — enough for type/zone/status/workstream."""
    fields = {}
    if not text.startswith("---"):
        return fields
    end = text.find("\n---", 3)
    if end == -1:
        return fields
    for line in text[3:end].splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
        if m:
            fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fields


def split_backlink_section(text):
    """Return (body, backlink_block).

    Links inside `## Linked from` are reverse edges: per the Linking Rules they
    never count as the page's forward links.
    """
    idx = text.find("\n" + BACKLINK_HEADING)
    if idx == -1:
        return text, ""
    return text[:idx], text[idx:]


class Page:
    __slots__ = ("path", "name", "front", "body", "forward", "backward",
                 "has_backlink_section", "raw")

    def __init__(self, root, rel_path):
        with open(os.path.join(root, rel_path), "r", encoding="utf-8") as fh:
            text = fh.read()
        body, backlinks = split_backlink_section(text)
        self.path = rel_path
        self.name = os.path.basename(rel_path)[:-3]
        self.raw = text
        self.body = body
        self.front = parse_frontmatter(text)
        self.forward = [m.strip() for m in WIKILINK_RE.findall(body)]
        self.backward = [m.strip() for m in WIKILINK_RE.findall(backlinks)]
        self.has_backlink_section = bool(backlinks)

    @property
    def type(self):
        return self.front.get("type", "").strip()

    @property
    def workstream(self):
        return self.front.get("workstream", "").strip()

    @property
    def status(self):
        return self.front.get("status", "").strip()

    @property
    def tags(self):
        raw = self.front.get("tags", "").strip().strip("[]")
        return [t.strip().strip('"').strip("'") for t in raw.split(",") if t.strip()]

    @property
    def has_conflict(self):
        return bool(CONFLICT_RE.search(self.body))

    def in_zone(self, zone):
        return self.path.startswith(zone)


class Vault:
    """Pages plus the resolved wikilink graph."""

    def __init__(self, root="."):
        self.root = root
        self.pages = [Page(root, p) for p in self._scan(root)]
        self.by_path = {p.path: p for p in self.pages}

        self._by_name = collections.defaultdict(list)
        for p in self.pages:
            self._by_name[p.name].append(p.path)
        self.ambiguous = {n: sorted(ps) for n, ps in self._by_name.items() if len(ps) > 1}

        self.forward_edges = collections.defaultdict(set)   # path -> {path}
        self.inbound = collections.defaultdict(set)         # path -> {path}
        self.declared_back = collections.defaultdict(set)   # path -> {path}
        self.unresolved = collections.defaultdict(list)     # target -> [source path]
        self.self_links = []

        for p in self.pages:
            for target in p.forward:
                dest = self.resolve(target)
                if dest is None:
                    self.unresolved[target].append(p.path)
                elif dest == p.path:
                    self.self_links.append((p.path, target))
                else:
                    self.forward_edges[p.path].add(dest)
                    self.inbound[dest].add(p.path)
            for target in p.backward:
                dest = self.resolve(target)
                if dest:
                    self.declared_back[p.path].add(dest)

    @staticmethod
    def _scan(root):
        paths = []
        for zone in ZONES:
            zone_dir = os.path.join(root, zone)
            if not os.path.isdir(zone_dir):
                continue
            for dirpath, _dirnames, filenames in os.walk(zone_dir):
                for f in sorted(filenames):
                    if is_content_page(f):
                        rel = os.path.relpath(os.path.join(dirpath, f), root)
                        paths.append(rel.replace("\\", "/"))
        return sorted(paths)

    def resolve(self, target):
        """Mirror of find_page_path() in abap-ingest.py."""
        if "/" in target:
            wanted = target + ".md"
            for p in self.pages:
                if p.path.endswith("/" + wanted) or p.path == wanted:
                    return p.path
            target = target.rsplit("/", 1)[-1]
        matches = self._by_name.get(target)
        if not matches:
            return None
        for prefix in RESOLUTION_ORDER:
            for path in sorted(matches):
                if path.startswith(prefix):
                    return path
        return sorted(matches)[0]

    def of_type(self, *types):
        return [p for p in self.pages if p.type in types]

    def workstreams(self):
        """Every workstream/module slug that has a Workstreams/{WS}.md page."""
        return sorted(
            p.name for p in self.pages
            if p.in_zone("02-workstreams/Workstreams/")
        )

    def slugs_in_use(self):
        """Every slug appearing in frontmatter, whether or not it has a page."""
        return sorted({p.workstream for p in self.pages if p.workstream})

    def links_to_zone(self, page, zone):
        return any(self.by_path[d].in_zone(zone) for d in self.forward_edges[page.path])

    def degree(self, path):
        return len(self.forward_edges[path]) + len(self.inbound[path])
