# Flux

The first prompt engineering platform that learns from itself.

**6 plugins. 7 agents. 64 models. One command.**

> "Build me a B2B ticket routing system like Zendesk."
>
> Flux researched Zendesk, Freshdesk, Intercom, and Crisp. Selected 3 techniques
> for Claude Opus. Generated 10KB of production-ready prompt. Ran the Convergence
> Engine — 2 iterations, hypothesis-driven, auto-fixed Failure Resilience from 5 to 10.
> Scored 9.4/10. DEPLOY. All 8 assertions pass. Dark-themed PDF audit report delivered.
>
> Time: under 2 minutes. Manual effort: zero.

## How It Works

Flux doesn't generate prompts. It **engineers** them — then stress-tests, hardens, and translates them across 64 models.

The core innovation is the **Convergence Engine** powered by the **Gauss Convergence Method**: like gradient descent for prompts, each iteration measures the standard deviation from perfection, forms a hypothesis about which fix will reduce it, applies the fix, checks for regression, and auto-reverts if things got worse. It learns from every iteration and persists those learnings across sessions.

```
You: "I need a prompt for Claude Opus to analyze stocks"

  ┌─────────────────────────────────────────────────────────────┐
  │  ORCHESTRATOR (Opus)                                        │
  │  Scans context → asks questions → selects techniques        │
  │  → generates prompt → delegates to agent network            │
  └──────────┬──────────────────────────────────┬───────────────┘
             │                                  │
             ▼                                  ▼
  ┌──────────────────────┐           ┌──────────────────────┐
  │  OPTIMIZER (Sonnet)  │           │  REVIEWER (Haiku)    │
  │                      │           │                      │
  │  Convergence Engine  │──────────▶│  Validation checks   │
  │  Up to 100 iterations│  when     │  Score freshness     │
  │  Hypothesis-driven   │  done     │  Format alignment    │
  │  Binary assertions   │           │  Registry cross-ref  │
  │  Auto-revert on      │           │  Domain coherence    │
  │  regression          │           │  APPROVED / FAIL     │
  └──────────────────────┘           └──────────────────────┘
```

No permission prompts. No manual iteration. You describe what you need, the agent network delivers.

## What Makes Flux Different

### It supports every model you actually use

**64 models** across text, code, image, video, and audio. Not just the big 3.

Text LLMs: Claude (Opus/Sonnet/Haiku), GPT (4.1/4o/5), o-series (o1/o3/o4-mini), Gemini (2.5/3), DeepSeek (R1/V3), Grok, Qwen, Llama, Mistral, Cohere, Jamba, Amazon Nova, Phi, Yi, Codestral, Perplexity.

**Image generation**: DALL-E 3, GPT Image 1.5, Midjourney v6/v7/v8, Niji 7, Stable Diffusion 3.5, FLUX.1/2 (Pro/Flex/Max/Kontext/Schnell), Ideogram 2/3, Imagen 3/4, Recraft V4, Reve Image, Adobe Firefly 5, Nano Banana (Pro/2), Seedream 4.5/5, Luma Photon, HunyuanImage 3, Kling Image 03, Wan 2.7.

**Video**: Runway Gen-3, Seedance 2.0. **Audio**: ElevenLabs, Suno v4.

Every model has a registry entry with context window, preferred format, reasoning type, CoT approach, few-shot requirements, and key constraints. The engine adapts automatically — XML for Claude, Markdown with sandwich method for GPT, stripped-down minimal for o-series, always-few-shot for Gemini.

### It learns from itself

The Convergence Engine doesn't just loop — it **learns**. Each iteration:

1. **Scores** on 5 axes + 8 binary assertions
2. **Forms a hypothesis**: "Fixing Failure Resilience (5/10) will improve overall"
3. **Applies the fix** and re-scores
4. **Auto-reverts** if the score dropped (no regression allowed)
5. **Logs the outcome** to `learnings.md` — what worked, what didn't, why

