# Enchanted Plugins Ecosystem Map

## The Five Questions

Every developer asks these during an AI-assisted session. Each question maps to a plugin.

```
┌──────────────────────────────────────────────────────────┐
│                   Developer Session                       │
│                                                          │
│   "What did I say?"        → Wixie     (prompts)          │
│   "What did I spend?"      → Fae    (tokens)           │
│   "What just happened?"    → Raven   (changes)          │
│   "Is it safe?"            → Hydra   (security)         │
│   "What did it cost?"      → Pech     (spend)            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Plugin Ecosystem (9 games, Hollow Knight shared by Raven + Sylph)

Shipped today: Wixie, Fae, Raven, Hydra, Sylph. Planned: Pech, Athena, Crucible, Assembler, + 11 more in Phase 3–4.

```
                          ┌─────────────────┐
                          │  ENCHANTED MCP   │
                          │  (unified layer) │
                          └────────┬────────┘
                                   │
    ┌──────────┬──────────┬────────┼────────┬──────────┬──────────┐
    │          │          │        │        │          │          │
┌───▼────┐ ┌──▼───┐ ┌────▼────┐ ┌─▼────┐ ┌─▼──────┐ ┌─▼────┐ ┌───▼──────┐
│  Wixie  │ │Fae │ │ Raven  │ │Hydra│ │ Sylph │ │ Pech │ │  + Phase │
│ prompt │ │token │ │ change  │ │sec-  │ │ git    │ │ cost │ │   3-4    │
│ craft  │ │health│ │ trust   │ │urity │ │ flow   │ │track │ │ plugins  │
│  v3.0  │ │ v2.0 │ │  v1.0   │ │ v1.0 │ │ v0.0.1 │ │ n/a  │ │          │
└────────┘ └──────┘ └─────────┘ └──────┘ └────────┘ └──────┘ └──────────┘
 Minecraft  Minecraft  Hollow    Subnautica Hollow   Animal   Hades, Terraria,
 enchant.    fae     Knight               Knight   Crossing Factorio, ...

  Shipped     Shipped     Shipped    Shipped  Shipped   Planned    Planned
```

## Data Flow Between Plugins

```
Session Start
     │
     ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Hydra  │───▶│  Wixie   │───▶│  Fae  │
│ scans   │    │ crafts  │    │ tracks  │
│ configs │    │ prompt  │    │ tokens  │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     │         ┌────▼────┐         │
     │         │ Raven  │         │
     │         │ watches │         │
     │         │ changes │         │
     │         └────┬────┘         │
     │              │              │
     │    ┌─────────▼─────────┐    │
     └───▶│     Pech          │◀───┘
           │  tallies costs   │
           └──────────────────┘
```

## Algorithm Distribution

```
Total: 32 named algorithms across 9 products (5 shipped + 4 planned)

Shipped:
  Wixie   (6):   Gauss ─── SAT ─── Game Theory ─── Adaptation ─── Verification ─── Accumulation
  Fae  (5):   Markov ─── Runway ─── Shannon ─── Atomic ─── Dedup
  Raven (6):   Bayesian Trust ─── Semantic Diff ─── Info-Gain ─── Continuity ─── Adversarial ─── Learning
  Hydra (8):   Aho-Corasick ─── Entropy ─── OWASP ─── Action ─── Config ─── Phantom ─── Overflow ─── Threat
  Sylph (5):   Myers-Diff ─── Jaccard-Cosine ─── Workflow Classifier ─── Path-History ─── Gauss Learning (W5)

Planned:
  Pech      (2): Exponential Smoothing ─── Budget Boundary
  Athena    (2): AST Diff ─── Decision Trees
  Crucible  (1): Genetic Mutation
  Assembler (1): Critical Path DAG
```

## Hook Lifecycle Coverage

```
SessionStart  ──▶  Hydra (config-shield: scan for repo-level attacks)
              ──▶  Sylph (capability-memory: provider registry, GitLab probe)

PreToolUse    ──▶  Fae  (token-saver: compress output, block dupes)
              ──▶  Hydra (action-guard: block dangerous commands)
              ──▶  Sylph (sylph-gate: destructive-op decision gate)

PostToolUse   ──▶  Fae  (context-guard: drift detection, runway)
              ──▶  Raven (change-tracker: semantic diff, trust scoring)
              ──▶  Hydra (secret-scanner, vuln-detector, audit-trail)
              ──▶  Sylph (boundary-segmenter: task-boundary clustering)

PreCompact    ──▶  Fae  (state-keeper: checkpoint before compaction)
              ──▶  Raven (session-memory: save continuity graph)
              ──▶  Sylph (sylph-learning: persist developer preferences)
```

## Game Origin Reference

| Game | Plugin | Why this game fits |
|------|--------|-------------------|
| Minecraft | Wixie, Fae | Crafting, enchanting, and collecting — the foundation of building something from nothing |
| Hollow Knight | Raven | A game about exploration where every area hides secrets you must carefully observe to survive |
| Subnautica | Hydra | A game where the ocean is beautiful but the darkness hides creatures that hunt by sound — you're never truly safe |
| Animal Crossing | Pech | A game where every transaction is tracked, every loan is remembered, and the economy is always watching |
| Hades | Athena | A game where gods judge your performance and reward excellence with boons — quality is earned |
| Terraria | Crucible | A game where you forge items in increasingly extreme conditions to prove their worth |
| Factorio | Assembler | A game that IS automation — every machine connects to the next in an optimized pipeline |
| Hollow Knight | Sylph | Sylphs are Raven's ancestral kin — silk-spinners who weave threads into coherent patterns. Branches are threads; merges stitch them into a coherent history. |

## Infrastructure

Beyond the plugins themselves, the ecosystem has one meta-artifact:

| Repo | Role |
|------|------|
| [`enchanted-plugins/schematic`](https://github.com/enchanted-plugins/schematic) | Canonical repo template. Every new sibling is cloned from here. Ships the invariant tree: `.claude-plugin/`, `CLAUDE.md` (8-section canonical shape), 10 `shared/conduct/*.md` behavioral modules, `docs/architecture/` auto-generation pipeline, `plugins/example-subplugin/` skeleton, renderer toolchain, tests scaffold. The template itself is never installed — it exists to be cloned. |

The architectural contract for the template is defined in [brand-guide.md § Plugin Structure Standard](brand-guide.md#plugin-structure-standard).
