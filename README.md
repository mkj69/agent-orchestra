# Agent orchestra

A reusable skill for coordinating a large build with a coordinator, judgment focused leaders, and isolated Codex workers. It includes task prompts, integration and verification guidance, a shared board, a dashboard, and small operational scripts.

```text
User
  |
Coordinator: decisions, supervision, updates
  |                     |
Leaders: contracts, review, browser work, integration lines
  |                     |
Codex workers in separate git worktrees and branches
  |                     |
Tested integration lines -> final branch -> verification -> release
```

## Install

Python 3.10 or newer is required for the Python scripts. From this repository root, install the optional command that locates the skill files:

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/agent-orchestra skill-path
```

`python -m agent_orchestra --help` and `agent-orchestra --help` show the same command help. For screenshot contact sheets, install `.[images]` to include Pillow.

Copy the skill directory into your Claude skills directory. For a project local Claude setup:

```sh
mkdir -p .claude/skills
cp -R skills/agent-orchestra .claude/skills/agent-orchestra
```

For a personal setup, copy it into `~/.claude/skills/agent-orchestra`. Open `SKILL.md` from that directory or invoke `agent-orchestra` using your host's skill mechanism. The instructions also work as a reference when a host has no skill discovery.

The scripts use Bash and Python 3. `contact_sheet.py` needs Pillow. `shot.sh` needs Chrome or Chromium. Video extraction also needs `ffmpeg`. The scripts do not install these dependencies.
Set `ORCH_CLIP=x,y,width,height` for a screenshot cropped to known element bounds. Capture with a tall viewport and do not scroll or use an anchor.

## Quick start

```sh
export ORCH_REPO="$PWD" ORCH_BOARD="$PWD/notes/board.md"
export ORCH_WORKTREES="$PWD/../orchestra-worktrees" ORCH_OUTPUT_DIR="$PWD/notes/jobs"
mkdir -p notes
skills/agent-orchestra/scripts/board.sh init
skills/agent-orchestra/scripts/launch_codex.sh task01 tasks/task01.txt HEAD
python3 skills/agent-orchestra/scripts/dashboard.py --once
```

Write a bounded task prompt before launch. `launch_codex.sh` creates the worktree and starts `codex exec` in the background. It prints the PID, output path, and log path. Check the output and tests before marking the board entry done. The launcher does not merge or release work.

The dashboard writes `notes/dashboard/index.html` by default. Its optional JSON configuration can register named Codex tasks and leader task output files:

```json
{
  "jobs": {"task01": "Implement feature"},
  "leaders": {"leader01": {"label": "Integration", "path": "notes/leader01.output"}}
}
```

Set `ORCH_CONFIG` to that file, then run `dashboard.py` continuously. Serve the output directory with `python3 -m http.server 8766 --directory notes/dashboard` if local port access is available. `restart_dashboard.sh` restarts only the matching Python process and writes a PID file.

## Lessons in brief

- Give code tasks separate worktrees, branches, and file ownership.
- Append start and end records to the board. Stage only owned files.
- Keep a final output file and log for each worker; verify the work before integration.
- Supervise every 30 minutes and look for new independent work.
- Use shared contracts before parallel features and tested integration lines afterward.
- Regenerate generated artifacts and guard stable default hashes.
- Plan fresh install, docs, browser, layout, and publication checks before the final merge.
- Recover interrupted tasks from the transcript and the existing worktree.

See [SKILL.md](skills/agent-orchestra/SKILL.md) for the operating loop and the reference guides. Scripts print usage with `--help` where applicable.

`board.sh` appends ownership records. `kill_jobs.sh PATTERN` previews matching PIDs and needs `--execute` to signal them. `extract_prompts.py TRANSCRIPT OUTPUT_DIR` recovers interrupted task instructions. `rebuild_with_previews.sh` runs `ORCH_BUILD_CMD` and reattaches directories listed in `ORCH_PREVIEWS_FILE` as tab separated name and source path. `shot.sh` and `contact_sheet.py` support browser and layout review by a leader with local browser access.
