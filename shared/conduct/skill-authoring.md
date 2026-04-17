# Skill Authoring — Frontmatter Discipline

Audience: Claude. How to write a SKILL.md so Claude invokes it at the right moment. As a plugin family grows past a few skills, trigger-collision becomes the #1 discovery failure.

## The discovery surface

Claude selects skills by matching the user's request against the `description` field of each available skill's frontmatter. **Body content is not used for selection.** A skill whose description is off will never fire, regardless of how well the body is written.

## Frontmatter contract

```yaml
---
name: refactor-module
description: >
  Refactors a module toward a named target metric via the optimizer loop.
  Use when: user runs /refactor, asks to improve a module's score,
  or references a HOLD verdict. Do not use for initial drafting (see /scaffold).
model: sonnet
tools: [Read, Edit, Write, Bash, Grep, Glob]
---
```

Required fields:

| Field | Rule |
|-------|------|
| `name` | kebab-case, matches the slash-command |
| `description` | ≤1024 chars; both **what** and **when**; third person |
| `model` | `opus` / `sonnet` / `haiku` — match the tier |
| `tools` | whitelist; smallest set that works |

## Description: both what and when

A description answers two questions. Skills missing either get skipped.

- **What:** "Refactors a module toward the target metric via the optimizer loop."
- **When:** "Use when the user runs /refactor or asks to improve a module's score."

Bad (what only): *"Module refactoring."*  
Bad (when only): *"For /refactor."*  
Good: *"Refactors a module toward the target metric. Use when the user runs /refactor or references a HOLD verdict."*

Optionally add a **do-not-use** clause to prevent steal from adjacent skills:

> *"Do not use for initial drafting (see /scaffold) or for cross-target adaptation (see /translate)."*

## Third person, always

POV drift breaks discovery. The selector is matching against a description, not reading a memo.

- Good: *"This skill converges prompts…"*
- Good: *"Converges prompts…"* (implicit third person)
- Bad: *"I converge prompts…"*
- Bad: *"You should run this when…"*

## Length limit

Hard cap: 1024 characters on `description`. Target 300-600. Beyond that, the selector starts losing signal; under 100, discovery matches too loosely and the wrong skill fires.

## No XML in frontmatter

Frontmatter is YAML. XML tags inside `description` break the parser and silently disable the skill. Keep frontmatter plain prose.

## One skill per verb

Bundle-skills lose to split-skills. If a single SKILL.md claims to do *craft* + *refine* + *converge*, the selector cannot disambiguate user intent.

| Bad | Good |
|-----|------|
| `prompt-lifecycle` (craft + refine + converge) | Three skills, each scoped |
| `review-and-fix` (review + edit) | `review`, plus the existing Edit tool |
| `deploy-anywhere` (translate + test + harden) | Three skills, composed by the user |

A skill's name, description, and behavior should each point at one verb.

## Tool whitelisting

List the minimum tools the skill needs. Over-granting lets the skill do things outside its lane and erodes the one-skill-per-verb contract.

| Skill role | Typical tool set |
|-----------|------------------|
| Investigator | Read, Grep, Glob |
| Red-team | Read, Grep, Glob — never Write |
| Crafter | Read, Write, Bash |
| Translator | Read, Write (target only) |
| Validator (Haiku tier) | Read, Grep |

If a skill needs Bash, narrow it to the specific commands via settings permissions — don't pass free-form Bash on trust.

## Body structure

The body is the *runbook*, not the pitch. Structure:

1. **Preconditions** — what must be true before this skill runs.
2. **Inputs** — args the slash command accepts, their defaults.
3. **Steps** — numbered. Each step names the tool used and the success criterion.
4. **Outputs** — artifacts produced, where they land.
5. **Handoff** — what the next skill in the chain expects.
6. **Failure modes** — which `shared/conduct/failure-modes.md` codes apply.

The body is read *after* selection, so optimize it for execution, not discovery.

## Testing a new skill's discovery

Before merging a new skill:

1. Write 5 user phrasings that *should* fire it.
2. Write 5 that *should not* (adjacent skills, wrong tool).
3. Invoke with each; verify the selector picks the right skill.

Ship only when 9/10 dispatches are correct.

## Anti-patterns

- **Description with only the what, no when.** Never fires at the right moment.
- **First-person description.** POV drift tanks recall.
- **Bundled skill (multi-verb).** Selector can't disambiguate.
- **Over-broad tool whitelist.** Skill edits files it shouldn't.
- **Body that explains *why* instead of *how*.** The body is a runbook.
- **Missing do-not-use clause on overlapping skills.** Siblings steal dispatches.
