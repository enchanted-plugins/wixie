#!/usr/bin/env python3
"""Flux Convergence Engine — iterates up to 100 times to converge on DEPLOY verdict.

Like gradient descent for prompts. Each iteration reduces the deviation from
perfection by fixing the weakest axis, re-scoring, and repeating.

Usage:
    python convergence.py <prompt-file>
    python convergence.py <prompt-file> --max 50
    python convergence.py <prompt-file> --verbose

Reads a prompt file, scores it, applies automatic fixes, re-scores,
and loops until DEPLOY (overall >= 9, all axes >= 7) or plateau.

Stdlib only. No pip installs.
"""
import sys, os, re, json
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# ─── Import scoring functions from self-eval ───────────────────────────────────

def _import_scorer():
    """Import scoring functions from self-eval.py."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("self_eval", os.path.join(SCRIPT_DIR, "self-eval.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_eval = _import_scorer()
AXES = _eval.AXES
SCORERS = _eval.SCORERS


def score_prompt(text):
    """Score a prompt and return dict of axis->score + overall."""
    scores = {a: round(fn(text), 1) for a, fn in zip(AXES, SCORERS)}
    scores["overall"] = round(sum(scores[a] for a in AXES) / len(AXES), 1)
    return scores


def is_deploy(scores):
    """Check if scores meet DEPLOY criteria."""
    return scores["overall"] >= 9.0 and all(scores[a] >= 7.0 for a in AXES)


# ─── Fix functions ─────────────────────────────────────────────────────────────

def fix_clarity(text):
    """Improve clarity: remove hedge words, shorten long sentences."""
    # Remove hedge words
    hedges = [
        (r'\bmaybe\s+', ''), (r'\bperhaps\s+', ''), (r'\bpossibly\s+', ''),
        (r'\bsomewhat\s+', ''), (r'\btry to\s+', ''),
        (r'\bif possible,?\s*', ''), (r'\bmight want to\s+', ''),
    ]
    for pattern, replacement in hedges:
        text = re.sub(pattern, replacement, text, flags=re.I)

    # Shorten very long sentences (>50 words) by splitting at commas or semicolons
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        words = line.split()
        if len(words) > 50 and ('; ' in line or ', and ' in line or ', which ' in line):
            line = re.sub(r';\s+', '.\n', line, count=1)
            line = re.sub(r',\s+which\s+', '. This ', line, count=1)
        new_lines.append(line)
    return '\n'.join(new_lines)


def fix_completeness(text):
    """Add missing completeness components."""
    tl = text.lower()

    # Check for role
    has_role = bool(re.search(r'\b(you are|act as|role:|persona:|as a|your role)\b', tl))
    if not has_role:
        # Find the first line of actual content and prepend role
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith(('<', '#', '---')):
                lines.insert(i, "You are a domain expert.\n")
                break
        text = '\n'.join(lines)

    # Check for task definition
    has_task = bool(re.search(r'\b(task:|objective:|goal:|your job|you will|you should|instructions:)\b', tl))
    if not has_task:
        text = text.replace("You are a domain expert.\n", "You are a domain expert. Your job is to complete the following task.\n", 1)

    # Check for output format
    has_format = bool(re.search(r'\b(output format|respond in|return as|format:|response format|output:|json|xml|markdown)\b', tl))
    if not has_format:
        text += "\n\nOutput format: structure your response clearly with headers and sections.\n"

    # Check for constraints
    has_constraints = bool(re.search(r"\b(do not|don't|never|must not|avoid|constraint)\b", tl))
    if not has_constraints:
        text += "\nDo not include information you are unsure about.\n"

    return text


def fix_efficiency(text):
    """Remove filler phrases and redundant instructions."""
    fillers = [
        r"it's worth noting that\s*",
        r"please note that\s*",
        r"as an AI,?\s*",
        r"I want you to\s*",
        r"I need you to\s*",
        r"please make sure\s*(to\s*)?",
        r"it is important to note that\s*",
        r"keep in mind that\s*",
        r"I would like you to\s*",
        r"please ensure that\s*",
        r"in order to\s+",
    ]
    for filler in fillers:
        text = re.sub(filler, '', text, flags=re.I)

    # Remove double blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove trailing whitespace
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    return text


def fix_model_fit(text):
    """Improve model fit based on detected model."""
    tl = text.lower()
    claude = bool(re.search(r'\b(claude|anthropic)\b|<(instructions|context|example)>', tl))
    gpt = bool(re.search(r'\b(gpt-4|gpt-5|openai|chatgpt)\b', tl))
    oseries = bool(re.search(r'\b(o1|o3|o4-mini|o-series)\b', tl))

    if claude:
        # Add "think thoroughly" if missing
        if 'think thoroughly' not in tl:
            text = re.sub(
                r'(</instructions>)',
                '\nThink thoroughly before responding.\n\\1',
                text, count=1
            )
            if '</instructions>' not in text:
                text += "\n\nThink thoroughly before responding.\n"
        # Remove "step by step" — bad for Claude
        text = re.sub(r'\bthink step by step\b', 'think thoroughly', text, flags=re.I)

    if gpt:
        # Add "think step by step" if missing CoT
        has_cot = bool(re.search(r'\b(step by step|think through|let\'s think)\b', tl))
        if not has_cot:
            text += "\n\nThink step by step through your analysis before providing the final answer.\n"

    if oseries:
        # Remove CoT — harmful for o-series
        text = re.sub(r'\n.*think step by step.*\n', '\n', text, flags=re.I)
        text = re.sub(r'\n.*let\'s think.*\n', '\n', text, flags=re.I)

    return text


def fix_failure_resilience(text):
    """Add fallback/edge case handling if missing."""
    tl = text.lower()
    patterns_found = {
        'if_error': bool(re.search(r'\bif\b.{0,30}\b(error|fail|cannot|unable|unclear|missing|invalid|empty)\b', tl)),
        'edge_case': bool(re.search(r'\b(edge case|corner case|special case|exception|unexpected|otherwise)\b', tl)),
        'fallback': bool(re.search(r'\b(fallback|default to|if unsure|if you cannot|if not provided|when in doubt)\b', tl)),
        'validate': bool(re.search(r'\b(validate|verify|check that|ensure that|confirm|if unclear|ask for clarification)\b', tl)),
    }

    additions = []
    if not patterns_found['if_error']:
        additions.append("If the input is empty or invalid, report the error clearly and explain what input is expected.")
    if not patterns_found['edge_case']:
        additions.append("Handle unexpected edge cases gracefully rather than failing silently.")
    if not patterns_found['fallback']:
        additions.append("If unsure about any information, state your uncertainty explicitly rather than guessing.")
    if not patterns_found['validate']:
        additions.append("Verify your output against the requirements before delivering the final response.")

    if additions:
        # Find or create edge_cases/fallback section
        if '<edge_cases>' in text:
            insert_point = text.index('</edge_cases>')
            text = text[:insert_point] + '\n' + '\n'.join(additions) + '\n' + text[insert_point:]
        elif '# Edge' in text or '## Edge' in text:
            text += '\n' + '\n'.join(f'- {a}' for a in additions)
        else:
            text += '\n\n' + '\n'.join(additions) + '\n'

    return text


FIXERS = {
    "Clarity": fix_clarity,
    "Completeness": fix_completeness,
    "Efficiency": fix_efficiency,
    "Model Fit": fix_model_fit,
    "Failure Resilience": fix_failure_resilience,
}


# ─── Main loop ─────────────────────────────────────────────────────────────────

def run(prompt_path, max_iterations=100, verbose=False):
    if not os.path.isfile(prompt_path):
        print(f"Error: {prompt_path} not found", file=sys.stderr)
        sys.exit(2)

    with open(prompt_path, "r", encoding="utf-8") as f:
        text = f.read()

    if not text.strip():
        print("Error: Empty prompt file.", file=sys.stderr)
        sys.exit(2)

    history = []
    plateau_count = 0
    best_score = 0
    best_text = text

    print(f"\n{'=' * 60}")
    print(f"  FLUX CONVERGENCE ENGINE")
    print(f"  Target: DEPLOY (overall >= 9.0, all axes >= 7.0)")
    print(f"  Max iterations: {max_iterations}")
    print(f"{'=' * 60}\n")

    for iteration in range(1, max_iterations + 1):
        scores = score_prompt(text)
        overall = scores["overall"]
        history.append(overall)

        # Track best version
        if overall > best_score:
            best_score = overall
            best_text = text

        # Check DEPLOY
        if is_deploy(scores):
            print(f"  Iteration {iteration}: {overall}/10 — DEPLOY")
            print(f"\n  Prompt is production-ready.")
            _save(prompt_path, best_text)
            _print_final(scores, iteration)
            return scores

        # Check plateau (3 consecutive same scores)
        if len(history) >= 3 and history[-1] == history[-2] == history[-3]:
            plateau_count += 1
            if plateau_count >= 1:
                print(f"  Iteration {iteration}: {overall}/10 — PLATEAU (score unchanged for 3 iterations)")
                print(f"\n  Reached practical ceiling for this prompt structure.")
                _save(prompt_path, best_text)
                _print_final(scores, iteration)
                return scores

        # Progress update
        weak = [a for a in AXES if scores[a] < 7]
        if verbose or iteration <= 3 or iteration % 10 == 0:
            weak_str = ", ".join(f"{a}={scores[a]}" for a in weak) if weak else "none"
            print(f"  Iteration {iteration}: {overall}/10 — fixing: {weak_str}")

        # Apply fixes for weak axes (lowest first)
        axes_by_score = sorted(AXES, key=lambda a: scores[a])
        for axis in axes_by_score:
            if scores[axis] < 9.0 and axis in FIXERS:
                text = FIXERS[axis](text)

    # Max iterations reached
    print(f"\n  Max iterations ({max_iterations}) reached. Best score: {best_score}/10")
    _save(prompt_path, best_text)
    scores = score_prompt(best_text)
    _print_final(scores, max_iterations)
    return scores


def _save(path, text):
    """Save the improved prompt back to the file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _print_final(scores, iterations):
    """Print final scorecard."""
    print(f"\n{'=' * 60}")
    print(f"  FINAL SCORES (after {iterations} iteration{'s' if iterations != 1 else ''})")
    print(f"{'=' * 60}")
    for a in AXES:
        val = scores[a]
        pct = round((val / 10) * 20)
        bar = "#" * pct + "." * (20 - pct)
        print(f"  {(a + ':').ljust(22)}{val:4.0f}/10  {bar}")
    print(f"\n  {'OVERALL:'.ljust(22)}{scores['overall']:4.1f}/10")
    deploy = is_deploy(scores)
    print(f"  VERDICT: {'DEPLOY' if deploy else 'BEST EFFORT'}")
    print(f"{'=' * 60}\n")


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    max_iter = 100
    args = []
    skip_next = False
    for i, a in enumerate(sys.argv[1:]):
        if skip_next:
            skip_next = False
            continue
        if a == "--max":
            max_iter = int(sys.argv[i + 2])
            skip_next = True
            continue
        if a.startswith("--") or a == "-v":
            continue
        args.append(a)

    if not args:
        print("Usage: python self-perfection.py <prompt-file> [--max N] [--verbose]", file=sys.stderr)
        sys.exit(2)

    scores = run(args[0], max_iterations=max_iter, verbose=verbose)
    sys.exit(0 if is_deploy(scores) else 1)


if __name__ == "__main__":
    main()
