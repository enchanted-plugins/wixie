# The Science Behind Enchanted Plugins

Formal mathematical models powering every engine in the @enchanted-plugins ecosystem.

These aren't abstractions. Every formula maps to running code.

---

## Wixie: Prompt Engineering

### F1. Gauss Convergence Method

**Problem:** Given a prompt P, minimize its deviation from ideal quality across 5 dimensions.

<p align="center"><img src="../assets/math/gauss-sigma.svg" alt="sigma(P) = sqrt( sum_{i=1..5} (S_i(P) - 10)^2 / 5 )"></p>

At each iteration n, select transformation targeting the weakest axis:

<p align="center"><img src="../assets/math/sci-argmin-only.svg" alt="k* = argmin_i S_i(P_n)"></p>

<p align="center"><img src="../assets/math/sci-transform-only.svg" alt="P_{n+1} = T_{k*}(P_n)"></p>

**Regression protection:**

<p align="center"><img src="../assets/math/sci-accept.svg" alt="Accept P_{n+1} iff sigma(P_{n+1}) < sigma(P_n)"></p>

**Convergence:**

<p align="center"><img src="../assets/math/sci-convergence.svg" alt="DEPLOY: sigma < 0.45 | PLATEAU: three equal sigma | MAX: n >= 100"></p>

**Knowledge accumulation:**

<p align="center"><img src="../assets/math/accumulation.svg" alt="K_n = K_{n-1} ∪ { (k*, Δσ, outcome) }"></p>

**Implementation:** `shared/scripts/convergence.py`

---

### F2. Boolean Satisfiability Overlay

**Problem:** Continuous scoring can miss categorical failures.

Define 8 boolean predicates A_j mapping a prompt to TRUE or FALSE:

<p align="center"><img src="../assets/math/sat-deploy.svg" alt="DEPLOY(P) iff sigma(P) < tau AND all 8 A_j(P) hold"></p>

| j | Predicate | Check |
|-----|-----------|-------|
| 1 | has role | Prompt defines persona |
| 2 | has task | Prompt defines objective |
| 3 | has format | Specifies output structure |
| 4 | has constraints | Has guardrails |
| 5 | has edge cases | Handles failure modes |
| 6 | no hedges | No uncertainty language |
| 7 | no filler | No verbose padding |
| 8 | has structure | Markup present |

**Implementation:** `run_assertions()` in `shared/scripts/convergence.py`

---

### F3. Cross-Domain Adaptation

**Problem:** Transform a prompt for model M_s into equivalent quality for M_t.

<p align="center"><img src="../assets/math/adapt-signature.svg" alt="T : (P, M_s) -> (P', M_t)"></p>

<p align="center"><img src="../assets/math/adapt-constraints.svg" alt="Semantic(P') = Semantic(P) AND Techniques(P') ∩ AntiPatterns(M_t) = empty"></p>

Translation applies a composition:

<p align="center"><img src="../assets/math/sci-adapt-composition.svg" alt="P' = A_{M_t} ∘ T_{M_t} ∘ F_{M_s -> M_t}(P)"></p>

The 64-model registry provides per-model constraints: format, reasoning type, CoT approach, few-shot requirement, key constraint.

**Implementation:** `plugins/prompt-translate/skills/translate/SKILL.md`

---

### F4. Adversarial Robustness

**Problem:** Determine if a prompt resists adversarial inputs.

<p align="center"><img src="../assets/math/robust-omega.svg" alt="Omega(P) = | { k : delta(P, alpha(c_k)) = RESIST } | / |C|"></p>

Hardening maximizes security without degrading quality:

<p align="center"><img src="../assets/math/robust-hardened.svg" alt="P_hardened = argmax_{P'} Omega(P') subject to S(P') >= S(P) - epsilon"></p>

12 attack classes cover OWASP LLM Top 10 vectors.

**Implementation:** `plugins/prompt-harden/skills/harden/SKILL.md`

---

### F5. Static-Dynamic Dual Verification

**Problem:** Static analysis and dynamic behavior can diverge.

