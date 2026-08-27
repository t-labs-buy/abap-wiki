"""Ranked search over vault page bodies.

`grep -ril` answers "which files contain this string". That is the wrong
question for a vault whose pages are written in the team's vocabulary and
queried in the reader's: a page titled "Credit release blocked by legacy limit
table" is invisible to a search for "why do orders get stuck". This module
answers "which pages are most likely to hold the answer", and it does it for
every caller — the abap-wiki skill on a reader's laptop included.

Two tiers, and the second is optional by design:

  1. **Lexical.** BM25F over weighted fields, with the query expanded through
     meta/entities.md so a reader who says "Order-to-Cash" reaches OTC pages.
     No dependencies, no credentials, no network. Always available.
  2. **Semantic.** Cosine over the vectors embed-index.py precomputed and
     committed to meta/. Needs an embedding key at query time to encode the
     question; without one this tier simply does not run and the caller gets
     tier 1. See embeddings_available().

When both run, results are fused by reciprocal rank rather than by score:
the two tiers produce numbers on incomparable scales, and RRF needs no
calibration to combine them.

Standard library only — deliberately. graph-health.py imports this and its
workflow installs nothing, and the skill runs it on machines where a pip
install is not ours to perform. Even the provider call goes through
urllib.request. Never writes.
"""

import array
import collections
import json
import math
import os
import re
import urllib.error
import urllib.request

from vault_model import Vault

# --------------------------------------------------------------------------
# Tuning
# --------------------------------------------------------------------------

# BM25 saturation and length normalisation. Standard values; the corpus is
# small and homogeneous enough that tuning them would be overfitting.
K1 = 1.2
B = 0.75

# Field weights, applied as term-frequency multipliers (BM25F). A page *named*
# for the thing you asked about should outrank one that mentions it in passing,
# which raw body frequency alone gets backwards on long pages.
FIELD_WEIGHTS = {
    "name":     3.0,   # the filename — the vault's strongest naming signal
    "title":    2.0,   # frontmatter title
    "tags":     2.0,   # controlled vocabulary: a tag is a curated claim
    "headings": 2.0,   # ## and ### lines
    "body":     1.0,
}

# An alias reached through the entity registry is good evidence but weaker
# than the reader's own words: "finance" expands to both RTR and FI.
ALIAS_WEIGHT = 0.7

# Fraction of a neighbour's score a page absorbs from the wikilink graph.
# Small on purpose: this breaks ties between comparable pages and pulls in the
# development record next to the decision that scored, it does not float
# unrelated pages into the results.
NEIGHBOUR_BOOST = 0.18

# Reciprocal-rank-fusion constant. 60 is the value from the original paper and
# is deliberately large: it flattens the top of each list so neither tier can
# win a position on rank 1 alone.
RRF_K = 60

# Tokens shorter than this are dropped — except that SAP slugs are two
# characters (SD, MM, FI, CO, PP), so the floor is 2 and not 3.
MIN_TOKEN = 2

STOPWORDS = frozenset("""
a an the and or but if then than that this these those there here
is are was were be been being am
do does did doing done
have has had having
i we you he she it they them us our your their its his her
of in on at to for from by with without into onto over under
as about after before during while when where which who whom whose why how
not no nor only just also very much many more most some any each every
can could shall should will would may might must
what s t don t
""".split())

# Words that appear on nearly every page of a vault about one project. They are
# not English stopwords, but they carry no discriminating signal here, and BM25
# would otherwise reward a page for saying "vault" a lot. IDF handles most of
# this on a large corpus; the vault is small enough that it needs the help.
VAULT_STOPWORDS = frozenset("""
page pages vault linked link links section sections note notes
""".split())

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*")
CAMEL_RE = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|[0-9]+")
HEADING_RE = re.compile(r"^#{2,6}\s+(.*)$", re.MULTILINE)
BACKTICK_RE = re.compile(r"`([^`]+)`")
TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$", re.MULTILINE)
WIKILINK_ONLY_RE = re.compile(r"^(?:\[\[[^\]]+\]\][\s,;]*)+$")