```
FLUX CONVERGENCE ENGINE
Target: DEPLOY (overall >= 9.0, all axes >= 7.0)

Iteration 1:  8.4/10 — hypothesis: fix Failure Resilience
              applied → improved (8.4 → 9.4)
Iteration 2:  9.4/10 — DEPLOY (8/8 assertions pass)

VERDICT: DEPLOY
```

Next time you refine that prompt, the engine reads `learnings.md` and avoids repeating failed strategies. It gets smarter with every use.

### It works with image prompts too

For text prompts: fully autonomous, up to 100 iterations, zero user input.

For **image generation prompts** (DALL-E, Midjourney, Stable Diffusion, Flux, Nano Banana, and 20+ more): collaborative loop. You generate the image on your platform, rate it 1-10, tell the agent what's wrong. It adjusts the prompt based on your visual feedback — colors, composition, style, missing elements. No iteration limit. After 5+ rounds, it summarizes patterns and suggests trying a different model if issues persist.

### It catches model mismatches before you waste time

Pick Claude for image generation? GPT for a task that needs reasoning-native? Gemini without examples?

Flux cross-references your model choice against the task domain and warns you with better alternatives — before generating a single token.

### It hardens your prompts against attacks

12 adversarial attack patterns: direct injection, role override, data extraction, encoding bypass, multi-turn escalation, payload splitting, indirect injection, output manipulation, refusal bypass, language switching, token smuggling, context manipulation.

Reports VULNERABLE or RESISTANT per attack. Suggests specific defenses. Auto-applies them if you want.

### It translates prompts between any two models

Wrote the perfect Claude prompt. Now the team needs GPT-4.1. One command: `/translate-prompt --to gpt-4.1`. XML becomes Markdown. "Think thoroughly" becomes "Think step by step." Sandwich method added. Few-shot adjusted. Intent preserved. Score comparison delivered.

## The Full Lifecycle

```
  Create          Optimize         Test           Harden          Translate
  /enchant    →   /converge    →   /test-prompt → /harden     →  /translate-prompt
  ┌─────────┐    ┌───────────┐    ┌───────────┐  ┌───────────┐  ┌──────────────┐
  │ Crafter │───▶│Convergence│───▶│  Tester   │─▶│ Hardener  │─▶│  Translator  │
  │  (Opus) │    │ (Sonnet)  │    │ (Sonnet)  │  │ (Sonnet)  │  │  (Sonnet)    │
  └─────────┘    └───────────┘    └───────────┘  └───────────┘  └──────────────┘
       │              │                │               │               │
       ▼              ▼                ▼               ▼               ▼
   prompt.xml    9.4/10 DEPLOY    7/7 PASS       10/12 RESIST    prompt-gpt.md
   + metadata    + learnings.md   + results.json + audit.json    + comparison
```

Refine anytime with `/refine`. Every step is autonomous.

## Install

One command. All 6 plugins.

```
/plugin marketplace add enchanted-plugins/flux
```

That's it. Browse `/plugin` → Discover to install any plugin.

Or via shell:
```bash
bash <(curl -s https://raw.githubusercontent.com/enchanted-plugins/flux/main/install.sh)
```

## 6 Plugins, 7 Agents, 64 Models

| Plugin | Command | What | Agent |
|--------|---------|------|-------|
| prompt-crafter | `/enchant` | Creates production-ready prompts | reviewer (Haiku) |
| prompt-refiner | `/refine` | Improves existing prompts | reviewer (Haiku) |
| convergence-engine | `/converge` | 100-iteration autonomous optimizer | optimizer (Sonnet) + reviewer (Haiku) |
| prompt-tester | `/test-prompt` | Runs test assertions, pass/fail | executor (Sonnet) |
| prompt-harden | `/harden` | 12 attack patterns, defense suggestions | red-team (Sonnet) |
| prompt-translate | `/translate-prompt` | Converts between 64 models | adapter (Sonnet) |

