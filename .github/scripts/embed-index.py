#!/usr/bin/env python3
"""Build the vault's vector index — meta/embeddings.bin and meta/embeddings.json.

Lexical search finds pages that share words with the question. This finds pages
that share meaning with it: "why do orders get stuck" reaching a page called
"Credit release blocked by legacy limit table". vault_search.py fuses the two.

Runs in CI after each ingest, where an embedding key already lives. The read
side needs no index build and no package — see vault_search.py — so this script
is the only place a provider is ever called with vault content.

What gets embedded, and why in two granularities:

  - one vector per page, so the citable unit is directly searchable
  - one vector per `##` section of a long page, so a twelve-step runbook is
    findable by the step somebody actually needs rather than only by its title

Section hits collapse into their page at query time. The vault cites pages.

Incremental by unit hash: a one-page ingest re-embeds one page. Vectors are
unit-normalised and quantised to int8, so cosine survives as a plain dot
product and the whole index for a few hundred pages is well under a megabyte —
small enough to commit, which is what keeps query time keyless.

Usage:
    python3 .github/scripts/embed-index.py [--root .] [--dry-run] [--force]

Standard library only, including the provider call. Exits 0 with no key: an
absent index is an ordinary state that costs the reader recall, not answers.
"""

import argparse
import array
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vault_model import Vault                                    # noqa: E402
import vault_search                                              # noqa: E402

# Characters of a page sent to the provider. Roughly 2k tokens, comfortably
# inside every current model's window, and past this point a page is better
# served by its section vectors anyway.
PAGE_CHAR_BUDGET = 8_000

# Pages shorter than this are one idea and get one vector. Longer ones are also
# split by `##` heading.
SECTION_THRESHOLD = 2_500
SECTION_MIN_CHARS = 200

# Texts per provider request. Both providers accept far more; batching this
# small keeps one failed request from costing a whole vault's worth of work.
BATCH = 32

SECTION_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)

MANIFEST_VERSION = 1


def unit_text(page, heading, body):
    """What actually gets embedded.

    The page name and its type lead: they are the most compressed statement of
    what the page is, and a body that opens with a table would otherwise give
    the model nothing to anchor on.
    """
    head = f"{page.name}"
    if heading:
        head += f" — {heading}"
    kind = " · ".join(x for x in (page.type, page.workstream) if x)
    return f"{head}\n{kind}\n\n{body.strip()}"[:PAGE_CHAR_BUDGET]


def units_for(page):
    """[(kind, heading, text)] for one page."""
    body = vault_search.strip_frontmatter(page.body).strip()
    if not body:
        return []
    out = [("page", "", unit_text(page, "", body))]

    if len(body) < SECTION_THRESHOLD:
        return out

    marks = list(SECTION_RE.finditer(body))
    for i, match in enumerate(marks):
        start = match.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        section = body[start:end].strip()
        if len(section) >= SECTION_MIN_CHARS:
            heading = match.group(1).strip()
            out.append(("section", heading, unit_text(page, heading, section)))
    return out


def unit_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_existing(root, model, dim):
    """(unit key -> vector row) reusable from the committed index.

    Anything built by a different model is discarded wholesale: mixing two
    embedding spaces in one file produces neighbours that are confidently
    wrong, which is worse than having no index.
    """
    manifest, vectors = vault_search.load_embeddings(root)
    if manifest is None:
        return {}, None
    if manifest.get("model") != model or (dim and manifest.get("dim") != dim):
        return {}, None
    stored = manifest["dim"]
    reusable = {}
    for i, entry in enumerate(manifest["entries"]):
        key = (entry.get("path"), entry.get("kind"), entry.get("heading", ""),
               entry.get("hash"))
        reusable[key] = vectors[i * stored:(i + 1) * stored]
    return reusable, stored


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="vault root (default: cwd)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; embed nothing, write nothing")
    ap.add_argument("--force", action="store_true",
                    help="re-embed everything, ignoring the committed index")
    args = ap.parse_args()

    provider, key, model, _ = vault_search.provider_config()
    vault = Vault(args.root)

    wanted = []          # (path, kind, heading, hash, text)
    for page in vault.pages:
        for kind, heading, text in units_for(page):
            wanted.append((page.path, kind, heading, unit_hash(text), text))

    print(f"{len(vault.pages)} pages · {len(wanted)} units · "
          f"provider {provider} · model {model}")

    if not wanted:
        print("  nothing to embed — the vault has no content pages yet")
        return 0

    reusable, dim = ({}, None) if args.force else load_existing(args.root, model, None)
    fresh = [u for u in wanted if (u[0], u[1], u[2], u[3]) not in reusable]

    print(f"  {len(wanted) - len(fresh)} reusable, {len(fresh)} to embed")
    if args.dry_run:
        for path, kind, heading, _, _ in fresh[:20]:
            where = f" ({heading})" if heading else ""
            print(f"    - {kind}: {path}{where}")
        if len(fresh) > 20:
            print(f"    … and {len(fresh) - 20} more")
        return 0

    if fresh and not key:
        env_key = vault_search.PROVIDERS[provider][0]
        print(f"  ⚠ {env_key} is not set — leaving the committed index as it is.")
        print("    Search still works: the lexical tier needs no key.")
        return 0

    vectors = {}
    for start in range(0, len(fresh), BATCH):
        batch = fresh[start:start + BATCH]
        embedded = vault_search.embed_texts([u[4] for u in batch],
                                            input_type="document")
        if embedded is None:
            print(f"  ⚠ the provider call failed at unit {start} — "
                  "leaving the committed index as it is")
            return 0
        for unit, vector in zip(batch, embedded):
            if dim is None:
                dim = len(vector)
            elif len(vector) != dim:
                print("  ⚠ the provider returned mixed dimensions — aborting")
                return 0
            vectors[(unit[0], unit[1], unit[2], unit[3])] = vault_search.quantise(vector)
        print(f"  embedded {min(start + BATCH, len(fresh))}/{len(fresh)}")

    if dim is None:
        print("  nothing changed")
        return 0

    entries, blob = [], array.array("b")
    for path, kind, heading, digest, _ in wanted:
        key_tuple = (path, kind, heading, digest)
        row = vectors.get(key_tuple)
        if row is None:
            row = reusable[key_tuple]
        entries.append({"path": path, "kind": kind, "heading": heading,
                        "hash": digest})
        blob.extend(row)

    manifest = {
        "version": MANIFEST_VERSION,
        "provider": provider,
        "model": model,
        "dim": dim,
        "quantisation": "int8",
        "scale": vault_search.QUANT_SCALE,
        "pages": len(vault.pages),
        "entries": entries,
    }

    manifest_path = os.path.join(args.root, vault_search.EMBED_MANIFEST)
    bin_path = os.path.join(args.root, vault_search.EMBED_BIN)
    os.makedirs(os.path.dirname(manifest_path) or ".", exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(bin_path, "wb") as fh:
        fh.write(blob.tobytes())

    size_kb = len(blob) / 1024.0
    print(f"  wrote {vault_search.EMBED_MANIFEST} and "
          f"{vault_search.EMBED_BIN}: {len(entries)} vectors × {dim} dims "
          f"({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
