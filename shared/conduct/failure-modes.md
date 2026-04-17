# Failure Modes — Named Taxonomy

Audience: Claude. A controlled vocabulary for failure-log entries so accumulation across sessions can compound. Free-text learning notes don't compound; tagged ones do.

## Why a taxonomy

Accumulation only learns if failure reasons are comparable. "It got worse" is not a signal — "F04 task-drift during axis-3 tightening" is. Every log row tags exactly one code.

## The 14 canonical codes

### Generation failures

| Code | Name | Signature | Counter |
|------|------|-----------|---------|
| F01 | Sycophancy | User said "great!" and agent abandoned a flagged concern | Re-assert the concern before proceeding |
| F02 | Fabrication | Cited API / flag / file that doesn't exist | Verify before citing; `Glob` / `Grep` first |
| F03 | Context decay | Instruction from top of context violated at bottom | See @shared/conduct/context.md § Checkpoint protocol |
| F04 | Task drift | Work expanded past the stated goal | Re-read the success criterion; cut back to scope |
| F05 | Instruction attenuation | Rule stated once, obeyed once, then forgotten | Move rule to top-200 or bottom-200 slot |

### Action failures

| Code | Name | Signature | Counter |
|------|------|-----------|---------|
| F06 | Premature action | Edited before grounding — wrong file, wrong function | See @shared/conduct/tool-use.md § Read before Edit |
| F07 | Over-helpful substitution | Solved a problem the user didn't ask about | See @shared/conduct/discipline.md § Surgical changes |
| F08 | Tool mis-invocation | Wrong tool for the job (Bash for read, Write for small edit) | Default to the dedicated tool |
| F09 | Parallel race | Two writes to the same file / same branch | Serialize or partition by path |
| F10 | Destructive without confirmation | `rm`, `reset --hard`, `force push` without explicit yes | See @shared/conduct/verification.md § Dry-run for destructive ops |

### Reasoning failures

| Code | Name | Signature | Counter |
|------|------|-----------|---------|
| F11 | Reward hacking | Hit the metric by gaming it (e.g., pass assertion by weakening it) | Reviewer checks whether the test still tests the original behavior |
| F12 | Degeneration loop | Same edit, reverted, re-applied across iterations | No-regression contract; stop the axis |
| F13 | Distractor pollution | Long irrelevant context bent the output | See @shared/conduct/context.md § Smallest-set rule |
| F14 | Version drift | Used deprecated API / retired model ID / old flag | Check `models-registry.json` and docs before emitting |

## How to log a failure

In the plugin's failure log (e.g., `learnings.md` for convergence loops, `drift-log.md` for context-health tracking):

```markdown
## 2026-04-17 iteration v4 → v5 (reverted)

Code: F12 degeneration-loop
Dimension targeted: specificity
Hypothesis: tightening the `format` section would lift the specificity score
Outcome: specificity +0.3, clarity -0.8 → σ exploded, no-regression triggered
Counter: pick a different dimension next round; log this as a dead-end for v5
```

Required fields: `Code`, `Axis targeted` (if applicable), `Hypothesis`, `Outcome`, `Counter`.

## How to read the log before a new round

Before starting iteration N, scan the log for:

1. Any **F12 on the same dimension** → that dimension is saturated; try another.
2. Any **F11 from the reviewer** → the scoring surface itself is being gamed; re-derive the rubric.
3. Three **F04 in a row** → the success criterion is vague; escalate to the user.

## Escalation patterns

Some codes are single-occurrence — log and continue. Some require stopping:

| Code | Single occurrence | 3+ in one prompt |
|------|-------------------|------------------|
| F01, F02, F07, F13 | Log and continue | Escalate to developer — systemic issue |
| F03, F04, F05 | Checkpoint and reset context | Re-scope the task |
| F06, F08, F09, F10 | Revert, log, retry | Pause plugin — contract broken |
| F11, F12 | Revert, switch axis | Freeze convergence on this prompt |
| F14 | Regenerate against current registry | Audit the registry freshness |

## Anti-patterns in logging

- **Untagged free-text entries.** Not aggregable. Every row tags exactly one code.
- **Logging the fix, not the failure.** The log records what *didn't work* and why, not your victory lap.
- **Multiple codes on one entry.** Pick the dominant one. If truly two, split into two entries.
- **Logging at verdict time only.** Log the *hypothesis* before the iteration; log the *outcome* after. Both halves needed.
- **"Couldn't find a matching code."** Then propose a new one (F15+) in the PR, don't invent ad-hoc names. The taxonomy grows deliberately.

## Extending the taxonomy

New codes are additive. To propose F15:

1. Observe it in at least 3 independent prompts.
2. Name the signature precisely.
3. Write a counter that's testable.
4. Open a PR that updates this file *and* the learning entries that retroactively match.

Rejected: codes that overlap an existing one, codes defined by vibes, codes without a counter.