EMBED_BIN = os.path.join("meta", "embeddings.bin")
EMBED_MANIFEST = os.path.join("meta", "embeddings.json")

# Vectors are stored unit-normalised and quantised to int8 with this scale, so
# a dot product of two rows divided by SCALE**2 is their cosine similarity.
# No per-row scale factor is needed and none is stored.
QUANT_SCALE = 127.0


# --------------------------------------------------------------------------
# Tokenisation
# --------------------------------------------------------------------------

def split_identifier(token):
    """Sub-tokens of a compound identifier, the full token excluded.

    ABAP names carry their meaning in their parts: a reader who half-remembers
    ZSD_ORDER_CHECK and searches for "order check" should still find it. Also
    covers camelCase, which turns up in interface and CDS names.
    """
    parts = [p for p in token.split("_") if p]
    if len(parts) == 1:
        parts = CAMEL_RE.findall(token)
    if len(parts) < 2:
        return []
    return [p.lower() for p in parts if len(p) >= MIN_TOKEN]


def tokenize(text, keep_stopwords=False):
    """Lowercase tokens, with compound identifiers also emitted in parts."""
    out = []
    for raw in TOKEN_RE.findall(text or ""):
        low = raw.lower()
        if len(low) < MIN_TOKEN:
            continue
        if not keep_stopwords and (low in STOPWORDS or low in VAULT_STOPWORDS):
            continue
        out.append(low)
        out.extend(split_identifier(raw))
    return out


# --------------------------------------------------------------------------
# Entity registry
# --------------------------------------------------------------------------

def load_aliases(root):
    """alias phrase -> canonical slug, from meta/entities.md.

    The registry is the normalisation work the vault already does at ingest;
    reading it here means "Order-to-Cash", "o2c" and "order to cash" all reach
    OTC pages without a single embedding. Every markdown table row in the file
    is treated the same way: first cell is the canonical name, and every
    backticked string plus the display name in the row is an alias for it.
    That covers the workstream, module, system and vendor tables and the tag
    vocabulary, which share the shape without sharing a heading.

    A missing or malformed registry is not an error — expansion is an
    enhancement, and search must work without it.
    """
    path = os.path.join(root, "meta", "entities.md")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return {}

    aliases = {}
    for row in TABLE_ROW_RE.findall(text):
        cells = [c.strip() for c in row.split("|")]
        if len(cells) < 2:
            continue
        canonical = cells[0].strip("*` ")
        # Header rows and the ---|--- separator carry no entity.
        if not canonical or set(canonical) <= set("- :") or " " in canonical:
            continue
        if canonical.lower() in ("canonical slug", "tag"):
            continue
        variants = set()
        for cell in cells[1:]:
            variants.update(m.strip().lower() for m in BACKTICK_RE.findall(cell))
            plain = cell.strip("*_ ")
            # A display name ("Order-to-Cash"); status cells and prose are not.
            if plain and "`" not in cell and len(plain) < 40 and not plain.startswith("("):
                variants.add(plain.lower())
        for variant in variants:
            variant = variant.strip()
            if variant and variant != canonical.lower() and "*" not in variant:
                aliases.setdefault(variant, canonical)
    return aliases


def expand_query(query, aliases):
    """[(token, weight)] — the reader's own tokens, plus registry expansions.

    Multi-word aliases are matched against the raw query string before
    tokenisation, because "order to cash" is three tokens that mean one thing.
    """
    terms = collections.OrderedDict()
    for tok in tokenize(query):
        terms[tok] = max(terms.get(tok, 0.0), 1.0)

    low = " " + " ".join(tokenize(query, keep_stopwords=True)) + " "
    hits = set()
    for alias, canonical in aliases.items():
        if f" {alias} " in low or alias in terms:
            hits.add(canonical)
    for canonical in sorted(hits):
        for tok in tokenize(canonical):
            if tok not in terms:
                terms[tok] = ALIAS_WEIGHT
    return list(terms.items())


