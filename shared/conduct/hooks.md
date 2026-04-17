# Hooks — Advisory-Only Rules

Audience: Claude. How to wire hooks without breaking a skill-invoked lifecycle. A product's root `CLAUDE.md` decides whether hooks are permitted; this module defines the contract when they are.

## The rule

**Hooks inform, they don't decide.** Any hook in the product must pass this test:

> If the hook were removed, would the system still function correctly?
> If no — the hook is load-bearing, not advisory. Reconsider the design.

Load-bearing hooks are an anti-pattern in skill-invoked systems; hooks that gate behavior smuggle control flow into the runtime.

## Injection over denial

When a hook has something useful to say, inject context — don't block.

| Situation | Blocking hook (bad) | Injecting hook (good) |
|-----------|---------------------|----------------------|
| Post-edit TS errors | Reject the Write | PostToolUse emits: *"3 TS errors at lines 42/78/103"* |
| Missing test coverage | Reject the commit | Pre-submit emits: *"New function `foo` has no test — add one?"* |
| Registry mismatch | Reject the skill | UserPromptSubmit emits: *"Target not in registry — verify before proceeding"* |

The agent reads the injected context and decides. The hook does not short-circuit the decision.

## Matcher specificity

Always scope hooks to the smallest relevant event.

```jsonc
// Good — scoped to specific tools
{ "matcher": "Bash", "hooks": [...] }
{ "matcher": "Write|Edit", "hooks": [...] }

// Bad — fires on everything
{ "hooks": [...] }
```

Omitting the matcher runs the hook on every event — on a long session, that's thousands of invocations for one that matters.

## Single-entry dispatcher

One hook script that routes, not N scripts triggered in parallel.

```
.claude/hooks/dispatch.sh
├── if event == "PostToolUse:Write"  → lint.sh
├── if event == "PostToolUse:Bash"   → audit.sh
└── if event == "UserPromptSubmit"   → brief.sh
```

Why: one place to enable/disable, one log to grep, no hook-order confusion, no parallel-hook races.

## Subagent-loop guard

`UserPromptSubmit` can trigger when the parent *or* a subagent submits. Without a guard, you can loop:

1. Parent prompts → hook triggers → hook spawns a subagent → subagent's first prompt is a UserPromptSubmit → hook triggers again → …

Guard with an environment marker:

```bash
if [[ -n "$CLAUDE_SUBAGENT" ]]; then
  # inside a subagent, skip the hook
  exit 0
fi
```

Or check the nesting level in the hook payload if the runtime exposes one.

## Fail-open for advisory hooks

If an advisory hook errors, it must not block the underlying action.

```bash
#!/bin/bash
set -uo pipefail   # note: no -e

notify_save "$@" || true   # never propagate failure
exit 0
```

An advisory hook that sometimes blocks is worse than no hook — it introduces intermittent, hard-to-reproduce failures.

## Performance budget

Hooks run synchronously. They add latency to every matched event.

| Event | Budget |
|-------|--------|
| UserPromptSubmit | < 200ms |
| PostToolUse (high-frequency) | < 100ms |
| PreToolUse (on every tool call) | < 50ms |
| Stop | < 500ms (user already waiting) |

If the work doesn't fit the budget, move it async — spawn a background process, don't block the runtime.

## Logging from hooks

Hooks should log to a file, not stdout. stdout goes into the conversation and pollutes context.

```bash
echo "[$(date -Is)] prompt saved: $prompt_path" >> .claude/logs/hooks.log
```

Log format: timestamp, event, relevant id. Keep entries one-line so they're greppable.

## Legitimate hook jobs

- **Deterministic observation.** Save every prompt to disk, emit a Slack notification, update a dashboard.
- **Environment injection.** PreToolUse for Bash that adds env vars the command needs.
- **Post-hoc enrichment.** PostToolUse that appends lint output as a system message.

If the job is observe-or-inject, use a hook. If it's deny-or-gate, use a skill or a permission.

## Anti-patterns

- **Blocking hook masquerading as advisory.** Exit non-zero to "warn" — in practice it rejects. Use exit 0 + injection.
- **Hook that writes to stdout.** Output shows up in the conversation; confusing and costly.
- **No matcher.** Fires on every event; unreadable logs, killed performance.
- **Multiple parallel hooks for the same event.** Order undefined, races possible.
- **Hook with side effects on the repo.** Auto-commits, auto-renames — the hook is now a collaborator, not a listener.
- **Subagent-triggered loops.** No guard, infinite recursion.
