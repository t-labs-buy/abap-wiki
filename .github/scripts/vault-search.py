#!/usr/bin/env python3
"""Find the vault pages most likely to answer a question.

This replaces `grep -ril` in the abap-wiki skill. Grep answers "which files
contain this string"; a reader asks "why do orders get stuck" and the page is
called "Credit release blocked by legacy limit table". Ranking, entity-alias
expansion and the wikilink graph close most of that gap without a single
embedding — see vault_search.py for how, and for the optional vector tier.

Usage:
    python3 .github/scripts/vault-search.py "credit release" [--root .]
    python3 .github/scripts/vault-search.py "IDoc failures" --workstream OTC
    python3 .github/scripts/vault-search.py "ZSD_ORDER_CHECK" --literal
    python3 .github/scripts/vault-search.py "what recurs" --format paths

Deterministic, read-only, standard library only. Exits 0 with "no matches"
rather than failing when nothing scores: an empty result is an answer.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vault_model import Vault          # noqa: E402
import vault_search                    # noqa: E402


def render(hits, meta, fmt, show_terms):
    out = []
    w = out.append

    if fmt == "paths":
        for hit in hits:
            w(hit.path)
        return "\n".join(out)

    tier = "lexical + semantic" if meta["semantic"] else "lexical"
    detail = "" if meta["semantic"] else f" (semantic off: {meta['reason']})"
    w(f"{len(hits)} match(es) · {tier}{detail}")
    if show_terms:
        terms = ", ".join(f"{t}×{weight:g}" for t, weight in meta["terms"])
        w(f"terms: {terms}")
    w("")

    if not hits:
        w("No page scored. Try fewer words, or check meta/entities.md for the "
          "canonical name of what you are looking for.")
        return "\n".join(out)

    for i, hit in enumerate(hits, 1):
        page = hit.page
        bits = [page.type or "?"]
        if page.workstream:
            bits.append(page.workstream)
        if page.front.get("updated"):
            bits.append(f"updated {page.front['updated']}")
        flags = f"  ⚠ {' · '.join(hit.flags)}" if hit.flags else ""
        w(f"{i}. {page.name}")
        w(f"   {' · '.join(bits)}{flags}")
        w(f"   {hit.path}")
        if fmt == "full":
            score = f"score {hit.score:.3f}"
            if hit.semantic is not None:
                score += f" · lexical {hit.lexical:.2f} · cosine {hit.semantic:.3f}"
            w(f"   {score}")
        if hit.excerpt:
            where = f"{hit.heading} — " if hit.heading else ""
            w(f"   “{where}{hit.excerpt}”")
        w("")

    return "\n".join(out).rstrip()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="+", help="what you are looking for")
    ap.add_argument("--root", default=".", help="vault root (default: cwd)")
    ap.add_argument("--top", type=int, default=8, help="results to show (default: 8)")
    ap.add_argument("--workstream", help="restrict to one workstream or module slug")
    ap.add_argument("--type", dest="ptype", help="restrict to one page type")
    ap.add_argument("--zone", help="restrict to one zone folder")
    ap.add_argument("--literal", action="store_true",
                    help="exact terms only: no alias expansion, no vector tier")
    ap.add_argument("--no-semantic", action="store_true",
                    help="skip the vector tier even when it is available")
    ap.add_argument("--format", choices=("compact", "full", "paths"),
                    default="compact", help="output detail (default: compact)")
    ap.add_argument("--explain", action="store_true",
                    help="print the expanded query terms")
    ap.add_argument("--out", help="also write the result to this file")
    args = ap.parse_args()

    query = " ".join(args.query)
    vault = Vault(args.root)
    if not vault.pages:
        print("The vault has no content pages yet.")
        return 0

    hits, meta = vault_search.search(
        args.root, query,
        top=args.top, workstream=args.workstream, ptype=args.ptype,
        zone=args.zone, literal=args.literal,
        semantic=not args.no_semantic, vault=vault)

    report = render(hits, meta, args.format, args.explain)
    print(report)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
