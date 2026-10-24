#!/usr/bin/env bash
set -euo pipefail
usage() { echo 'Usage: kill_jobs.sh PATTERN [--signal TERM|INT|KILL] [--execute]' >&2; exit 2; }
[[ $# -ge 1 ]] || usage
pattern=$1; shift
[[ -n "$pattern" ]] || usage
sig=TERM; execute=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) execute=1; shift ;;
    --signal) [[ $# -ge 2 ]] || usage; sig=$2; shift 2 ;;
    *) usage ;;
  esac
done
[[ "$sig" == TERM || "$sig" == INT || "$sig" == KILL ]] || usage
# pgrep reads command lines once and skips inaccessible processes. Match the
# user's pattern literally in Bash, so regex characters in it stay literal.
while IFS= read -r line; do
  [[ "$line" == *' '* ]] || continue
  pid=${line%% *}
  cmd=${line#* }
  [[ "$pid" =~ ^[0-9]+$ ]] || continue
  [[ "$pid" != "$$" && "$pid" != "$PPID" ]] || continue
  [[ "$cmd" == *"$pattern"* ]] || continue
  IFS= read -r comm < "/proc/$pid/comm" 2>/dev/null || continue
  [[ "$comm" == codex* || "$comm" == python* || "$comm" == chrome* || "$comm" == chromium* ]] || continue
  if (( execute )); then
    kill -s "$sig" "$pid" 2>/dev/null || continue
    printf 'sent %s to %s (%s)\n' "$sig" "$pid" "$comm"
  else
    printf 'would send %s to %s (%s)\n' "$sig" "$pid" "$comm"
  fi
done < <(pgrep -u "$(id -u)" -f -a -- .)