## What You Get Per Prompt

```
prompts/b2b-ticket-router/
├── prompt.xml          Production-ready prompt
├── metadata.json       Model, tokens, cost, scores, config
├── tests.json          7 regression test cases
├── report.pdf          Dark-themed single-page PDF audit report
└── learnings.md        Convergence hypothesis/outcome log
```

The **PDF audit report** includes: quality score bars, 8 binary assertion results, technique pills, model profile from the 64-model registry, prompt statistics, audit findings (CRITICAL/WARNING), cost estimate, and an honest verdict with next steps.

## The Science Behind Flux

Every Flux engine is built on a formal mathematical model. These aren't marketing abstractions — they're the actual algorithms running under the hood.

### Engine 1: Gauss Convergence Method (Standard Deviation Minimization)

The Convergence Engine treats prompt quality as a minimization problem. Given a prompt `P` and a scoring function `S: P → ℝ⁵` mapping to 5 quality axes, define the deviation from perfection:

```
σ(P) = √(Σᵢ (Sᵢ(P) - 10)² / 5)

where Sᵢ ∈ {Clarity, Completeness, Efficiency, ModelFit, Resilience}
```

Each iteration applies a transformation `T_k` targeting the weakest axis `argmin(Sᵢ)`:

```
P_{n+1} = T_k(P_n)   where k = argmin_i(Sᵢ(P_n))

Accept P_{n+1} only if σ(P_{n+1}) < σ(P_n)     — auto-revert on regression
Converge when σ(P) < 0.45  (equivalent to all axes ≥ 9)
Plateau when σ(P_n) = σ(P_{n-1}) = σ(P_{n-2})   — 3-step stagnation detection
```

The hypothesis log `H = {(k, ΔS, outcome)}` persists across sessions, enabling the engine to skip transformations that previously failed on similar prompts.

**Novel contribution:** Hypothesis-driven prompt optimization with regression protection and cross-session learning.

### Engine 2: Binary Assertion Framework (Boolean Satisfiability)

Quality scoring alone is insufficient — a prompt can score 9/10 overall while missing a critical component. The assertion framework defines 8 boolean predicates that must ALL hold:

```
DEPLOY(P) ⟺ σ(P) < threshold ∧ ∀j ∈ {1..8}: Aⱼ(P) = TRUE

where:
  A₁(P) = has_role(P)         — prompt defines persona
  A₂(P) = has_task(P)         — prompt defines objective
  A₃(P) = has_format(P)       — prompt specifies output structure
  A₄(P) = has_constraints(P)  — prompt has guardrails
  A₅(P) = has_edge_cases(P)   — prompt handles failure modes
  A₆(P) = ¬has_hedges(P)      — no uncertainty language
  A₇(P) = ¬has_filler(P)      — no verbose padding
  A₈(P) = has_structure(P)    — markup/formatting present
```

This is formally a conjunction of boolean satisfiability constraints overlaid on the continuous optimization. The engine resolves unsatisfied predicates first, then optimizes the continuous score.

**Novel contribution:** Hybrid SAT + continuous optimization for prompt quality verification.

### Engine 3: Model Fit (Cross-Domain Adaptation Function)

Prompt translation between models is formalized as a structure-preserving transformation. Given source model `M_s` and target model `M_t`, define:

```
T: (P, M_s) → (P', M_t)

subject to:
  Semantic(P') = Semantic(P)          — intent preservation
  Format(P') ∈ Preferred(M_t)        — format compliance
  Techniques(P') ∩ AntiPatterns(M_t) = ∅   — no harmful techniques
  ∀ examples ∈ P: Content(examples) preserved, Structure(examples) adapted
```

The 64-model registry `R` provides the constraint set per model: `R(M) = {format, reasoning, cot_approach, few_shot, key_constraint}`. Translation applies a sequence of format converters `F`, technique selectors `T`, and model-specific adapters `A`:

