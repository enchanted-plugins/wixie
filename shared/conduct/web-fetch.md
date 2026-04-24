# Web Fetch — Skills Reading the Live Web

Audience: Claude. How to read external web pages without burning budget, duplicating fetches, or citing stale content. Any skill that touches `WebFetch` or `WebSearch` — directly or via a subagent — obeys these rules.

## The rule

Web fetches cost latency, tokens, and context attention. Treat them like calls against a paid API: cache, dedup, budget. Don't fetch what you can re-use; don't re-use what's stale; don't blow your share of a parallel budget.

## Tier selection — by page shape, not URL origin

Pick the fetcher's model tier by what the caller needs back, not by where the page lives.

| Page shape | Tier | Why |
|------------|------|-----|
| Short structured (pricing, API ref, changelog, one-paragraph answer) | Haiku | Answer lives in the first 500 tokens; no synthesis |
| Long doc needing cross-section summary | Sonnet | Mid-judgment — too much for Haiku, overkill for Opus |
| Dense paper / benchmark PDF / technical spec | Opus | Technical judgment on what matters |
| Unfetchable (paywalled, heavy JS, 404, login wall) | Return error | Don't spend a call producing hallucinated content |

The same URL can route differently depending on what the caller needs. Classify the *ask*, not the *source*.

Defaulting everything to Haiku saves tokens on easy pages but produces shallow extracts on dense ones. Defaulting to Opus wastes budget. Classify first.

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