# --------------------------------------------------------------------------
# Lexical index
# --------------------------------------------------------------------------

def strip_frontmatter(text):
    """Body text without the YAML block.

    Frontmatter is indexed field by field (name, title, tags) with weights that
    say what each one is worth. Leaving it in the body as well would index
    `created`, `owner` and `source_files` as prose and count every real field
    twice.
    """
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    return text if end == -1 else text[end + 4:]


def page_fields(page):
    """The weighted fields of one page. Backlinks are excluded: `page.body`
    already drops the `## Linked from` section, and a page must not rank for
    the names of pages that happen to cite it."""
    body = strip_frontmatter(page.body)
    return {
        "name":     page.name,
        "title":    page.front.get("title", ""),
        "tags":     " ".join(page.tags),
        "headings": " ".join(HEADING_RE.findall(body)),
        "body":     body,
    }


class LexicalIndex:
    """BM25F over the four content zones. Built at query time — a few hundred
    pages index in well under a second, and an index that is never persisted
    can never go stale."""

    def __init__(self, vault):
        self.vault = vault
        self.tf = {}            # path -> {term: weighted frequency}
        self.length = {}        # path -> weighted length
        self.df = collections.Counter()

        for page in vault.pages:
            weighted = collections.defaultdict(float)
            for field, text in page_fields(page).items():
                weight = FIELD_WEIGHTS[field]
                for tok in tokenize(text):
                    weighted[tok] += weight
            self.tf[page.path] = dict(weighted)
            self.length[page.path] = sum(weighted.values())
            for term in weighted:
                self.df[term] += 1

        self.n = len(vault.pages) or 1
        self.avg_len = (sum(self.length.values()) / self.n) if self.length else 1.0

    def idf(self, term):
        df = self.df.get(term, 0)
        # Standard BM25 probabilistic IDF, floored: a term in every page scores
        # ~0 rather than going negative and penalising a page for containing it.
        return max(0.0, math.log(1.0 + (self.n - df + 0.5) / (df + 0.5)))

    def score(self, terms, candidates=None):
        """path -> score, for pages matching at least one term."""
        scores = collections.defaultdict(float)
        for term, weight in terms:
            idf = self.idf(term)
            if idf <= 0:
                continue
            for path, tf in self.tf.items():
                freq = tf.get(term)
                if not freq:
                    continue
                if candidates is not None and path not in candidates:
                    continue
                norm = 1.0 - B + B * (self.length[path] / self.avg_len)
                scores[path] += weight * idf * (freq * (K1 + 1.0)) / (freq + K1 * norm)
        return dict(scores)


def apply_graph_boost(vault, scores):
    """Lift pages adjacent to strong matches.

    An answer usually spans a decision and the development it changed. The
    decision matches the query wording; the development often does not, but it
    is one wikilink away and the reader needs it. Boost is computed from the
    pre-boost scores only, so it never cascades.
    """
    if not scores:
        return scores
    boosted = dict(scores)
    for path in scores:
        neighbours = vault.forward_edges[path] | vault.inbound[path]
        gain = sum(scores.get(n, 0.0) for n in neighbours)
        if gain:
            boosted[path] += NEIGHBOUR_BOOST * gain / math.sqrt(len(neighbours))
    return boosted


# --------------------------------------------------------------------------
# Semantic tier
# --------------------------------------------------------------------------

PROVIDERS = {
    # provider -> (env var for the key, default model, endpoint, dimension key)
    "voyage": ("VOYAGE_API_KEY", "voyage-3.5-lite",
               "https://api.voyageai.com/v1/embeddings"),
    "openai": ("OPENAI_API_KEY", "text-embedding-3-small",
               "https://api.openai.com/v1/embeddings"),
}