<p align="center"><img src="../assets/math/verified.svg" alt="VERIFIED(P) iff sigma(P) < tau AND PassRate(P, T) = 1.0"></p>

<p align="center"><img src="../assets/math/sci-passrate.svg" alt="PassRate(P, T) = | { i : for all s in E_i, s ⊆ Output(P, x_i) } | / |T|"></p>

**Implementation:** `plugins/prompt-tester/skills/test-runner/SKILL.md`

---

## Fae: Context Health

### A1. Hidden Markov Drift Detection

**Problem:** Detect unproductive loops without false positives.

Hidden states: PRODUCTIVE, READ LOOP, EDIT REVERT, TEST FAIL

<p align="center"><img src="../assets/math/fae-readloop.svg" alt="P(read loop) = 1 if count(read(f, h)) >= 3 AND no write(f)"></p>

<p align="center"><img src="../assets/math/fae-editrevert.svg" alt="P(edit revert) = 1 if hash of write_n(f) equals hash of write_{n-2}(f)"></p>

<p align="center"><img src="../assets/math/fae-testfail.svg" alt="P(test fail) = 1 if count of bash commands with non-zero exit >= 3"></p>

Cooldown:

<p align="center"><img src="../assets/math/fae-alert.svg" alt="Alert(t) = 1 iff P(drift) = 1 AND t - t_last > tau"></p>

**Implementation:** `plugins/context-guard/hooks/post-tool-use/detect-drift.sh`

---

### A2. Linear Runway Forecasting

**Problem:** Predict turns remaining before compaction.

<p align="center"><img src="../assets/math/fae-forecast.svg" alt="mu_hat = mean of tokens; runway = floor(remaining / mu_hat)"></p>

<p align="center"><img src="../assets/math/fae-ci.svg" alt="CI = t_{alpha/2} · s / sqrt(N)"></p>

| Runway | Action |
|--------|--------|
| &gt; 20 | Silent |
| 10–20 | Suggest checkpoint |
| ≤ 10 | Warning |
| ≤ 3 | Critical |

**Implementation:** `plugins/context-guard/skills/token-awareness/SKILL.md`

---

### A3. Information-Theoretic Compression

**Problem:** Reduce token consumption while preserving semantic content.

<p align="center"><img src="../assets/math/fae-compression.svg" alt="O -> O' subject to H(O') >= theta · H(O) AND |O'| < |O|"></p>

| Content | θ | Compression |
|---------|-----|-------------|
| Code | 1.0 | Lossless |
| Tests | 0.7 | Pass/fail + first error |
| Logs | 0.3 | Summary only |

<p align="center"><img src="../assets/math/fae-cr.svg" alt="CR(O) = 1 - |O'| / |O|"></p>

**Implementation:** `plugins/token-saver/hooks/pre-tool-use/compress-bash.sh`

---

### A4. Atomic State Serialization

**Problem:** Persist session state to survive compaction.

<p align="center"><img src="../assets/math/fae-checkpoint-size.svg" alt="|Checkpoint(t)| <= 50 KB"></p>

<p align="center"><img src="../assets/math/fae-atomic.svg" alt="write(f.tmp) -> validate(f.tmp) -> rename(f.tmp, f)"></p>

Locking: `acquire = mkdir(lock)` (atomic on all filesystems)

**Implementation:** `plugins/state-keeper/hooks/pre-compact/save-checkpoint.sh`

---

### A5. Content-Addressable Deduplication

**Problem:** Prevent re-reading unchanged files.

<p align="center"><img src="../assets/math/fae-sha.svg" alt="h_t = SHA256(content(f, t))"></p>

<p align="center"><img src="../assets/math/fae-decision.svg" alt="Decision(f, t) = BLOCK if cache hash matches; ALLOW if hash differs; ALLOW if cache entry older than TTL"></p>

**Implementation:** `plugins/token-saver/hooks/pre-tool-use/block-duplicates.sh`

---

*Every formula maps to executable code in the enchanted-plugins ecosystem. The math runs.*
