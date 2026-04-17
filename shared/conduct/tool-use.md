# Tool Use — Invocation Hygiene

Audience: Claude. How to call tools so the right one runs, the right arguments flow, and parallel dispatch doesn't race.

## Right tool, first try

| If you would reach for… | Use instead |
|-------------------------|-------------|
| `find`, `ls -R` | `Glob` |
| `grep`, `rg` | `Grep` |
| `cat`, `head`, `tail` | `Read` |
| `sed`, `awk` for in-file edits | `Edit` |
| `echo > file`, heredoc-to-file | `Write` |
| `printf` / `echo` for user messages | Output text directly |

Bash is for shell-only work — git, npm, test runners, build tools. Reaching for Bash to do what a dedicated tool does better is a smell; fix the reflex, don't route around it.

## Parallel vs. serial

Two tool calls in one message run in parallel. That's the right default — *if* they're independent.

| Shape | Rule |
|-------|------|
| N independent reads (Read/Grep/Glob/Agent) | Parallel. One message, N calls. |
| Read A, then Read B-where-A-points | Serial. B depends on A's output. |
| Two Writes or Edits | Serial. Order matters; diffs compose. |
| Write + Read-same-file | Serial. Read stale before write lands. |
| Bash mutating state + anything downstream | Serial. Side effects. |

A good heuristic: *if swapping the order would change the result, they're not independent.*

## Error payloads are contracts

When a tool returns an error, the payload must be actionable for the next step.

- **"Failed"** → useless. Retry loop, no progress.
- **"Expected X, got Y at line N"** → usable. Agent can fix.
- **"File not found: /foo/bar.md"** → usable.
- **"Syntax error"** without location → useless.

If you're writing a tool, this is the contract: error messages name *what* and *where*. If you're consuming one, and the error is unhelpful, stop and diagnose — don't retry with tweaks.

## Read before Edit

The Edit tool enforces this, and for good reason: editing without reading is how you clobber a file you half-remember.

1. `Read` the file — even if you think you know it.
2. Match `old_string` to the exact post-Read content, including indentation.
3. If `old_string` isn't unique, add surrounding context until it is. Don't `replace_all` a non-unique short string by accident.

The line-number prefix from Read (`   42\tfoo`) is not part of the file. Don't include it in `old_string`.

## Bash hygiene

1. **Quote paths with spaces.** Always. Windows paths especially.
2. **Absolute paths over `cd`.** Session state bleeds; absolute paths are reproducible.
3. **No `cd` unless the user asks.** The working directory is the user's, not yours to relocate.
4. **Chain with `&&` when order matters; parallel via multiple tool calls when it doesn't.**
5. **Unix syntax on bash-on-Windows** — `/dev/null`, not `NUL`. Forward slashes in paths.

## Semantic identifiers

When tools return handles, prefer semantic over opaque.

- **Good:** prompt slug, branch name, test ID.
- **Bad:** row ID, in-memory pointer, session-scoped handle.

Semantic IDs survive serialization, logs, and human review. Opaque handles die at the first cache eviction.

## Namespacing as the registry grows

When a plugin ships a tool, prefix it: `flux_converge_score`, not `score`. As the registry grows past ~20 tools, collision-driven mis-selection becomes the #1 failure. A longer name is cheaper than a wrong dispatch.

## Anti-patterns

- **Retry-with-tweaks on an uninformative error.** Diagnose first; repeated guesses burn context.
- **Parallel Writes to the same file.** Race. One wins, one is lost silently.
- **Bash for what the dedicated tool does.** `cat` for a file read, `find` for a glob — every time, reach for the dedicated tool.
- **Edit without a preceding Read.** The tool blocks this; don't work around it.
- **Unquoted paths with spaces.** Intermittent failures that look like tool bugs.
- **Opaque handles in returns.** Future-you has no way to re-derive what the handle meant.
