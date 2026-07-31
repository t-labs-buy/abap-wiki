#!/usr/bin/env python3
"""Domain-adapted starter prompts for the ABAP vault.

GraphRAG's auto prompt tuning reads a sample of the corpus with an LLM and
writes prompts adapted to that domain, because its graph is auto-extracted and
has no schema. This vault has the opposite property — a fixed ontology of 21
page types, mandatory frontmatter, mandatory link patterns — so the same
adaptation is *derivable*: the page type says what kind of question a page can
answer, the filename says what it is about, and the link graph says how well
it is supported. No model call, no nondeterminism, no token cost.

This is the mirror image of `question-gen.py`:

    question-gen.py   asks what the vault CANNOT answer yet — gaps, for the
                      curator to close. Output goes into Open-Questions pages.
    prompt-suggest.py asks what the vault CAN answer well — starter prompts,
                      for a reader who does not know what is in here. Output is
                      shown by the abap-wiki skill; nothing is written.

Every suggestion names the page(s) that answer it, so a suggestion the vault
cannot honour is a bug, not a style choice. Pages that are archived, thin, or
unlinked are filtered or down-ranked for exactly that reason.

Usage:
    python3 .github/scripts/prompt-suggest.py                    # top 8, markdown
    python3 .github/scripts/prompt-suggest.py --top 12
    python3 .github/scripts/prompt-suggest.py --workstream OTC
    python3 .github/scripts/prompt-suggest.py --about credit     # bias to a topic
    python3 .github/scripts/prompt-suggest.py --near "OTC - E-001 - Credit Auto-Release Job"
    python3 .github/scripts/prompt-suggest.py --format compact   # cheapest to read
    python3 .github/scripts/prompt-suggest.py --format json

Read-only. Standard library only.
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys

from vault_model import Vault, WIKILINK_RE, parse_frontmatter

# --------------------------------------------------------------------------
# Naming-convention vocabulary
# --------------------------------------------------------------------------
#
# The Naming Rules in CLAUDE.md put scaffolding in every filename: a type
# label, a workstream slug, a WRICEF id, a date. None of it belongs in a
# question addressed to a human, so it is stripped back to the subject.

TYPE_LABELS = {
    "standard", "architecture", "landscape", "decision", "spec", "estimation",
    "issue", "pattern", "lessons", "gotcha", "troubleshooting", "faq", "poc",
    "onboarding", "process", "runbook",
}
WRICEF_ID_RE = re.compile(r"^[A-Z]{1,4}-?\d{2,4}[A-Z]?$")
DATE_SUFFIX_RE = re.compile(r"\s*-\s*\d{4}-\d{2}-\d{2}\s*$")
YEAR_PART_RE = re.compile(r"^\d{4}$")

SKIP_STATUSES = {"archived"}

# A page whose body carries fewer words than this cannot answer a question
# well, whatever its type says. Suggesting it would break the guarantee that
# every prompt here is answerable.
THIN_BODY_WORDS = 45


def subject_of(page, slugs):
    """The topic of a page, with naming-convention scaffolding removed.

    `Decision - OTC - Custom credit auto-release job - 2026-07-14`
        -> `Custom credit auto-release job`
    `OTC - CR045 - BP Address Validation` -> `BP Address Validation`
    """
    name = DATE_SUFFIX_RE.sub("", page.name)
    parts = [p.strip() for p in name.split(" - ") if p.strip()]

    kept = []
    for i, part in enumerate(parts):
        if part.lower() in TYPE_LABELS:
            continue
        if part in slugs or part == page.workstream:
            continue
        if WRICEF_ID_RE.match(part):
            continue
        if YEAR_PART_RE.match(part) and i == len(parts) - 1:
            continue
        kept.append(part)

    # Everything was scaffolding — a workstream page, or `Open-Questions/OTC`.
    return " - ".join(kept) if kept else name


# --------------------------------------------------------------------------
# Question templates, one per page type
# --------------------------------------------------------------------------
#
# Phrased the way a teammate actually asks, not the way the vault files it.
# `{s}` is the subject, `{ws}` the workstream slug.

TEMPLATES = {
    "decision":        "What did we decide about {s}, and why did we rule out the alternative?",
    "development":     "What does {s} do, and what does it depend on?",
    "spec":            "What does the {s} spec require?",
    "issue":           "What was the root cause of {s}, and how was it resolved?",
    "estimation":      "How was {s} estimated, and how did the actuals compare?",
    "gotcha":          "What is the catch with {s}?",
    "pattern":         "What is our standard approach to {s}?",
    "troubleshooting": "How do I diagnose {s}?",
    "lessons-learned": "What did we learn from {s}?",
    "standard":        "What does the {s} standard actually require?",
    "architecture":    "What constraints does {s} put on what we build?",
    "landscape":       "How is {s} laid out — systems, clients and transport routes?",
    "runbook":         "How do I run {s}, step by step?",
    "process":         "What is our process for {s}?",
    "onboarding":      "How does a new joiner get productive on {s}?",
    "contact":         "Who is the point of contact for {s}?",
    "stakeholder":     "What does {s} own, and what are their concerns?",
    "workstream":      "Where does {ws} stand — scope, status and next actions?",
    "open-questions":  "What is still open on {ws}, and who owns each item?",
    "meeting":         "What came out of {s}?",
}

# What the answer is worth to someone six months from now. The constitution
# treats meetings as source material rather than durable artifacts (Core
# Behavior Rule 3), and stakeholder pages answer a narrow question — both sit
# at the bottom. Decisions, gotchas and patterns are the reuse layer.
TYPE_WEIGHT = {
    "decision": 10, "gotcha": 10, "troubleshooting": 9, "pattern": 9,
    "issue": 8, "lessons-learned": 8, "development": 8, "faq": 8,
    "spec": 7, "standard": 7, "architecture": 7, "runbook": 7,
    "estimation": 6, "landscape": 6, "open-questions": 6, "workstream": 6,
    "process": 5, "onboarding": 5, "contact": 4,
    "stakeholder": 3, "meeting": 2,
}

THEMES = {
    "decision": "Decisions and rationale",
    "issue": "Decisions and rationale",
    "development": "Custom objects and specs",
    "spec": "Custom objects and specs",
    "estimation": "Custom objects and specs",
    "gotcha": "Gotchas, patterns and troubleshooting",
    "pattern": "Gotchas, patterns and troubleshooting",
    "troubleshooting": "Gotchas, patterns and troubleshooting",
    "lessons-learned": "Gotchas, patterns and troubleshooting",
    "faq": "Gotchas, patterns and troubleshooting",
    "standard": "Standards and landscape",
    "architecture": "Standards and landscape",
    "landscape": "Standards and landscape",
    "runbook": "How we work",
    "process": "How we work",
    "onboarding": "How we work",
    "contact": "People and ownership",
    "stakeholder": "People and ownership",
    "workstream": "Status and open threads",
    "open-questions": "Status and open threads",
    "meeting": "Status and open threads",
}
CROSS_THEME = "Across the vault"

THEME_ORDER = (
    "Decisions and rationale",
    "Custom objects and specs",
    "Gotchas, patterns and troubleshooting",
    "Standards and landscape",
    "Status and open threads",
    "How we work",
    "People and ownership",
    CROSS_THEME,
)


class Suggestion:
    __slots__ = ("question", "kind", "pages", "theme", "workstream", "ptype",
                 "flags", "score")

    def __init__(self, question, kind, pages, theme, workstream, ptype,
                 flags=(), score=0.0):
        self.question = question
        self.kind = kind
        self.pages = list(pages)
        self.theme = theme
        self.workstream = workstream or ""
        self.ptype = ptype
        self.flags = list(flags)
        self.score = score

    def as_dict(self):
        return {
            "question": self.question,
            "kind": self.kind,
            "type": self.ptype,
            "workstream": self.workstream,
            "theme": self.theme,
            "flags": self.flags,
            "answered_by": self.pages,
            "score": round(self.score, 2),
        }


# --------------------------------------------------------------------------
# Page substance and scoring
# --------------------------------------------------------------------------

def strip_frontmatter(text):
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text[end + 4:] if end != -1 else text


def body_words(page):
    """Prose words in the body — headings, tables, links and frontmatter out.

    Measures whether there is an answer on the page, not how long the file is.
    """
    text = strip_frontmatter(page.body)
    text = WIKILINK_RE.sub(" ", text)
    lines = [l for l in text.splitlines()
             if not l.lstrip().startswith(("#", "|", ">", "---"))]
    return len(" ".join(lines).split())


def parse_date(value):
    try:
        return datetime.date.fromisoformat(str(value).strip()[:10])
    except (ValueError, TypeError):
        return None


def score_page(v, page, today, words):
    """How well this page can carry a question, and why.

    Returns (score, flags). Flags are shown to the reader so a suggestion
    backed by a draft or an unvalidated page is never presented as settled.
    """
    flags = []
    score = float(TYPE_WEIGHT.get(page.type, 4))

    # Support: a well-linked page answers with context around it. Capped so a
    # single hub does not crowd out every other topic.
    score += min(v.degree(page.path), 12) * 0.5

    # Substance.
    if words < THIN_BODY_WORDS:
        score -= 4.0
        flags.append("thin")
    elif words > 250:
        score += 1.0

    status = page.status
    if status in ("evergreen", "active"):
        score += 1.0
    elif status == "draft":
        score -= 3.0
        flags.append("draft")
    elif status == "parked":
        score -= 3.0
        flags.append("parked")
    elif status == "resolved":
        score += 0.5

    if "ai-generated" in page.tags:
        score -= 2.0
        flags.append("unvalidated")

    updated = parse_date(page.front.get("updated"))
    if updated:
        age = (today - updated).days
        if age < 0:
            pass  # dated in the future; treat as current, do not reward it
        elif age <= 30:
            score += 3.0
        elif age <= 90:
            score += 1.5
        elif age > 365:
            score -= 2.0
            flags.append(f"last updated {updated.isoformat()}")
    else:
        flags.append("no updated date")

    if page.has_conflict:
        # Worth surfacing — the vault knows the two sides — but the reader is
        # told before they ask.
        flags.append("unresolved conflict")

    return score, flags


# --------------------------------------------------------------------------
# Generators
# --------------------------------------------------------------------------

def per_page_suggestions(v, today):
    slugs = set(v.slugs_in_use()) | set(v.workstreams())
    for page in v.pages:
        if page.status in SKIP_STATUSES:
            continue
        template = TEMPLATES.get(page.type)
        if not template:
            continue
        words = body_words(page)
        # An open-questions page is a table; a workstream page is mostly links.
        # Neither is thin in the sense the word count means.
        if words < 15 and page.type not in ("open-questions", "workstream"):
            continue
        subject = subject_of(page, slugs)
        ws = page.workstream or subject
        question = template.format(s=subject, ws=ws)
        score, flags = score_page(v, page, today, words)
        yield Suggestion(question, f"page:{page.type}", [page.path],
                         THEMES.get(page.type, CROSS_THEME), page.workstream,
                         page.type, flags, score)


def _section(body, heading):
    """The text under a `## heading`, up to the next heading of any level."""
    m = re.search(r"^#{1,6}\s*" + re.escape(heading) + r"\s*$", body,
                  re.IGNORECASE | re.MULTILINE)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = re.search(r"^#{1,6}\s", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest


def faq_questions(v, today):
    """Real questions the team already asked, taken verbatim.

    The highest-fidelity prompts in the vault: nobody had to guess the phrasing.
    Only answered ones — an unanswered FAQ entry is a gap, and gaps are
    question-gen.py's job.
    """
    for page in v.of_type("faq"):
        if page.status in SKIP_STATUSES:
            continue
        answered = _section(strip_frontmatter(page.body), "Answered Questions")
        if not answered:
            continue
        seen = set()
        for raw in re.findall(r"^\s*(?:[-*]\s+|\|\s*)(.+?)\s*(?:\||$)",
                              answered, re.MULTILINE):
            text = WIKILINK_RE.sub(lambda m: m.group(1).split("|")[0], raw)
            text = re.sub(r"[*_`]", "", text).strip()
            if "?" not in text or len(text) < 15:
                continue
            text = text[:text.index("?") + 1]
            if text.lower() in seen or text.lower().startswith("question"):
                continue
            seen.add(text.lower())
            score, flags = score_page(v, page, today, body_words(page))
            yield Suggestion(text, "faq:asked", [page.path],
                             THEMES["faq"], page.workstream, "faq", flags,
                             score + 2.0)  # a question someone really asked


# Tag categories that describe a subject worth comparing across the vault.
# `role` tags (client, developer, tech-lead) and `governance` tags
# (ai-generated) label the page's *audience or state*, not its topic — "how do
# INT and OTC each handle developer?" is not a question anyone asks.
TOPICAL_TAG_CATEGORIES = {
    "technology", "business-object", "quality", "process", "phase",
    "artifact-kind",
}
FALLBACK_NON_TOPICAL = {
    "ai-generated", "client", "our-team", "developer", "tech-lead", "reviewer", "it",
}


def topical_tags(root):
    """Tags whose registry category describes a subject.

    Parsed from the Tag Vocabulary section of `meta/entities.md`, which groups
    tags under `### category` headings. Returns None when the registry is
    missing or unparseable — callers then fall back rather than guess.
    """
    path = os.path.join(root, "meta", "entities.md")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    start = re.search(r"^#{1,3}\s*Tag Vocabulary\s*$", text, re.MULTILINE)
    if not start:
        return None
    section = text[start.end():]
    nxt = re.search(r"^##\s(?!#)", section, re.MULTILINE)
    if nxt:
        section = section[:nxt.start()]

    allowed, category = set(), None
    for line in section.splitlines():
        heading = re.match(r"^###\s+([a-z-]+)", line.strip())
        if heading:
            category = heading.group(1)
            continue
        row = re.match(r"^\|\s*`?([a-z0-9-]+)`?\s*\|", line.strip())
        if row and category in TOPICAL_TAG_CATEGORIES:
            tag = row.group(1)
            if set(tag) <= set("-:"):
                continue  # the table's separator row, not a tag
            allowed.add(tag)
    return allowed or None


def cross_cutting(v, today):
    """Questions no single page answers — the graph's own suggestions.

    Tags and workstream slugs are controlled vocabulary (Tag Discipline), so
    co-occurrence across pages is a real signal rather than string luck.
    """
    allowed = topical_tags(v.root)
    by_tag = collections.defaultdict(list)
    for page in v.pages:
        if page.status in SKIP_STATUSES:
            continue
        for tag in page.tags:
            if allowed is not None and tag not in allowed:
                continue
            if allowed is None and tag in FALLBACK_NON_TOPICAL:
                continue
            by_tag[tag].append(page)

    for tag, pages in sorted(by_tag.items()):
        types = {p.type for p in pages}
        streams = {p.workstream for p in pages if p.workstream}
        paths = sorted(p.path for p in pages)

        if len(streams) >= 2 and len(pages) >= 3:
            a, b = sorted(streams)[:2]
            yield Suggestion(
                f"How do {a} and {b} each handle {tag.replace('-', ' ')}?",
                "cross:tag-across-workstreams", paths, CROSS_THEME, "", "",
                [], 12.0 + min(len(pages), 8) * 0.4)
        elif len(types) >= 3 and len(pages) >= 3:
            yield Suggestion(
                f"What do we know about {tag.replace('-', ' ')} — the decisions, "
                f"the objects and the gotchas?",
                "cross:tag-span", paths, CROSS_THEME, sorted(streams)[0] if streams else "",
                "", [], 11.0 + min(len(pages), 8) * 0.4)

    # Hubs: the pages the rest of the graph hangs off. Worth an end-to-end walk.
    slugs = set(v.slugs_in_use()) | set(v.workstreams())
    hubs = sorted(v.pages, key=lambda p: (-v.degree(p.path), p.path))
    for page in hubs[:3]:
        if v.degree(page.path) < 8 or page.status in SKIP_STATUSES:
            continue
        if page.type in ("workstream", "open-questions", "meeting"):
            continue
        neighbours = sorted(v.forward_edges[page.path] | v.inbound[page.path])
        yield Suggestion(
            f"Walk me through {subject_of(page, slugs)} end to end — the decision, "
            f"the spec, the object and the gotchas.",
            "cross:hub", [page.path] + neighbours, CROSS_THEME,
            page.workstream, page.type, [], 12.5)

    # Handover readiness is checkable from structure alone (Handover Criterion).
    live = [p for p in v.pages
            if p.workstream and p.status not in SKIP_STATUSES]
    counts = collections.Counter(p.workstream for p in live)
    for slug in v.workstreams():
        if counts.get(slug, 0) >= 5:
            paths = sorted(p.path for p in live if p.workstream == slug)
            yield Suggestion(
                f"Is {slug} handover-ready — which of the required artifacts are missing?",
                "cross:handover", paths, CROSS_THEME, slug, "", [], 10.5)


GENERATORS = (per_page_suggestions, faq_questions, cross_cutting)


# --------------------------------------------------------------------------
# Filtering, ranking, selection
# --------------------------------------------------------------------------

def neighbourhood(v, start_paths, max_hops=2):
    """Undirected BFS distance from the starting pages."""
    dist = {p: 0 for p in start_paths}
    frontier = list(start_paths)
    for hop in range(1, max_hops + 1):
        nxt = []
        for path in frontier:
            for other in v.forward_edges[path] | v.inbound[path]:
                if other not in dist:
                    dist[other] = hop
                    nxt.append(other)
        frontier = nxt
    return dist


def match_strength(v, suggestion, term):
    """0 no match, 1 mentioned in a supporting page, 2 the page is about it.

    A page that merely mentions "address" somewhere in its body is a weaker
    answer than one whose name or tag says address — the two must not rank
    alike, or the topic filter returns the vault's hubs every time.
    """
    low = term.lower()
    if low in suggestion.question.lower():
        return 2
    best = 0
    for path in suggestion.pages:
        page = v.by_path.get(path)
        if not page:
            continue
        if low in page.name.lower() or any(low in t for t in page.tags):
            return 2
        if low in page.body.lower():
            best = 1
    return best


def rank(v, suggestions, today, about=None, workstream=None, near=None):
    kept = []
    near_dist = {}
    if near:
        start = [p for p in (v.resolve(n) for n in near) if p]
        for name in near:
            if v.resolve(name) is None:
                print(f"--near: no page named {name!r}; ignoring it",
                      file=sys.stderr)
        near_dist = neighbourhood(v, start)

    for s in suggestions:
        if workstream and s.workstream and s.workstream != workstream:
            continue
        if workstream and not s.workstream and s.kind.startswith("page:"):
            continue
        if about:
            strength = match_strength(v, s, about)
            if not strength:
                continue
            s.score += 8.0 if strength == 2 else 2.0
        if near_dist:
            hops = [near_dist[p] for p in s.pages if p in near_dist]
            if not hops:
                continue
            best = min(hops)
            if best == 0 and len(s.pages) == 1:
                continue  # the page they just read
            s.score += 5.0 if best <= 1 else 2.0
        kept.append(s)

    kept.sort(key=lambda s: (-s.score, s.question))
    return kept


def dedupe(suggestions):
    seen, out = set(), []
    for s in suggestions:
        key = s.question.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def diversify(suggestions, top):
    """Round-robin over (theme, workstream) so the list spans the vault.

    Without this the top of a small vault is five questions about whichever
    workstream has the most pages, which teaches the reader nothing about what
    else is in here.
    """
    picked, used, remaining = [], set(), list(suggestions)
    seen_questions = set()
    while remaining and len(picked) < top:
        progressed = False
        for s in list(remaining):
            key = (s.theme, s.workstream)
            if key in used:
                continue
            remaining.remove(s)
            if s.question.lower() in seen_questions:
                continue
            seen_questions.add(s.question.lower())
            used.add(key)
            picked.append(s)
            progressed = True
            if len(picked) >= top:
                break
        if not progressed:
            break
        used.clear()
    return picked


# --------------------------------------------------------------------------
# Vault profile — the domain-adaptation header
# --------------------------------------------------------------------------

def profile(v, root):
    live = [p for p in v.pages if p.status not in SKIP_STATUSES]
    types = collections.Counter(p.type for p in live if p.type)
    streams = sorted({p.workstream for p in live if p.workstream})
    tags = collections.Counter(t for p in live for t in p.tags if t != "ai-generated")
    dates = sorted(d for d in (parse_date(p.front.get("updated")) for p in live) if d)

    entities = []
    reg = os.path.join(root, "meta", "entities.md")
    if os.path.isfile(reg):
        with open(reg, "r", encoding="utf-8") as fh:
            entities = re.findall(r"^\|\s*`?([A-Z][A-Z0-9_-]{1,12})`?\s*\|",
                                  fh.read(), re.MULTILINE)

    return {
        "pages": len(live),
        "workstreams": streams,
        "types": types.most_common(),
        "top_tags": [t for t, _ in tags.most_common(5)],
        "updated_range": [dates[0].isoformat(), dates[-1].isoformat()] if dates else [],
        "registered_entities": sorted(set(entities))[:20],
    }


def profile_line(p):
    parts = [f"{p['pages']} pages"]
    if p["workstreams"]:
        parts.append(f"{len(p['workstreams'])} workstream(s): "
                     + ", ".join(p["workstreams"]))
    if p["types"]:
        parts.append(f"{len(p['types'])} page types")
    if p["updated_range"]:
        parts.append("last updated " + p["updated_range"][1])
    line = "ABAP delivery vault — " + "; ".join(parts) + "."
    if p["top_tags"]:
        line += " Strongest coverage: " + ", ".join(p["top_tags"]) + "."
    return line


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def render_markdown(v, picked, prof, header=True):
    out = []
    w = out.append
    if header:
        w("# What you can ask this vault")
        w("")
        w(profile_line(prof))
        w("")
        w("_Derived from vault structure and content — every question below is "
          "answered by the page(s) named under it._")
        w("")

    by_theme = collections.defaultdict(list)
    for s in picked:
        by_theme[s.theme].append(s)

    order = [t for t in THEME_ORDER if t in by_theme]
    order += sorted(t for t in by_theme if t not in THEME_ORDER)

    for theme in order:
        w(f"## {theme}")
        w("")
        for s in by_theme[theme]:
            flag = f" _({'; '.join(s.flags)})_" if s.flags else ""
            w(f"- {s.question}{flag}")
            names = [v.by_path[p].name for p in s.pages if p in v.by_path]
            shown = ", ".join(f"`{n}`" for n in names[:3])
            if len(names) > 3:
                shown += f" +{len(names) - 3} more"
            w(f"    - answered by {shown}")
        w("")
    if not picked:
        w("_No suggestion matched. The vault may be empty, or the filter too narrow._")
        w("")
    return "\n".join(out)


def render_compact(picked, prof):
    """Cheapest form — what the skill reads when it only needs the questions."""
    lines = [profile_line(prof), ""]
    for i, s in enumerate(picked, 1):
        flag = f"  ({'; '.join(s.flags)})" if s.flags else ""
        lines.append(f"{i}. {s.question}{flag}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="vault root (default: cwd)")
    ap.add_argument("--top", type=int, default=8, help="how many prompts (default: 8)")
    ap.add_argument("--workstream", help="only prompts for this slug (OTC, INT, …)")
    ap.add_argument("--about", help="bias toward a topic (matches names, tags, body)")
    ap.add_argument("--near", action="append", default=[],
                    help="page name to suggest follow-ups around; repeatable")
    ap.add_argument("--format", choices=("md", "compact", "json"), default="md")
    ap.add_argument("--out", help="also write the output to this file")
    ap.add_argument("--today", default=datetime.date.today().isoformat(),
                    help="reference date for recency scoring (default: today)")
    args = ap.parse_args()

    today = parse_date(args.today)
    if today is None:
        print(f"--today: not a date: {args.today}", file=sys.stderr)
        return 2

    v = Vault(args.root)
    raw = [s for gen in GENERATORS for s in gen(v, today)]
    ranked = rank(v, raw, today, about=args.about,
                  workstream=args.workstream, near=args.near)
    # `--about` and `--near` are themselves the reader's filter: they said what
    # they want, so rank order beats spreading the list across the vault.
    if args.about or args.near:
        picked = dedupe(ranked)[:args.top]
    else:
        picked = diversify(ranked, args.top)
    prof = profile(v, args.root)

    if args.format == "json":
        text = json.dumps({"profile": prof,
                           "suggestions": [s.as_dict() for s in picked]},
                          indent=2)
    elif args.format == "compact":
        text = render_compact(picked, prof)
    else:
        text = render_markdown(v, picked, prof)

    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
