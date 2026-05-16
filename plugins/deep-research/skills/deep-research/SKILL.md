---
name: deep-research
description: >
  Deep research engine (E0) that produces a verified, cited claims artifact
  before prompts are engineered. Decomposes the query, fans out parallel
  Haiku fetchers, triangulates claims across independent sources, synthesizes,
  and verifies every claim traces to a fetched quote.
  Auto-fires inside /create when the topic depends on external or
  time-sensitive facts. Also callable standalone.
  Auto-triggers on: "/deep-research", "/research", "research this topic",
  "look up the current state of", "what's the latest on", "fact-check this",
  "find sources on", "before we craft the prompt, research".
  Do not use for static topics (pure logic, timeless writing tasks) or when
  a fresh brief already exists (freshness < 30 days) — reuse it.
  Do not use to render an existing brief — use /research-render for that.
allowed-tools: Read, Write, Grep, Glob, Agent, Bash(mkdir *)
---

# Deep Research (E0)

Produces the factual ground truth that E1–E6 score against. Every load-bearing claim in `claims.json` has at least two independent sources, or is explicitly flagged.

## Inputs

- `<topic>` — slug or free-text topic
- Optional: `--depth quick` (alias `--depth shallow`) — single-round, no adversarial pass, no re-fetch sample
- Optional: `--render` — also run `/research-render` at the end
- Optional: `--mcp <name>` — route Phase 2 fetchers through a configured MCP server (one of `brave-search | tavily | zotero | playwright`). Requires `state/mcp-config.json` + a matching fingerprint file under `state/mcp-manifests/<name>.fingerprint.json`. See `@../vis/packages/web/conduct/mcp-research-discipline.md` for per-query-class routing and the three security gates (manifest audit, version pin, least-privilege creds). Per-fetcher routing is also valid — the orchestrator may pass `--mcp` on only some Phase 2 dispatches and leave the rest on the static `WebSearch` + `WebFetch` path. **MCP is opt-in**; omitting the flag preserves the existing default.

## Output

```
state/briefs/<slug>/
├── claims.json       triangulated claims — machine-facing (/create reads this)
├── sources.jsonl     raw source-level findings
└── trace.json        per-phase execution trace + verdict
```

`report.md` is produced separately via `/research-render`.

## Discipline — governed by vis conduct modules

The work-budget floors, six-phase shape, adversarial-round contract, wall-clock floor, untrusted-source wrapping, independence checks, dissemination score, 4-class support taxonomy, re-fetch protocol, and Wayback fallback all live in vis. E0 is one implementation of that contract — read the modules first; they're authoritative:

- `@../vis/packages/web/conduct/research-pipeline.md` — the 6-phase shape + work-budget floors + adversarial-round contract
- `@../vis/packages/web/conduct/source-discipline.md` — untrusted-source wrapping + independence + τ + dissemination_score + confidence tiers
- `@../vis/packages/web/conduct/citation-verification.md` — trace check + re-fetch + Wayback fallback + 4-class support_class
- `@../vis/packages/web/conduct/web-fetch.md` — single-fetch hygiene (cache, dedup, budget)

E0-specific wiring follows below.

## Agent tier map

| Phase | Tier | E0 wiring |
|-------|------|-----------|
| 1 Decompose | Opus (inline) | The caller writes sub-questions + seed queries to `trace.json#phase1` |
| 2 Cast | Haiku × N | `Agent(general-purpose, haiku, prompt="Run the fetcher at ${CLAUDE_PLUGIN_ROOT}/agents/fetcher.md with query=<q> sub_question=<sq>")` — parallel dispatch in one message. **MCP dispatch (optional, per-fetcher):** when an MCP is the right call for a given (`query`, `sub_question`) pair per the routing table in `@../vis/packages/web/conduct/mcp-research-discipline.md`, the orchestrator appends `mcp=<name>` to the prompt — the fetcher then delegates to `${CLAUDE_PLUGIN_ROOT}/agents/mcp-fetcher.md` which runs the three security gates (manifest audit, version pin, least-privilege creds) before any MCP tool call. Gate failures return `{"error": "<gate>-failed"}` and the orchestrator decides whether to re-dispatch on the static path. **Never let `mcp-fetcher.md` silently fall back to `WebSearch`** — that breaks the F22 capability-fidelity contract. |
| 3 Triangulate | Sonnet | `Agent(general-purpose, sonnet, prompt="Run the triangulator at ${CLAUDE_PLUGIN_ROOT}/agents/triangulator.md with sources_path=<path> round=<N> sub_questions=<json> prior_claim_count=<N>")` |
| 4 Gap-fill + adversarial | Opus decides, Haiku fetches | Consume triangulator's `negation_queries` for the adversarial family; generate gap-fill from `coverage_gaps`; re-enter Phase 2 |
| 5 Synthesize | Opus (inline) | Codify triangulator's final claim graph into `claims.json` (schema below) |
| 6 Verify | Haiku | `Agent(general-purpose, haiku, prompt="Run the verifier at ${CLAUDE_PLUGIN_ROOT}/agents/verifier.md with target_path=<path> sources_path=<path> refetch_pct=<10\|0>")` |
| 6c CIBER | Haiku | `Agent(general-purpose, haiku, prompt="Run the CIBER agent at ${CLAUDE_PLUGIN_ROOT}/agents/ciber.md with claims_path=<path> sources_path=<path> top_n=10 k_per_claim=3")` — full depth only; skipped at `--depth quick` |