def provider_config():
    """(name, key, model, url) or (name, None, model, url) when no key is set.

    The model name is configuration, not code: providers rename and retire
    models faster than this repo changes, so VAULT_EMBED_MODEL overrides it
    without a commit.
    """
    name = os.environ.get("VAULT_EMBED_PROVIDER", "voyage").strip().lower()
    if name not in PROVIDERS:
        name = "voyage"
    env_key, default_model, url = PROVIDERS[name]
    model = os.environ.get("VAULT_EMBED_MODEL", default_model)
    return name, os.environ.get(env_key), model, url


def embed_texts(texts, input_type=None, timeout=60):
    """Embed via the configured provider. Returns [[float]] or None.

    Never raises: no key, no network and a provider outage are ordinary states
    for a tier that is optional by construction. The caller falls back.
    """
    if not texts:
        return []
    name, key, model, url = provider_config()
    if not key:
        return None

    payload = {"model": model, "input": texts}
    if name == "voyage" and input_type:
        payload["input_type"] = input_type

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return None

    rows = body.get("data")
    if not isinstance(rows, list) or len(rows) != len(texts):
        return None
    try:
        # Both providers return {"data": [{"index": i, "embedding": [...]}, ...]}
        ordered = sorted(rows, key=lambda r: r.get("index", 0))
        return [[float(x) for x in r["embedding"]] for r in ordered]
    except (KeyError, TypeError, ValueError):
        return None


def normalise(vector):
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return list(vector)
    return [x / norm for x in vector]


def quantise(vector):
    """Unit-normalise, then scale to int8. Cosine survives as a dot product."""
    return [max(-127, min(127, int(round(x * QUANT_SCALE))))
            for x in normalise(vector)]


def load_embeddings(root):
    """(manifest, array('b')) or (None, None).

    A missing, unreadable, or internally inconsistent index is treated as
    absent rather than as an error: the lexical tier answers either way, and a
    half-read vector file would silently return wrong neighbours.
    """
    manifest_path = os.path.join(root, EMBED_MANIFEST)
    bin_path = os.path.join(root, EMBED_BIN)
    if not (os.path.isfile(manifest_path) and os.path.isfile(bin_path)):
        return None, None
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        vectors = array.array("b")
        with open(bin_path, "rb") as fh:
            vectors.frombytes(fh.read())
    except (OSError, ValueError, json.JSONDecodeError):
        return None, None

    dim = manifest.get("dim")
    entries = manifest.get("entries")
    if not isinstance(dim, int) or dim <= 0 or not isinstance(entries, list):
        return None, None
    if len(vectors) != dim * len(entries):
        return None, None
    return manifest, vectors


def embeddings_available(root):
    manifest, _ = load_embeddings(root)
    return manifest is not None


def semantic_scores(root, query, vault):
    """path -> cosine, or None when the tier cannot run.

    Section vectors collapse into their page: the vault's citable unit is the
    page, so a page keeps the score of its best-matching section.
    """
    manifest, vectors = load_embeddings(root)
    if manifest is None:
        return None
    embedded = embed_texts([query], input_type="query")
    if not embedded:
        return None

    dim = manifest["dim"]
    q = normalise(embedded[0])
    if len(q) != dim:
        # The committed index was built with a different model. Silently
        # wrong neighbours are worse than no semantic tier.
        return None

    best = {}
    for i, entry in enumerate(manifest["entries"]):
        path = entry.get("path")
        if path not in vault.by_path:
            continue
        base = i * dim
        dot = 0.0
        for j in range(dim):
            dot += q[j] * vectors[base + j]
        score = dot / QUANT_SCALE
        if score > best.get(path, -2.0):
            best[path] = score
    return best


# --------------------------------------------------------------------------
# Fusion and the public entry point
# --------------------------------------------------------------------------

def rank(scores):
    """path -> 1-based rank, ties broken by path so output is deterministic."""
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return {path: i for i, (path, _) in enumerate(ordered, 1)}


def fuse(lexical, semantic):
    """Reciprocal rank fusion. The two tiers produce numbers on incomparable
    scales — one is a BM25 sum, the other a cosine in [-1, 1] — so they are
    combined by position, which needs no calibration."""
    lex_rank, sem_rank = rank(lexical), rank(semantic)
    fused = {}
    for path in set(lexical) | set(semantic):
        total = 0.0
        if path in lex_rank:
            total += 1.0 / (RRF_K + lex_rank[path])
        if path in sem_rank:
            total += 1.0 / (RRF_K + sem_rank[path])
        fused[path] = total
    return fused


