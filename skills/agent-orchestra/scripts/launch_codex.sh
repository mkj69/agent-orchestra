#!/usr/bin/env bash
set -euo pipefail
usage() { echo 'Usage: launch_codex.sh TASK PROMPT_FILE [BASE_REF]' >&2; exit 2; }
[[ $# -ge 2 && $# -le 3 ]] || usage
[[ "$1" =~ ^[A-Za-z0-9_]+$ ]] || { echo 'TASK must contain only letters, digits, underscores' >&2; exit 2; }
task=$1
prompt=$(realpath "$2")
[[ -s "$prompt" ]] || { echo 'Prompt file is empty' >&2; exit 2; }
base=${3:-${ORCH_BASE:-HEAD}}
repo=$(realpath "${ORCH_REPO:-$(git rev-parse --show-toplevel)}")
worktrees=${ORCH_WORKTREES:-"$(dirname "$repo")/orchestra-worktrees"}
outdir=${ORCH_OUTPUT_DIR:-"$repo/notes/jobs"}
board=${ORCH_BOARD:-"$repo/notes/board.md"}
notes=${ORCH_NOTES_DIR:-"$(dirname "$board")"}
codex=${ORCH_CODEX_BIN:-codex}
if [[ -n ${ORCH_PREFER_API_FILE:-} && -f ${ORCH_PREFER_API_FILE} ]]; then
  codex=${ORCH_API_CODEX_BIN:-}
  [[ -n "$codex" ]] || { echo 'Set ORCH_API_CODEX_BIN to an API-authenticated Codex launcher' >&2; exit 2; }
fi
mode=${ORCH_MODE:-workspace-write}
duration=${ORCH_JOB_TIMEOUT:-3h}
no_commit=${ORCH_WORKER_NO_COMMIT:-0}
[[ "$mode" == workspace-write || "$mode" == read-only ]] || { echo 'ORCH_MODE must be workspace-write or read-only' >&2; exit 2; }
[[ "$no_commit" == 0 || "$no_commit" == 1 ]] || { echo 'ORCH_WORKER_NO_COMMIT must be 0 or 1' >&2; exit 2; }
timeout "$duration" true || { echo 'Invalid ORCH_JOB_TIMEOUT' >&2; exit 2; }
command -v "$codex" >/dev/null || { echo "Codex executable unavailable: $codex" >&2; exit 2; }
[[ -d "$repo/.git" ]] || { echo 'ORCH_REPO must have a .git directory' >&2; exit 2; }
git -C "$repo" rev-parse --verify "$base^{commit}" >/dev/null
mkdir -p "$worktrees" "$outdir" "$notes"
wt="$worktrees/$task"
branch=${ORCH_BRANCH:-"orch/$task"}
[[ ! -e "$wt" ]] || { echo "Worktree exists: $wt" >&2; exit 2; }
git -C "$repo" worktree add "$wt" -b "$branch" "$base"
ORCH_BOARD="$board" "$(dirname "$0")/board.sh" init
ORCH_BOARD="$board" "$(dirname "$0")/board.sh" start "$task" "$branch" "${ORCH_FILES:-see prompt: $prompt}"
log="$outdir/$task.log"
out="$outdir/$task.out"
: > "$log"
: > "$out"
git_access=()
if [[ "$no_commit" == 0 ]]; then
  git_access=(--add-dir "$repo/.git")
fi
(
  cd "$wt"
  nohup timeout "$duration" "$codex" exec -s "$mode" -C "$wt" "${git_access[@]}" --add-dir /tmp --add-dir "$notes" -o "$out" - < "$prompt" > "$log" 2>&1 &
  printf '%s\n' "$!" > "$outdir/$task.pid"
)
printf 'PID %s\nOUT %s\nLOG %s\nWORKTREE %s\nBRANCH %s\n' "$(cat "$outdir/$task.pid")" "$out" "$log" "$wt" "$branch"
