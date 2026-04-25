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

## Cross-repo path references

Documentation, conduct modules, learning entries, and any other tracked file that references a path inside the ecosystem MUST use one of two forms:

- **Repo-relative** when the reference points inside a specific repo: `wixie/docs/ROADMAP.md`, `shared/conduct/precedent.md`. Always preferred — works for every developer regardless of where they cloned the repo.
- **`<repo-root>/<plugin>/...`** when the reference must include the parent directory containing all sibling enchanted-plugins repos: `<repo-root>/wixie/plugins/inference-engine/state/artifacts.jsonl`. The placeholder `<repo-root>` is the developer's local parent — `~/git/enchanted-plugins`, `/Users/alice/code`, `D:/dev`, whatever fits their setup.

**Never write absolute machine-specific paths** (`c:/git/enchanted-skills/...`, `/home/dan/repos/...`) in a tracked file. They leak the author's filesystem layout, break for every other developer, and trigger F02 Fabrication when an agent later tries to follow them. Caught violations: count as a F02 instance and fix in place.

For runnable shell scripts that genuinely need a substitutable path, use `$REPO_ROOT` set by the developer's shell or by an `install.sh` — runtime variables, distinct from documentation placeholders.

## Rename sweeps with sed

When propagating a rename across SVGs, rendered HTML, or other artifacts that mix visible text and internal IDs:

1. **Drop `\b` boundaries on SVG/HTML internal IDs.** GNU sed treats underscore as a word character, so `\bhornet\b` does NOT match `hornet_learning` — internal IDs slip through unchanged.
2. **Run all three case variants in one pass:** `sed -i -e 's/Hornet/Crow/g' -e 's/hornet/crow/g' -e 's/HORNET/CROW/g'`. Rendered SVG output and node label conventions both use UPPER and lowercase forms; case-sensitive single-form sweep misses them.
3. **Inline-rendered diagrams need a separate pass.** `docs/architecture/index.html` (and similar) often contains inline `<pre class="mermaid">` blocks that render via JS at runtime — neither the `.mmd` source files nor the `.svg` exports control them. After a rename, grep `index.html` independently for the old name.

## Semantic identifiers

When tools return handles, prefer semantic over opaque.

- **Good:** prompt slug, branch name, test ID.
- **Bad:** row ID, in-memory pointer, session-scoped handle.

Semantic IDs survive serialization, logs, and human review. Opaque handles die at the first cache eviction.

## Namespacing as the registry grows

When a plugin ships a tool, prefix it: `wixie_converge_score`, not `score`. As the registry grows past ~20 tools, collision-driven mis-selection becomes the #1 failure. A longer name is cheaper than a wrong dispatch.

## Anti-patterns

- **Retry-with-tweaks on an uninformative error.** Diagnose first; repeated guesses burn context.
- **Parallel Writes to the same file.** Race. One wins, one is lost silently.
- **Bash for what the dedicated tool does.** `cat` for a file read, `find` for a glob — every time, reach for the dedicated tool.
- **Edit without a preceding Read.** The tool blocks this; don't work around it.
- **Unquoted paths with spaces.** Intermittent failures that look like tool bugs.
- **Opaque handles in returns.** Future-you has no way to re-derive what the handle meant.
