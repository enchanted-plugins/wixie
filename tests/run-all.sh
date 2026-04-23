#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PASS=0
FAIL=0

run_test() {
  local test_file="$1"
  local name
  name="$(basename "$test_file" .sh)"
  if bash "$test_file" "$REPO_ROOT" 2>/dev/null; then
    echo "  PASS  $name"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $name"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "================================================"
echo "  WIXIE TEST SUITE"
echo "================================================"
echo ""

for suite_dir in "$SCRIPT_DIR"/*/; do
  suite="$(basename "$suite_dir")"
  echo "  [$suite]"
  for test_file in "$suite_dir"test-*.sh; do
    [[ -f "$test_file" ]] || continue
    run_test "$test_file"
  done
  echo ""
done

TOTAL=$((PASS + FAIL))
echo "================================================"
echo "  $PASS/$TOTAL passed"
if [[ $FAIL -gt 0 ]]; then
  echo "  $FAIL FAILED"
  exit 1
fi
echo "  All tests passed."
echo "================================================"
