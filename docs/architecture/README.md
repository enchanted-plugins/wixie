# Wixie Architecture

> Auto-generated from codebase by `generate.py`. Run `python docs/architecture/generate.py` to regenerate.

## Interactive Explorer

Open [index.html](index.html) in a browser to explore the architecture interactively with tabbed Mermaid diagrams and plugin component cards.

## At a Glance

**6 plugins. 7 agents. 7 skills. 6 engines (F1–F6). 5-axis scoring. 8 SAT assertions. 16 tests.**

## Diagrams

| Diagram | File | Description |
|---------|------|-------------|
| High Level | [highlevel.mmd](highlevel.mmd) | 6 plugins on top of Opus/Sonnet/Haiku agent tiers |
| Session Lifecycle | [lifecycle.mmd](lifecycle.mmd) | Craft → Refine → Converge → Test → Harden → Translate |
| Data Flow | [dataflow.mmd](dataflow.mmd) | Prompt artifacts (`prompt.*`, `metadata.json`, `learnings.md`) across skills |
| Hook Bindings | [hooks.mmd](hooks.mmd) | Single advisory hook: PostToolUse on `prompts/*/prompt.*` saves |

## Plugin Summary

| Plugin | Stage | Agent tier | Skill | Artifact |
|--------|-------|-----------|-------|----------|
| prompt-crafter | Craft | Opus + Haiku | `/create` | `prompt.*`, `metadata.json` |
| prompt-refiner | Refine | Opus + Haiku | `/refine` | `prompt.*` (v++), `metadata.json` |
| convergence-engine | Converge | Sonnet + Haiku | `/converge` | `learnings.md`, updated scores |
| prompt-tester | Test | Sonnet | `/test-prompt` | `tests.json`, pass/fail |
| prompt-harden | Harden | Sonnet red-team | `/harden` | `audit.json` (12 attacks) |
| prompt-translate | Translate | Sonnet adapter | `/translate-prompt --to <model>` | `prompt.<new>`, score comparison |

## Agent Tiers

| Tier | Model | Used for |
|------|-------|----------|
| Orchestrator | Opus | Judgment, intent, technique selection (crafter, refiner) |
| Executor | Sonnet | Convergence loop, adversarial attacks, format conversion, test execution |
| Validator | Haiku | Quality gate — file completeness, metadata consistency, score freshness |

## Engines (F1–F6)

| Code | Name | Where |
|------|------|-------|
| F1 | Gauss Convergence | `shared/scripts/convergence.py` |
| F2 | Boolean Satisfiability Overlay | `run_assertions()` in `convergence.py` |
| F3 | Cross-Domain Adaptation | `prompt-translate` adapter |
| F4 | Adversarial Robustness | `prompt-harden` red-team loop |
| F5 | Static-Dynamic Dual Verification | tester + reviewer pair |
| F6 | Gauss Accumulation (self-learning) | `learnings.md` aggregation |

Full derivations: [docs/science/README.md](../science/README.md).

## DEPLOY Bar

| Verdict | Criteria |
|---------|----------|
| DEPLOY | σ < 0.45 **and** overall ≥ 9.0 **and** all 5 axes ≥ 7.0 **and** 8/8 SAT assertions pass |
| HOLD | σ ≥ 0.45 or any axis < 7.0 |
| FAIL | Reviewer flags registry mismatch / stale technique / format drift |

σ = standard deviation of 5 axis scores from 10. Axes: clarity, specificity, structure, constraints, coverage.

## Execution Order

```
1. /create            → prompt-crafter (Opus) drafts prompt.* + metadata.json
2. /refine            → prompt-refiner (Opus) increments version, updates metadata
3. PostToolUse save   → advisory hook: "convergence engine will optimize automatically"
4. /converge          → convergence-engine (Sonnet) runs Gauss loop, appends learnings.md
5. /test-prompt       → prompt-tester (Sonnet) runs regression cases from tests.json
6. /harden            → prompt-harden (Sonnet) runs 12 adversarial attacks, emits audit.json
7. /translate-prompt  → prompt-translate (Sonnet) retargets format (Claude/GPT/o-series/Gemini)
```

## Artifacts per Prompt

```
prompts/<name>/
├── prompt.<ext>       production prompt, format matches target model
├── metadata.json      model, tokens, cost, 5-axis scores, 8 assertions, version
├── tests.json         regression test cases (≥ 3, ≥ 1 edge-case)
├── report.pdf         dark-themed single-page audit (final only)
└── learnings.md       F6 hypothesis/outcome log — persists across sessions
```

## Test Coverage

16 tests across all plugins + shared utilities:

```
tests/
├── convergence-engine/  Gauss loop, no-regression, accumulation
├── prompt-crafter/      technique selection, metadata schema
├── prompt-refiner/      version increment, diff generation
├── prompt-tester/       fixture execution, pass/fail routing
├── prompt-harden/       12-attack audit, red-team coverage
├── prompt-translate/    format conversion (XML ↔ Markdown ↔ minimal ↔ few-shot)
└── run-all.sh           Master runner
```
