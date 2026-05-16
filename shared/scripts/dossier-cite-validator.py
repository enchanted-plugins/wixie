#!/usr/bin/env python3
"""dossier-cite-validator.py — Phase 6 trace-check (Test A + Test B) at write-time.

Closes G-4 in the deep-research gaps roadmap: catches synthesis-prose cites
that don't trace to a supporting finding in sources.jsonl BEFORE the Phase 6
verifier rejects the brief.

Mechanical reproduction of `plugins/deep-research/agents/verifier.md` Steps 2-4
(web-citation branch only — Test C interval-overlap is out of scope here; the
target is markdown dossier prose, not code citations).

Inputs:
  --dossier <path.md>     dossier markdown to scan for S-cites
  --sources <path.jsonl>  sources.jsonl with findings[].claim + findings[].quote
  --claims  <path.json>   OPTIONAL: claims.json for cite-ID enumeration sanity check

Output:
  JSON to stdout:
    {
      "total_cites_checked": N,
      "violations": [{claim_excerpt, cite, reason}, ...],
      "pass_rate": float,
      "notes": "..."
    }

Honest-numbers contract:
  - No fuzzy semantic matching. Tests A+B reduce to substring / synonym checks
    over a small built-in synonym table — paraphrase tolerance only where the
    verifier spec explicitly allows ("uses X" ↔ "employs X"; "5-stage" ↔ "five-stage").
  - A cite PASSES if AT LEAST ONE finding in the cited source passes BOTH
    Test A (subject match) AND Test B (action/property match).
  - Stdlib only — no external deps.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ---------- citation extraction ---------------------------------------------

# Match S<n> tokens in dossier prose. Accepts: S14, (S14), [S14], (S14, S15),
# [S14, S15], cite=S14. Excludes runs that look like SHA fragments or unrelated
# capitalized words by requiring digit-only suffix.
CITE_TOKEN_RE = re.compile(r"\bS(\d+)\b")

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\*\(\[])")


@dataclass
class Cite:
    cite_id: str          # e.g. "S14"
    supported_text: str   # the surrounding sentence (or table cell / list item)
    line_no: int          # 1-based line number for diagnostics


def _split_into_units(markdown: str) -> list[tuple[int, str]]:
    """Walk the markdown line-by-line. Treat each line as the unit of cite
    context, since dossier tables and bullet lists put each claim on one line.
    Skip code fences."""
    units: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(markdown.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            continue
        units.append((i, line))
    return units


def _claim_cell_from_table_row(line: str) -> str:
    """For a markdown table row `| claim text | source col | engine | ...`,
    return the FIRST cell (the claim text). Outside table context, return the
    whole line. The Phase 6 verifier scopes supported_text to the *claim*, not
    the cite column."""
    s = line.lstrip()
    if not s.startswith("|"):
        return line
    # Drop leading pipe, split on `|`. Tables also include separator rows
    # like `|---|---|`; ignore those by returning empty.
    cells = [c.strip() for c in s.split("|")]
    # The first element is "" because of the leading pipe.
    cells = [c for c in cells if c != ""]
    if not cells:
        return line
    if re.fullmatch(r"-+:?|:?-+:?", cells[0]):
        return ""  # separator row
    return cells[0]


def extract_cites(markdown: str) -> list[Cite]:
    cites: list[Cite] = []
    for line_no, line in _split_into_units(markdown):
        # For table rows, the claim is in the first cell. For bullets/prose
        # the whole sentence is the supported_text.
        is_table_row = line.lstrip().startswith("|")
        claim_text = _claim_cell_from_table_row(line) if is_table_row else line

        for m in CITE_TOKEN_RE.finditer(line):
            cite_id = f"S{m.group(1)}"
            if is_table_row:
                supported = claim_text
            else:
                sentences = SENTENCE_SPLIT_RE.split(line)
                if len(sentences) > 1:
                    pos = 0
                    supported = line
                    for s in sentences:
                        end = pos + len(s)
                        if pos <= m.start() <= end + 4:
                            supported = s
                            break
                        pos = end + 1
                else:
                    supported = line
            cites.append(Cite(cite_id=cite_id, supported_text=supported.strip(), line_no=line_no))
    return cites


# ---------- sources index ----------------------------------------------------

def load_sources(path: Path) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"WARN: malformed sources.jsonl line: {e}", file=sys.stderr)
                continue
            sid = obj.get("id")
            if not sid:
                continue
            idx[sid] = obj
    return idx


# ---------- Test A: subject match -------------------------------------------

ARTICLES_AND_PRONOUNS = {
    "the", "a", "an", "this", "that", "these", "those",
    "it", "its", "they", "them", "their", "he", "she", "his", "her",
    "we", "us", "our", "you", "your", "i", "my",
    "what", "which", "who", "whose", "where", "when", "why", "how",
    "is", "are", "was", "were", "be", "been", "being",
    "and", "but", "or", "so", "yet", "for", "nor",
    "in", "on", "at", "of", "to", "by", "with", "from", "as",
}

# Tokens we strip from the front of a supported_text to get to the subject.
# Markdown table rows often start with bold tokens, pipes, etc.
def _clean_for_subject(text: str) -> str:
    # strip markdown structural noise
    t = text.lstrip("|*-# \t")
    # remove leading bold markers and parenthetical openers
    t = re.sub(r"^\*{1,3}", "", t)
    # collapse whitespace
    t = re.sub(r"\s+", " ", t)
    return t.strip()


# Adjectives that often lead a claim heading but don't carry subject identity.
# Verifier spec says "first noun or proper noun" — these are descriptive
# adjectives that should be skipped to find the actual noun phrase.
LEADING_ADJECTIVES = {
    "quadratic", "hybrid", "layered", "interpretable", "native", "multi",
    "cross", "single", "double", "open", "closed", "deep", "shallow", "raw",
    "new", "old", "current", "recent", "latest", "early", "late",
    "fast", "slow", "lightweight", "heavyweight",
    "manual", "automatic", "automated", "explicit", "implicit",
    "linear", "nonlinear", "global", "local", "static", "dynamic",
    "small", "large", "huge", "tiny", "mini", "macro", "micro",
}

# Extra proper-noun fragments not in the synonym table. The full set is built
# lazily at first call to extract_subject() to avoid module-load ordering issues.
_EXTRA_PROPER_NOUNS = {
    "owasp", "cve", "github", "sat-diff", "open swe", "sweep",
    "memoryarena", "voyager", "promptguard", "memento", "promptlayer",
    "phoenix", "arize", "pezzo", "opik", "puaro", "openssl",
    "cvss", "cwe", "rce", "json", "yaml", "toml", "css", "sbom",
}

_KNOWN_PROPER_NOUNS_CACHE: set[str] | None = None


def _known_proper_nouns() -> set[str]:
    global _KNOWN_PROPER_NOUNS_CACHE
    if _KNOWN_PROPER_NOUNS_CACHE is not None:
        return _KNOWN_PROPER_NOUNS_CACHE
    out: set[str] = set(_EXTRA_PROPER_NOUNS)
    for canon, group in SUBJECT_SYNONYMS.items():
        out.add(canon.lower())
        for syn in group:
            out.add(syn.lower())
    _KNOWN_PROPER_NOUNS_CACHE = out
    return out


def extract_subject(supported_text: str) -> str:
    """Verifier Step 4 Test A: the first noun or proper noun that isn't an
    article or a pronoun. Approximation:
      1. Tokenize the cleaned claim.
      2. Look for a known proper-noun fragment anywhere in the first ~6
         content tokens — it wins (matches the verifier's "obvious synonym"
         leeway in identifying the real subject).
      3. Else pick the first non-stopword, non-leading-adjective capitalized token.
      4. Else first non-stopword content token of len ≥ 3.
    """
    cleaned = _clean_for_subject(supported_text)
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9._\-+/]*", cleaned)
    content = [t for t in tokens if t.lower() not in ARTICLES_AND_PRONOUNS]
    # Pass 1: known proper noun (or multi-word group) in the first 8 content tokens.
    window = " ".join(content[:8]).lower()
    for proper in sorted(_known_proper_nouns(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(proper)}\b", window):
            return proper
    # Pass 2: first capitalized non-stopword non-adjective token.
    for tok in content:
        if tok.lower() in LEADING_ADJECTIVES:
            continue
        if tok[0].isupper() and len(tok) > 1:
            return tok
    # Pass 3: first non-adjective non-stopword content token.
    for tok in content:
        if tok.lower() in LEADING_ADJECTIVES:
            continue
        if len(tok) >= 3:
            return tok
    # Pass 4: anything.
    for tok in content:
        if len(tok) >= 3:
            return tok
    return ""


# Light synonym table — verifier explicitly cites "Perplexity ↔ Perplexity's
# system", "the agent ↔ agents", "GPT-5 ↔ gpt-5". Keep this conservative.
SUBJECT_SYNONYMS: dict[str, set[str]] = {
    "semgrep": {"semgrep", "semgrep ce", "semgrep pro"},
    "codeql": {"codeql"},
    "trufflehog": {"trufflehog"},
    "gitleaks": {"gitleaks"},
    "dspy": {"dspy", "miprov2", "mipro", "bootstrapfewshot"},
    "openhands": {"openhands", "open hands", "swe-agent"},
    "langgraph": {"langgraph"},
    "smolagents": {"smolagents"},
    "langfuse": {"langfuse"},
    "langsmith": {"langsmith"},
    "helicone": {"helicone"},
    "opentelemetry": {"opentelemetry", "otel", "gen_ai", "genai"},
    "litellm": {"litellm"},
    "openrouter": {"openrouter"},
    "conventional": {"conventional", "conventional-commits", "conventional commits"},
    "semantic-release": {"semantic-release", "semantic release"},
    "commitizen": {"commitizen"},
    "commitlint": {"commitlint"},
    "echoleak": {"echoleak", "cve-2025-32711"},
    "osv-scanner": {"osv-scanner", "osv.dev"},
    "syft": {"syft"},
    "grype": {"grype"},
    "gumtree": {"gumtree"},
    "ast-grep": {"ast-grep", "tree-sitter"},
    "joern": {"joern", "code property graph", "cpg"},
    "sourcegraph": {"sourcegraph"},
    "promptfoo": {"promptfoo"},
    "garak": {"garak"},
    "nemo": {"nemo", "nemo guardrails"},
    "agents.md": {"agents.md", "agents md"},
    "codeowners": {"codeowners"},
    "wayback": {"wayback", "wayback machine"},
    "crewai": {"crewai"},
}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def _subject_synonyms_for(subject: str) -> set[str]:
    s = subject.lower()
    out = {s}
    # Add stem (strip trailing 's, plural s)
    if s.endswith("'s"):
        out.add(s[:-2])
    if s.endswith("s") and len(s) > 3:
        out.add(s[:-1])
    # Add canonical groups
    for canon, group in SUBJECT_SYNONYMS.items():
        if s in group or any(s.startswith(g) or g.startswith(s) for g in group):
            out.update(group)
            out.add(canon)
    return {x for x in out if x}


def test_a_subject_match(subject: str, finding_text: str) -> bool:
    """Subject occurs in finding_text via exact or obvious-synonym match."""
    if not subject:
        return False
    haystack = _norm(finding_text)
    for cand in _subject_synonyms_for(subject):
        cand_n = _norm(cand)
        if not cand_n:
            continue
        # Word-boundary substring match against the normalized haystack.
        if re.search(rf"\b{re.escape(cand_n)}\b", haystack):
            return True
    return False


# ---------- Test B: action / property match ---------------------------------

# Conservative stopword list for content tokens used to derive action keywords.
STOPWORDS = ARTICLES_AND_PRONOUNS | {
    "via", "into", "onto", "than", "then", "while", "during", "before", "after",
    "vs", "vs.", "per", "across", "between", "among",
    "do", "does", "did", "have", "has", "had", "having",
    "can", "may", "might", "must", "should", "could", "would", "will",
    "not", "no", "yes", "only", "also", "even", "still",
    "very", "more", "most", "less", "much", "many", "some", "any", "all",
    "such", "like", "than", "thus", "however", "moreover",
    "one", "two", "three", "four", "five",
}

# Verifier explicitly allows "uses X ↔ employs X", "5-stage ↔ five-stage" —
# keep a tiny normalisation map. Numbers spelled-out get normalized to digits.
WORD_NUMBERS = {
    "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}


def _action_tokens(text: str, drop_subject: str = "") -> set[str]:
    """Extract a bag of content tokens representing the action/property.
    We drop articles, pronouns, function words, and the subject itself."""
    norm = _norm(text)
    drop_subj_n = _norm(drop_subject)
    drop_subj_tokens = set(drop_subj_n.split())
    drop_subj_synonyms = set()
    for syn in _subject_synonyms_for(drop_subject) if drop_subject else set():
        drop_subj_synonyms.update(_norm(syn).split())
    tokens = []
    for tok in norm.split():
        if tok in STOPWORDS:
            continue
        if tok in drop_subj_tokens or tok in drop_subj_synonyms:
            continue
        if len(tok) < 3 and not tok.isdigit():
            continue
        # Normalize spelled-out numbers and trailing 's plural.
        tok = WORD_NUMBERS.get(tok, tok)
        if tok.endswith("s") and len(tok) > 4:
            tok = tok[:-1]
        tokens.append(tok)
    return set(tokens)


def test_b_action_match(supported_text: str, finding_text: str, subject: str) -> tuple[bool, int]:
    """Return (passed, overlap_count). PASS if the supported_text's content
    tokens overlap the finding's content tokens by at least 2 distinct tokens
    (after subject and stopword removal). This is the spec's "paraphrase
    counts if the meaning is clearly the same" reduced to a mechanical floor.

    Threshold = 2: a single shared word is the F11 lexical-overlap trap
    (verifier failure mode). Two distinct content tokens means an action
    verb + an object/qualifier overlap, which is the minimum signal for
    semantic correspondence.
    """
    sup = _action_tokens(supported_text, drop_subject=subject)
    fnd = _action_tokens(finding_text, drop_subject=subject)
    overlap = sup & fnd
    return (len(overlap) >= 2, len(overlap))


# ---------- per-cite verdict -------------------------------------------------

@dataclass
class Violation:
    cite: str
    claim_excerpt: str
    reason: str
    line_no: int


def verify_cite(cite: Cite, sources_idx: dict[str, dict]) -> Violation | None:
    if cite.cite_id not in sources_idx:
        return Violation(
            cite=cite.cite_id,
            claim_excerpt=cite.supported_text[:80],
            reason="cited ID not in sources.jsonl",
            line_no=cite.line_no,
        )
    src = sources_idx[cite.cite_id]
    findings = src.get("findings", []) or []
    if not findings:
        return Violation(
            cite=cite.cite_id,
            claim_excerpt=cite.supported_text[:80],
            reason="source has no findings",
            line_no=cite.line_no,
        )

    subject = extract_subject(cite.supported_text)
    any_a_pass = False
    any_b_pass = False
    best_overlap = 0

    for fnd in findings:
        f_claim = fnd.get("claim", "") or ""
        f_quote = fnd.get("quote", "") or ""
        combined = f_claim + " || " + f_quote
        a = test_a_subject_match(subject, combined)
        b_pass, overlap = test_b_action_match(cite.supported_text, combined, subject)
        if a:
            any_a_pass = True
        if b_pass:
            any_b_pass = True
        best_overlap = max(best_overlap, overlap)
        if a and b_pass:
            return None  # PASS — at least one finding clears both tests

    # Determine the most specific failure reason.
    if not any_a_pass and not any_b_pass:
        reason = "no finding passes both tests"
    elif not any_a_pass:
        reason = f"Test A failed — subject '{subject}' not in source's findings"
    else:
        reason = f"Test B failed — action/property mismatch (best overlap {best_overlap})"
    return Violation(
        cite=cite.cite_id,
        claim_excerpt=cite.supported_text[:80],
        reason=reason,
        line_no=cite.line_no,
    )


# ---------- main -------------------------------------------------------------

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dossier", type=Path, required=True)
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--claims", type=Path, required=False, default=None)
    ap.add_argument("--quiet", action="store_true", help="Suppress per-violation line output (machine-readable JSON only).")
    args = ap.parse_args(argv)

    for p in (args.dossier, args.sources):
        if not p.exists():
            print(f"ERROR: missing {p}", file=sys.stderr)
            return 2

    markdown = args.dossier.read_text(encoding="utf-8")
    sources_idx = load_sources(args.sources)
    cites = extract_cites(markdown)

    # Optional sanity check: every cite ID present in claims.json should also
    # be in sources.jsonl, otherwise the brief generation already drifted.
    claims_cite_ids: set[str] = set()
    if args.claims and args.claims.exists():
        claims_obj = json.loads(args.claims.read_text(encoding="utf-8"))
        # claims.json may carry a top-level "claims" list, or only contradiction
        # entries with `ids` keyed as C<n> — neither is necessary for S-cite
        # validation, so we just record what we find for diagnostics.
        for entry in claims_obj.get("claims", []) or []:
            for sid in entry.get("supporting", []) or []:
                claims_cite_ids.add(sid)

    violations: list[Violation] = []
    for c in cites:
        v = verify_cite(c, sources_idx)
        if v is not None:
            violations.append(v)

    total = len(cites)
    pass_rate = 0.0 if total == 0 else (total - len(violations)) / total

    result = {
        "total_cites_checked": total,
        "unique_cite_ids": sorted({c.cite_id for c in cites}, key=lambda s: int(s[1:])),
        "violations": [
            {
                "cite": v.cite,
                "line": v.line_no,
                "claim_excerpt": v.claim_excerpt,
                "reason": v.reason,
            }
            for v in violations
        ],
        "violation_count": len(violations),
        "pass_rate": round(pass_rate, 4),
        "notes": (
            f"Validated {total} S-cite occurrences across "
            f"{len({c.cite_id for c in cites})} distinct source IDs against "
            f"{len(sources_idx)} sources. "
            f"{len(violations)} violations (mechanical Test A + Test B)."
        ),
    }

    print(json.dumps(result, indent=2))

    if not args.quiet and violations:
        sys.stderr.write(f"\n{len(violations)} cite violation(s):\n")
        for v in violations:
            sys.stderr.write(f"  L{v.line_no}  {v.cite}  {v.reason}\n    >> {v.claim_excerpt}\n")

    # Exit 0 always — caller decides whether violations block. The Phase 6
    # verifier is the gatekeeper; this script is the write-time advisor.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