class Hit:
    __slots__ = ("path", "page", "score", "lexical", "semantic", "heading", "excerpt")

    def __init__(self, path, page, score, lexical, semantic, heading, excerpt):
        self.path = path
        self.page = page
        self.score = score
        self.lexical = lexical
        self.semantic = semantic
        self.heading = heading
        self.excerpt = excerpt

    @property
    def flags(self):
        """Provisional-content markers, in the order a reader needs them."""
        out = []
        if self.page.has_conflict:
            out.append("unresolved conflict")
        if "ai-generated" in self.page.tags:
            out.append("unvalidated")
        status = self.page.status
        if status in ("draft", "parked", "archived"):
            out.append(status)
        return out


def best_context(page, terms):
    """(heading, excerpt) — where in the page the query actually landed.

    Cheap and literal on purpose: this is orientation for the reader, not
    evidence, and the caller opens the page next.
    """
    wanted = {t for t, _ in terms}
    heading, best_line, best_hits = "", "", 0
    current = ""
    for line in strip_frontmatter(page.body).splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            current = stripped.lstrip("# ").strip()
            continue
        if not stripped or stripped.startswith(("|", ">", "---")):
            continue
        # A line that is nothing but wikilinks is navigation, not an answer.
        if WIKILINK_ONLY_RE.match(stripped):
            continue
        hits = sum(1 for tok in tokenize(stripped) if tok in wanted)
        if hits > best_hits:
            heading, best_line, best_hits = current, stripped, hits
    excerpt = " ".join(best_line.split())
    if len(excerpt) > 200:
        excerpt = excerpt[:197].rstrip() + "…"
    return heading, excerpt


def search(root, query, top=10, workstream=None, ptype=None, zone=None,
           literal=False, semantic=True, vault=None):
    """Ranked pages for a query. The one entry point every caller uses.

    `semantic=True` means "use the vector tier if it is available"; it is not a
    demand, and no caller has to know whether a key is set.
    """
    vault = vault or Vault(root)
    aliases = {} if literal else load_aliases(root)
    terms = ([(t, 1.0) for t in tokenize(query)] if literal
             else expand_query(query, aliases))
    if not terms:
        return [], {"terms": [], "semantic": False, "reason": "empty query"}

    index = LexicalIndex(vault)
    lexical = apply_graph_boost(vault, index.score(terms))

    sem = semantic_scores(root, query, vault) if semantic and not literal else None
    combined = fuse(lexical, sem) if sem else lexical

    def keep(path):
        page = vault.by_path[path]
        if workstream and page.workstream.upper() != workstream.upper():
            return False
        if ptype and page.type != ptype:
            return False
        if zone and not page.in_zone(zone):
            return False
        return True

    ordered = sorted((p for p in combined if keep(p)),
                     key=lambda p: (-combined[p], p))[:top]

    hits = []
    for path in ordered:
        page = vault.by_path[path]
        heading, excerpt = best_context(page, terms)
        hits.append(Hit(path, page, combined[path],
                        lexical.get(path, 0.0),
                        (sem or {}).get(path), heading, excerpt))

    meta = {
        "terms": terms,
        "semantic": bool(sem),
        "reason": None if sem else semantic_reason(root, semantic, literal),
    }
    return hits, meta


def semantic_reason(root, requested, literal):
    """Why the vector tier did not run — reported, never raised."""
    if literal:
        return "literal mode"
    if not requested:
        return "not requested"
    if not embeddings_available(root):
        return f"no {EMBED_MANIFEST} in this vault"
    _, key, _, _ = provider_config()
    if not key:
        name, _, _, _ = provider_config()
        env_key = PROVIDERS[name][0]
        return f"{env_key} is not set"
    return "the provider call failed"
