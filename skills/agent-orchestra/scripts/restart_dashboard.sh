#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd "$(dirname "$0")" && pwd)
repo=${ORCH_REPO:-$PWD}
run_dir=${ORCH_DASHBOARD_DIR:-"$repo/notes/dashboard"}
mkdir -p "$run_dir"
pidfile=${ORCH_DASHBOARD_PIDFILE:-"$run_dir/dashboard.pid"}
log=${ORCH_DASHBOARD_LOG:-"$run_dir/dashboard.log"}
if [[ -f "$pidfile" ]]; then
  old=$(cat "$pidfile")
  if [[ "$old" =~ ^[0-9]+$ && -r "/proc/$old/cmdline" ]]; then
    comm=$(cat "/proc/$old/comm" 2>/dev/null || true)
    cmd=$(tr '\0' ' ' < "/proc/$old/cmdline")
    if [[ "$comm" == python* && "$cmd" == *"$script_dir/dashboard.py"* ]]; then
      kill "$old"
    fi
  fi
fi
nohup python3 "$script_dir/dashboard.py" > "$log" 2>&1 &
printf '%s\n' "$!" > "$pidfile"
printf 'dashboard PID %s; output %s/index.html\n' "$(cat "$pidfile")" "$run_dir"
