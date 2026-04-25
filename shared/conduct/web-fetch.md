# Web Fetch — Skills Reading the Live Web

Audience: Claude. How to read external web pages without burning budget, duplicating fetches, or citing stale content. Any skill that touches `WebFetch` or `WebSearch` — directly or via a subagent — obeys these rules.

## The rule

Web fetches cost latency, tokens, and context attention. Treat them like calls against a paid API: cache, dedup, budget. Don't fetch what you can re-use; don't re-use what's stale; don't blow your share of a parallel budget.

## Tool ownership — WebFetch is Haiku-tier-only

**`WebFetch` is owned by Haiku-tier subagents.** The orchestrator (Opus) and decomposer/synth tiers do NOT call `WebFetch` directly — they delegate via the Agent tool to a Haiku fetcher subagent and consume the structured return.

| Caller | May call `WebFetch` directly? |
|--------|-------------------------------|
| Opus orchestrator (e.g., `/create`, `/deep-research` Phase 1/4/5) | No — delegate to a Haiku fetcher |
| Sonnet executor (triangulator, optimizer, red-team) | No — receive findings from Haiku, do not re-fetch |
| Haiku fetcher (e.g., `plugins/deep-research/agents/fetcher.md`) | **Yes — this is the canonical owner** |
| Haiku validator | No — read-only on artifacts, not the live web |

**Why this rule.**
1. Cost — Haiku is the cheapest tier; bulk page-reading work belongs there, not at Opus prices.
2. Context hygiene — fetched pages are large; a Haiku fork absorbs the page tokens, returns ≤ 400 words. The orchestrator's context never sees the raw HTML.
3. Determinism — fetcher.md's mechanical paragraph-by-paragraph tests (A/B/C) work because the agent runs them literally; an Opus orchestrator running the same steps will skip ahead.

Permission requirement: project `.claude/settings.json` must allow `"WebFetch"` for Haiku subagents to actually run it. Domain-pinned WebFetch entries (`WebFetch(domain:foo.com)`) are insufficient when the fetcher hits diverse sources — allow `"WebFetch"` broadly so the fetcher can chase any URL its WebSearch returns.

## Page-shape sizing — within Haiku, not across tiers

The fetcher is always Haiku, but the *amount of work* per fetcher varies by page shape:

| Page shape | Haiku fetcher behavior |
|------------|------------------------|
| Short structured (pricing, API ref, changelog) | Top 500 tokens; one finding |
| Long doc needing cross-section summary | Walk top 3 sections; up to 3 findings; truncate at 8 KB |
| Dense paper / benchmark PDF / technical spec | Walk abstract + key results section; flag with `low_coverage: true` if dense math defeats paragraph-by-paragraph extraction |
| Unfetchable (paywalled, heavy JS, 404, login wall) | Return `{url, error: "unfetchable"}` — don't guess |

For genuinely dense papers where Haiku struggles, the fix is *more fetchers in parallel* (each on a narrow query), not escalating to Sonnet/Opus for fetching. Synthesis is what scales up the tier — `WebFetch` itself stays at Haiku.

## Caching — don't re-fetch what you already have

- **URL-hash cache**, 24-hour TTL. Two skills asking for the same URL share one fetch.
- **Query-hash cache** for `WebSearch`. Identical search strings within a session → one call, shared result.
- Cache is skipped on explicit `--force`, or when the caller declares the topic fresh-critical ("as of today", release-day checks).
- Cache lives in plugin state (`plugins/<plugin>/state/fetch-cache/`) or a shared location when the router is in use.
- Eviction is explicit (manual sweep or `/research-refresh`-style skill), never silent.

## Budget discipline — parallel fetchers share one

When a skill spawns N parallel fetchers, enforce:

| Budget | Default |
|--------|---------|
| Session-wide bytes after extraction | 200 KB |
| Per-fetcher structured output | 400 words |
| Per-page extracted text | 8 KB (hard truncate with `partial: true` flag) |

One heavy page must not eat the budget the other fetchers were allocated. If you hit the per-page cap, return a partial with a note — never silent truncation.

## Cite hygiene

Every fetched fact carries all four fields:

| Field | Rule |
|-------|------|
| `url` | Exact URL fetched |
| `date` | Publish date if detectable (meta tag, URL path, copyright footer); else `null` |
| `source_type` | One of `official | third-party | community | paper | other` |
| `quote` | Verbatim excerpt ≤ 200 chars that contains the fact |

No paraphrase in `quote`. Paraphrases belong in `claim`. Paraphrase-as-quote is F02 fabrication.

## Failure modes

| Code | Signature | Counter |
|------|-----------|---------|
| F02 | Paraphrase in the `quote` field | Quote must be copy-paste verbatim; if you can't, return without that finding |
| F13 | Adjacent-topic facts polluted findings | Topic filter applied *before* extraction, not after |
| F14 | Cited a retired spec / deprecated API | `date` field present; downstream weights by freshness |
| F09 | Two parallel fetchers raced on cache write | Atomic write-then-rename on cache store |
| F08 | Used Bash curl instead of WebFetch | Prefer the dedicated tool; WebFetch handles headers, timeouts, encoding |

## Anti-patterns

- **Default everything to Haiku.** Dense papers get shallow extracts, load-bearing claims miss nuance.
- **Default everything to Opus.** Easy pages cost 10× what they should.
- **No cache at all.** Re-fetching a public doc five times per session is invisible waste.
- **Quote that "captures the gist."** Either copy-paste a sentence or return without the finding.
- **Fetch-without-date.** Can't tell if the page is from 2022 or last week; downstream can't weight freshness.
- **Per-plugin fetch implementations that silently diverge.** All fetching is governed by this conduct; plugin-level agents specialize (task-specific extraction), not reinvent (routing, caching, cite hygiene).
- **Fetching when a local doc answers the question.** Check `shared/references/` and plugin docs first. Web fetches are for the *live* web, not replacements for reading local material.
