"""Flux shared sanitizer — input validation utilities. Stdlib only."""
import sys


def read_prompt(argv=None):
    """Read prompt from file argument or stdin. Exits on error."""
    argv = argv or sys.argv
    if len(argv) > 1:
        # Skip --flags and their values
        args = []
        skip_next = False
        for a in argv[1:]:
            if skip_next:
                skip_next = False
                continue
            if a.startswith("--"):
                skip_next = True
                continue
            args.append(a)
        if args:
            try:
                with open(args[0], "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                print(f"Error: File not found: {args[0]}", file=sys.stderr)
                sys.exit(2)

    if not sys.stdin.isatty():
        return sys.stdin.read()

    return None


def require_nonempty(text, script_name="script"):
    """Validate that text is non-empty. Exits with usage message if empty."""
    if not text or not text.strip():
        print(f"Error: Empty prompt provided.", file=sys.stderr)
        print(f"Usage: echo 'prompt' | python {script_name}", file=sys.stderr)
        sys.exit(2)
    return text