All work-budget floors per `research-pipeline.md` — re-decompose / re-dispatch on floor violations rather than proceeding under-budget.

## Phase 6c — Multi-aspect interrogation (CIBER)

Phase 6c runs *after* Phase 6 verifier returns `verify_passed: true` (`violations` empty, `refetch_pass_rate ≥ 0.9`), and *before* the verdict is finalized. Per `@../vis/packages/web/conduct/citation-verification.md` § "Multi-aspect interrogation (CIBER)".

**Why it exists.** Trace check + re-fetch confirm a claim is *attributable* to its sources. CIBER confirms the claim is *stable* under re-framing. A `high`-confidence claim that collapses under paraphrase or negation has load-bearing wording that the sources don't actually back. The round-2 adversarial pass (Phase 4) hunts for *new* contradicting queries; Phase 6c re-frames the original claims against the *existing* corpus — orthogonal coverage.

**Dispatch syntax.**

```
Agent(general-purpose, haiku,
  prompt="Run the CIBER agent at ${CLAUDE_PLUGIN_ROOT}/agents/ciber.md with claims_path=<path-to-claims.json> sources_path=<path-to-sources.jsonl> top_n=10 k_per_claim=3")
```

Defaults: `top_n = 10`, `k_per_claim = 3` (1 negation + 1 verb-swap + 1 scope-shift, per the agent's mechanical patterns). Configurable upward — Haiku tier is cheap; raising `top_n` to 20–30 is a low-cost robustness bump for high-stakes briefs.

**Skip conditions.**
- `--depth quick` → skip entirely (matches Phase 6b re-fetch skip).
- Fewer than 2 `confidence: high` claims in `claims.json` → skip; record `ciber_skipped: "insufficient-high-confidence-claims"` in `trace.json`.
- Phase 6b returned `refetch_pass_rate < 0.7` → Phase 6c skipped; brief is already heading to FAIL/regenerate.

**Consuming the result.** The CIBER agent returns:

```json
{
  "ciber_passed": true|false,
  "consistency_failures": [
    {"claim_id": "C?",
     "failed_reframing": "...",
     "failed_reframing_type": "negation|verb-swap|scope-shift",
     "contradicting_source_ids": ["S?"],
     "severity": "negation_supported|paraphrase_split"}
  ],
  ...
}
```

The orchestrator applies the demotion mechanically (CIBER is read-only; it diagnoses, the orchestrator mutates):

1. For each entry in `consistency_failures`:
   - Locate the claim by `claim_id` in `claims.json#claims`.
   - If `confidence == "high"` → set `confidence: "medium-contested"`.
   - Increment `dissemination_score` by `0.25` per failure (cap at `1.0`).
   - Append `contradicting_source_ids` to a new `contests:` array on the claim entry (separate from `supporting:`).
   - Append `{ids: [<claim_id>], topic: "CIBER consistency failure", description: "<failed_reframing>"}` to `claims.json#unresolved_contradictions`.

2. Set `claims.json#ciber_passed = <agent's value>` and record agent output verbatim in `trace.json#phase6c`.

3. Verdict consequence — see "Verdict — wixie's mapping over the vis criteria" below.

**Interaction with Phase 6b (re-fetch).** Phase 6b runs first. If 6b fails hard (`refetch_pass_rate < 0.7`), Phase 6c is skipped and the brief regenerates from a fresh Phase 2 — CIBER on a poisoned corpus would amplify noise. If 6b is in the flagged band (`0.7 ≤ refetch_pass_rate < 0.9`), Phase 6c still runs — the brief is already PARTIAL; CIBER's job is to identify *which* specific claims are weak.

## `claims.json` schema (E0 output, /create reads this)

```json
{
  "topic": "<slug>",
  "generated": "<YYYY-MM-DD>",
  "freshness": "<YYYY-MM-DD>",
  "triangulation_score": 0.0,
  "refetch_pass_rate": 0.0,
  "ciber_passed": true,
  "verdict": "READY|PARTIAL|PARTIAL_QUICK|HOLD|FAIL",
  "source_count": 0,
  "claims": [
    {"id": "C1", "claim": "...", "sq": "sq1",
     "supporting": ["S1", "S3"], "independent_count": 2,
     "confidence": "high|medium-contested|medium|low",
     "support_class": "Supported|Partially Supported|Unsupported|Uncertain",
     "dissemination_score": 0.0,
     "contradicts": null,
     "contests": []}
  ],
  "unresolved_contradictions": [{"ids": ["C?", "C?"], "topic": "...", "description": "..."}],
  "coverage_gaps": ["..."],
  "sub_questions": [<from phase1>]
}
```

The `confidence`, `support_class`, and `dissemination_score` fields are defined in `source-discipline.md` and `citation-verification.md` — don't redefine here.

## Verdict — wixie's mapping over the vis criteria

The vis `research-pipeline.md` defines the verdict criteria. E0's mapping is identical; the `verdict` field in `claims.json` carries it forward to `/create` and to the metadata layer.

| Verdict | `/create` consumption |
|---|---|
| `READY` | Fold `support_class: Supported` + `confidence: high` claims directly into `<context>` |
| `PARTIAL` | Same, but surface `medium-contested` and `Partially Supported` claims in `<constraints>` |
| `PARTIAL_QUICK` | Consumable for time-sensitive lookups; never satisfies freshness-reuse (re-run on next ground-truth need) |
| `HOLD` | Do not ship; orchestrator re-dispatches the offending phase |
| `FAIL` | Regenerate `sources.jsonl` from a fresh Phase 2 |

**CIBER override on the verdict (Phase 6c).** A CIBER consistency failure on a `high`-confidence claim downgrades that claim to `medium-contested` AND forces the brief verdict to `PARTIAL` — even if every other gate passes (`τ ≥ 0.85`, `refetch_pass_rate ≥ 0.9`, all `verifier` violations empty). Rationale: a claim whose paraphrase splits its own source set is not READY-grade ground truth, regardless of how well the original phrasing traced.

Mapping precedence (highest wins):
1. `refetch_pass_rate < 0.7` → `FAIL` (Phase 6b hard fail)
2. Any `verifier.violations` non-empty → `HOLD`
3. `ciber_passed == false` (any consistency failure on a `high` claim) → `PARTIAL` (CIBER override)
4. `0.7 ≤ refetch_pass_rate < 0.9` → `PARTIAL` (Phase 6b flagged)
5. `τ < 0.85` OR unresolved contradictions present → `PARTIAL`
6. All gates pass AND `--depth full` → `READY`
7. `--depth quick` and all available gates pass → `PARTIAL_QUICK`

## Handoff to /create

`/create`'s Phase 2.7 reads `claims.json` directly:

1. Filter to `support_class = "Supported"` AND `confidence ∈ {high, medium}` → fold into `<context>` or sandwich-middle.
2. `support_class = "Partially Supported"` or `confidence = medium-contested` → surface in `<constraints>` with both positions when contested.
3. `verdict = PARTIAL` → add a one-line note listing uncovered SQs.

Metadata passed forward:
```json
"research_claims": "plugins/deep-research/state/briefs/<slug>/claims.json",
"research_freshness": "<YYYY-MM-DD>",
"triangulation_score": 0.0,
"refetch_pass_rate": 0.0,
"ciber_passed": true,
"verdict": "..."
```

Freshness rules:
- `verdict ∈ {READY, PARTIAL}` AND `freshness < 30 days` → reuse
- `verdict = PARTIAL_QUICK` → never reuse; regenerate at full depth
- Otherwise → regenerate

## Wixie-specific failure modes

(Generic research failure modes — F02, F11, F12, F13, F14 — live in vis modules.)

| Code | Signature | Counter |
|------|-----------|---------|
| F11.1 | Haiku fetcher schema-drift (non-canonical JSON shape) on round-3 dispatch | Orchestrator runs `wixie/shared/scripts/fetcher-normalize.py` on every fetcher return to coerce drift back to canonical |
| F11.2 | Phase 6c CIBER surfaces negation-supported on a `high`-confidence claim | Orchestrator demotes to `medium-contested`, bumps `dissemination_score`, forces brief verdict → PARTIAL (see "CIBER override on the verdict") |
| OP06 | Arxiv `/pdf/<id>` URL passed to WebFetch — returns binary | Fetcher Step 2 URL normalization rewrites `/pdf/<id>` → `/abs/<id>` before fetch |

Log occurrences to `state/precedent-log.md` per `@../vis/packages/core/conduct/precedent.md`.

## Wixie-specific anti-patterns

(Generic anti-patterns — round-1 stop, padding queries, skipping re-fetch, silent contradiction resolution — live in `research-pipeline.md` and `source-discipline.md`.)

- **Writing `report.md` from this skill.** Rendering is `/research-render`'s job — separation of concerns.
- **Regenerating when a fresh brief exists.** If `verdict ∈ {READY, PARTIAL}` and `freshness < 30 days`, reuse `claims.json` without re-running. Re-running burns tokens for no new signal.
- **Bypassing `fetcher-normalize.py`.** Haiku schema drift on round 3 is documented (F11.1); the normalizer is enforcement, the schema clauses in `fetcher.md` are documentation of intent.
