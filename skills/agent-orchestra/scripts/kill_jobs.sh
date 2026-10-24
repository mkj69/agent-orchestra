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
# Compare the pattern as data in Bash. No pgrep or pkill command line can self match.
declare -A exclude=()
pid=$$
while [[ "$pid" =~ ^[0-9]+$ && "$pid" -gt 1 ]]; do
  exclude[$pid]=1
  pid=$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null || true)
done
for path in /proc/[0-9]*/cmdline; do
  pid=${path#/proc/}; pid=${pid%%/*}
  [[ -z "${exclude[$pid]:-}" ]] || continue
  [[ -r "$path" ]] || continue
  comm=$(cat "/proc/$pid/comm" 2>/dev/null || true)
  [[ "$comm" == codex* || "$comm" == python* || "$comm" == chrome* || "$comm" == chromium* ]] || continue
  cmd=$(tr '\0' ' ' < "$path" 2>/dev/null || true)
  [[ "$cmd" == *"$pattern"* ]] || continue
  if (( execute )); then
    kill -s "$sig" "$pid"
    printf 'sent %s to %s (%s)\n' "$sig" "$pid" "$comm"
  else
    printf 'would send %s to %s (%s)\n' "$sig" "$pid" "$comm"
  fi
done
