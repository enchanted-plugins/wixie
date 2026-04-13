# prompt-crafter

**Creates production-ready prompts. Zero manual iteration.**

Give it a task description. It scans your project context, asks targeted questions, selects from 16 techniques, adapts format to 64 models, then runs the Convergence Engine autonomously until the prompt hits DEPLOY quality.

## Pipeline

```
User describes task
  → Phase 1: Context Scan (silent — reads CLAUDE.md, .cursorrules)
  → Phase 2: Interactive Profiling (3-8 targeted questions)
  → Phase 2.5: Model Fit Check (warns if wrong model for task)
  → Phase 3: Generation (technique selection + prompt generation)
  → Phase 4: Multi-Agent Pipeline
      → Convergence Agent (Opus, background, up to 100 iterations)
      → Reviewer Agent (Opus, validates against registry)
      → Save: prompt + metadata + tests + report.pdf
```

## Components

| Type | Name | What it does |
|------|------|-------------|
| Skill | prompt-creator | Main workflow — phases 1-4 |
| Skill | prompt-reviewer | Internal validator (not user-invocable) |
| Agent | convergence | Runs convergence.py in background (Opus) |
| Agent | reviewer | Validates folder against registry (Opus) |
| Hook | PostToolUse | Auto-triggers on prompt file save |

## Triggers

`/create`, "I need a prompt for...", "build me a prompt", "write a system prompt"

## Output

```
prompts/<name>/
├── prompt.<format>     Production-ready prompt
├── metadata.json       Model, tokens, cost, scores, config
├── tests.json          3-5 regression test cases
└── report.pdf          Dark-themed single-page audit report
```
