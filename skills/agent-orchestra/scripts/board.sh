#!/usr/bin/env bash
set -euo pipefail

board=${ORCH_BOARD:-${ORCH_REPO:-$PWD}/notes/board.md}
usage() { echo 'Usage: board.sh init | start TASK BRANCH FILES | end TASK STATUS COMMIT [NOTE] | append TEXT' >&2; exit 2; }
[[ $# -ge 1 ]] || usage
cmd=$1; shift
mkdir -p "$(dirname "$board")"
case "$cmd" in
  init)
    [[ $# -eq 0 ]] || usage
    if [[ ! -e "$board" ]]; then
      ( set -C; printf '# Shared task board\n\nAppend one record per event. Read ownership before editing shared files.\n\n## Log\n' > "$board" ) 2>/dev/null || true
    fi
    ;;
  start|end|append)
    case "$cmd" in
      start) [[ $# -eq 3 ]] || usage; line="$(date -u +%FT%TZ) | $1 | START | $2 | $3" ;;
      end) [[ $# -ge 3 && $# -le 4 ]] || usage; line="$(date -u +%FT%TZ) | $1 | END | $2 | $3${4:+ | ${4:-}}" ;;
      append) [[ $# -eq 1 ]] || usage; line=$1 ;;
    esac
    [[ "$line" != *$'\n'* && "$line" != *$'\r'* ]] || { echo 'Board record must be one line' >&2; exit 2; }
    printf '%s\n' "$line" >> "$board"
    ;;
  *) usage ;;
esac