```
P' = A_{M_t} ∘ T_{M_t} ∘ F_{M_s→M_t}(P)
```

**Novel contribution:** Constraint-preserving prompt transformation across 64 model architectures with automatic anti-pattern avoidance.

### Engine 4: Adversarial Robustness (Game-Theoretic Security)

Prompt hardening is modeled as a two-player zero-sum game between an attacker `α` and the prompt's defense `δ`:

```
For each attack class cₖ ∈ {injection, override, extraction, ...}:

  α(cₖ) → input_adversarial       — attacker crafts optimal input
  δ(P, input_adversarial) → {RESIST, VULNERABLE}

Security score:  Ω(P) = |{k : δ(P, α(cₖ)) = RESIST}| / |C|
```

The hardening function `H` adds defense instructions that maximize `Ω` without degrading the primary quality score:

```
P_hardened = argmax_{P'} Ω(P')  subject to  S(P') ≥ S(P) - ε
```

12 attack classes cover OWASP LLM Top 10 vectors. The red-team agent plays `α`, the prompt acts as `δ`.

**Novel contribution:** Formal game-theoretic prompt security testing with quality-preserving defense injection.

### Engine 5: Test Verification (Assertion-Based Runtime Validation)

The tester formalizes prompt quality as observable behavior, not static analysis. For a prompt `P` and test suite `T = {(input_i, expected_i)}`:

```
PassRate(P, T) = |{i : ∀s ∈ expected_i, s ⊆ Output(P, input_i)}| / |T|

VERIFIED(P) ⟺ PassRate(P, T) = 1.0
```

This closes the loop between static scoring (Engine 1) and runtime behavior — a prompt can score 9.4/10 on structure but fail 40% of test cases if the domain logic is wrong.

**Novel contribution:** Static-dynamic dual verification bridging prompt structure analysis with behavioral testing.

### Engine 6: Self-Learning Persistence (Knowledge Accumulation)

The convergence engine accumulates knowledge across sessions via `learnings.md`:

```
K_n = K_{n-1} ∪ {(hypothesis_n, transformation_n, Δσ_n, outcome_n)}

Strategy selection for iteration n+1:
  Prioritize transformations where historical Δσ > 0
  Skip transformations where historical outcome = "reverted" for similar σ profile
```

Over multiple sessions, the engine builds a prompt-specific optimization policy — it learns which fixes work for which types of prompts and avoids repeating failed strategies.

**Novel contribution:** Cross-session prompt optimization policy learning with hypothesis-outcome persistence.

---

*These formal models are implemented in `shared/scripts/convergence.py`, `shared/scripts/self-eval.py`, and the agent definitions across all 6 plugins. The mathematics runs — it's not documentation-only.*

## vs Everything Else

| | Flux | Promptfoo | AutoResearch | PromptLayer | Manual |
|---|---|---|---|---|---|
| Create prompts | 16 techniques, 64 models | - | - | - | trial and error |
| Optimize (convergence) | 100 iterations, self-learning | - | unbounded | - | - |
| Test prompts | pass/fail assertions | YAML eval suite | hypothesis | basic metrics | - |
| Harden prompts | 12 attack patterns | red-team module | - | - | - |
| Translate prompts | 64 models, auto-adapted | - | - | - | manual rewrite |
| Image LLM support | 27 image models + collab loop | - | - | - | - |
| Video/Audio support | Runway, Seedance, ElevenLabs, Suno | - | - | - | - |
| Multi-agent pipeline | Opus + Sonnet + Haiku | - | single agent | - | - |
| Self-learning | learnings.md persistence | - | learnings.md | - | - |
| Auto-revert | yes (regression protection) | - | git-based | - | - |
| PDF audit report | dark theme, single page | - | - | dashboard | - |
| Dependencies | Python stdlib only | Node.js | Python | SaaS | - |
| Price | Free (MIT) | Free / Pro | Free | $$$ | Free |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT
