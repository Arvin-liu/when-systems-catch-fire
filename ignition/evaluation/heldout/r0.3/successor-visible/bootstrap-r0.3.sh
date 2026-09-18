#!/bin/sh
set -eu

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf '%s\n' FAIL_WRONG_REPOSITORY
  exit 1
}
guard="$repo_root/ignition/evaluation/tools/task_branch_guard_r0_3.py"
if [ ! -f "$guard" ]; then
  printf '%s\n' FAIL_AUTHORIZATION_RECEIPT
  exit 1
fi
exec python3 "$guard" --operation CHECK
