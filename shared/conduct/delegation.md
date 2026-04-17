# Delegation — Subagent Contracts

Audience: Claude. How plugins spawn subagents without poisoning the parent context or duplicating work. Root `CLAUDE.md` names the tier (Opus / Sonnet / Haiku); this module defines the *contract* at the boundary.

## When to spawn a subagent

Spawn one when **all three** hold:

1. The raw material is large — logs, dozens of files, a test suite run.
2. The answer back to the parent is small — a verdict, a list of paths, a score.
3. The subtask is genuinely independent of the ongoing parent reasoning.

If even one is false, stay in the parent context. Delegation for its own sake burns tokens and latency.

## The three non-negotiable clauses

Every subagent prompt includes all three. Missing one is a contract violation.

### 1. Structured return clause

End the prompt with an explicit output shape. The subagent's final message *is* the hand-off; intermediate tool noise is invisible to the parent.

> *"Return one findings block per matching file as: `{path, line_range, finding, confidence}`. Skip unrelated files. Under 300 words total."*

No structure → parent gets a discursive paragraph → parent wastes a round re-extracting.

### 2. Scope fence

Name what's out of scope. Subagents over-help by default.

> *"Do not fix issues you find. Do not edit files. Read-only investigation."*
> *"Do not spawn sub-subagents. If the task is larger than expected, return early with a note."*

### 3. Context briefing

The subagent has no memory of the conversation. Brief it like a colleague who just walked in: goal, what's already ruled out, why this matters.

> *"I'm tracking down a score-inflation bug in the convergence loop. Already ruled out: the metadata writer and the self-eval path. Need to check: the reviewer's score-extraction regex. Files: …"*

A one-sentence command yields a shallow generic report. A briefing yields a useful one.

## Tool whitelisting per subagent

Match tools to the job. Over-granting is how subagents corrupt the parent repo state.

| Subagent role | Tools granted |
|---------------|---------------|
| Investigator (research, grep) | Read, Grep, Glob |
| Red-team (adversarial audit) | Read, Grep, Glob — never Write or Edit |
| Test-runner | Read, Bash (test commands only) |
| Format translator | Read, Write (target file only) |
| Validator (Haiku tier) | Read, Grep |

The parent runs the actual writes after consuming the subagent's summary.

## Parallel vs. serial

Parallel when independent. Serial when step 2 consumes step 1's output.

| Pattern | Rule |
|---------|------|
| Multiple independent reads | Parallel. One message, multiple Read/Grep calls. |
| Multiple independent subagent investigations | Parallel. One message, multiple Agent calls. |
| Subagent whose output feeds the next subagent | Serial. Wait, read result, then spawn. |
| Two writes to the same file | **Never parallel.** Race condition. |

A good heuristic: if two subagents could contradict each other, don't run them in parallel.

## Tier placement

Root `CLAUDE.md` § Agent tiers is canonical. For delegation: Opus spawns (never spawned), Sonnet takes long loops / attacks / translation / heavy search, Haiku takes shape checks and freshness audits. Routing up or down the tiers breaks the cost-or-quality contract.

## Trust but verify the subagent

The subagent's summary describes what it *intended to do*, not necessarily what it did.

1. **If the subagent wrote code:** read the diff before declaring the parent task done.
2. **If the subagent reported "all tests pass":** ask for the relevant test command output or re-run it.
3. **If the subagent's finding contradicts your prior belief:** don't blindly accept — check the underlying evidence.

## Anti-patterns

- **Delegating a task you could do in one tool call.** "Spawn a subagent to read one file" — just read the file.
- **Prompt that says "figure out what I need."** Subagent lacks conversation context. Brief it.
- **Parallel subagents with overlapping writes.** Race, lost work. Serialize or partition by path.
- **Sub-subagents.** Two-level delegation loses too much context. Flatten.
- **Trusting the subagent's "done" without reading its output.** The result is the contract, not the claim.
- **Subagent loop without a termination clause.** A fixed N-attack audit is bounded; an open-ended "keep finding issues" isn't.
