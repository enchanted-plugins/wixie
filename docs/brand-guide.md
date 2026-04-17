# Enchanted Plugins Brand Guide

## Identity

**Tagline:** Algorithm-driven tools for AI-assisted development.

**Three pillars:**
1. **Algorithm-named engines** — every feature backed by formal math
2. **Managed agent networks** — Opus orchestrates, Sonnet executes, Haiku validates
3. **Self-learning systems** — engines improve with every session

## Naming Rules

1. Every plugin is named after a game entity
2. The metaphor must be immediately obvious (Allay collects, Reaper hunts threats)
3. One game per plugin — no repeats except Minecraft (max 2)
4. The name must be short (1-2 syllables preferred), pronounceable, and memorable
5. The game must be well-known (>1M copies sold or cultural impact)

## Plugin Structure Standard

Every @enchanted-plugins product is cloned from [`enchanted-plugins/schematic`](https://github.com/enchanted-plugins/schematic) — the canonical repo template. The tree below is the shape `schematic` ships. New siblings clone it, fill placeholders, and rename `plugins/example-subplugin/` before first commit.

Every @enchanted-plugins product follows this exact structure:

```
<product>/
├── .claude-plugin/marketplace.json       # name + owner.name + metadata + plugins[]
├── plugins/
│   └── <plugin-name>/
│       ├── .claude-plugin/plugin.json
│       ├── skills/<skill>/SKILL.md       # frontmatter: name, description, model, tools
│       ├── agents/<agent>.md             # frontmatter: model, context, allowed-tools
│       ├── commands/<command>.md          # slash commands
│       ├── hooks/hooks.json              # advisory-only lifecycle bindings
│       ├── state/.gitkeep                # per-plugin state, gitignored at runtime
│       └── README.md
├── shared/
│   ├── conduct/                          # 10 universal behavioral modules (@-loaded by CLAUDE.md)
│   ├── scripts/                          # plugin-specific Python (stdlib only)
│   ├── constants.sh                      # shell helpers: now_iso, ensure_dir, log
│   ├── metrics.sh                        # emit_metric, rotate_if_too_big
│   ├── sanitize.sh                       # sanitize_for_json, sanitize_path, sanitize_slug
│   └── <plugin-specific>                 # e.g. references/, patterns/, models-registry.json
├── tests/
│   ├── run-all.sh                        # iterates plugins/*/tests/
│   ├── shared/                           # cross-plugin test helpers
│   └── <plugin>/test-*.sh
├── docs/
│   ├── architecture/                     # auto-generated from plugin.json + hooks.json + SKILL.md
│   │   ├── generate.py                   # the generator — reads source-of-truth, writes below
│   │   ├── highlevel.mmd                 # system diagram
│   │   ├── hooks.mmd                     # hook lifecycle
│   │   ├── lifecycle.mmd                 # session flow
│   │   ├── dataflow.mmd                  # enchanted-mcp event flow
│   │   ├── index.html                    # dark-themed single-page explorer
│   │   └── README.md                     # "do not hand-edit, run generate.py"
│   ├── assets/                           # renderer toolchain (mermaid-cli + puppeteer + mathjax)
│   │   ├── apply-blueprint.js            # Mermaid SVG → blueprint background
│   │   ├── render-math.js                # LaTeX → SVG for mobile-readable README
│   │   ├── mermaid.config.json
│   │   ├── puppeteer.config.json
│   │   ├── package.json                  # devDeps only; node_modules + lockfile gitignored
│   │   └── math/                         # pre-rendered equation SVGs
│   ├── science/README.md                 # LaTeX formulas, named algorithms
│   ├── ecosystem.md                      # ecosystem map, data flow, algorithm distribution
│   ├── brand-guide.md                    # this file
│   ├── ROADMAP.md                        # phased development plan
│   └── org-profile-README.md             # GitHub org landing page source
├── configs/claude-code/README.md          # optional settings.json snippets
├── install.sh                             # pre-flight + clone to ~/.claude/plugins/
├── README.md                              # product selling page (10 required sections)
├── CONTRIBUTING.md
└── LICENSE                                # MIT, enchanted-plugins copyright
```

## README Standard

Every product README must include:

1. **Header:** "An @enchanted-plugins product — algorithm-driven, agent-managed, self-learning."
2. **Game reference:** explain the name's origin in the first paragraph
3. **Problem statement:** what pain point does this solve, with evidence
4. **Architecture diagram:** ASCII showing the plugin/agent/hook flow
5. **Named algorithms section:** key formulas in GitHub LaTeX (`$$...$$`)
6. **Install:** one-liner marketplace command
7. **Plugin table:** command, function, agent per plugin
8. **Comparison table:** vs competitors with honest feature comparison
9. **Lifecycle diagram:** where this product fits in the full ecosystem
10. **Contributing link**

## Algorithm Naming Convention

Every algorithm follows: `[Method] [Domain] [Action]`

Examples:
- Gauss Convergence Method (standard deviation minimization)
- Shannon Entropy Analysis (information-theoretic secret detection)
- Bayesian Trust Scoring (prior-posterior change risk assessment)
- Markov Drift Detection (hidden state transition recognition)

## Commit Message Standard

```
feat: <what was added>
fix: <what was fixed>
docs: <what was documented>
refactor: <what was restructured>
test: <what was tested>
```

One logical change per commit. Never batch unrelated changes.

## Agent Model Tiers

| Tier | Model | Role | When to use |
|------|-------|------|-------------|
| Orchestrator | Opus | Judgment, design, intent | Main skill that interacts with user |
| Executor | Sonnet | Script execution, analysis | Background convergence, deep review |
| Validator | Haiku | Pass/fail checks, file validation | Quick verification, format checks |

## Report Standard

Every product generates dark-themed single-page PDF reports via the `docs/architecture/` pipeline:
- Background: `#0d1117` · Surface: `#161b22` · Border: `#1e3a5f` · Accent: `#58a6ff`
- Agent-tier accents: Opus `#bc8cff` · Sonnet `#58a6ff` · Haiku muted
- Generated via `docs/architecture/generate.py` + `docs/assets/puppeteer.config.json` (Chrome headless)
- Content: score bars, technique pills, audit findings, verdict with next steps
- Never hand-edit the diagrams or HTML — regenerate via `python docs/architecture/generate.py`
