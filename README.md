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

## Claude lead with Codex workers

For quality-heavy, scene-based creative work such as rebuilding an animated explainer, give a **headless Claude lead** the judgment and integration role, with Codex workers implementing disjoint scenes in separate git worktrees. Use the [generic lead brief template](skills/agent-orchestra/references/creative-lead-brief.md): it covers where things are, what the user said, quality bar, team rules and file reservations, the review loop, rules, and the final report. Not for routine edits; delegation and outside-sandbox services require authorization from the user and host.

The lead keeps one reservation table for scene/files (including generated/shared assets), launches every agent job with a timeout, and reviews every scene frame by frame in **both themes**. It rejects the first pass with concrete scene/time/theme notes when below the bar, iterates, reviews diffs, then commits worker edits itself if worker Git metadata is read-only. Workers need not start Chrome: an outside-sandbox render service returns frames and contact sheets for their review. The supervisor only monitors the lead during execution; before merging it independently inspects contact sheets extracted from the **final media files**, checks displayed numbers by hand, and runs verification. The lead's report is evidence, not a substitute for this gate.

For a headless lead, check actual weekly quota first and route **new** work through the subscription below about 80%, otherwise use a configured API gateway (no secrets in the brief). The small wrapper does not check quota itself:

```sh
ORCH_WEEKLY_USAGE_PERCENT=75 ORCH_LEAD_TIMEOUT=8h \
  skills/agent-orchestra/scripts/route_lead.sh -p "$(cat tasks/lead.md)" \
  --permission-mode acceptEdits --allowedTools 'Read,Edit,Bash'
# At 80% or above, also set ORCH_API_CLAUDE to your configured gateway launcher.
```

`launch_codex.sh` bounds worker jobs with `ORCH_JOB_TIMEOUT` (default `3h`). Set `ORCH_WORKER_NO_COMMIT=1` to omit its writable main `.git` grant when workers must leave commits to the lead; the lead can commit reviewed work. Verify the recorded PID (the `timeout` process) before signaling it; never use `pkill -f` patterns that may match the supervisor's shell.

For workers without Chrome, start the render service **outside** their sandbox with a trusted, configurable command. The command runs in the requested worktree and accepts `OUTPUT --at TIMES --themes THEMES`; it must produce `OUTPUT/<theme>/at-*.png`, one frame per time. Pillow is required for contact sheets. The request and output directories must be shared with workers; configure access without exposing unrelated worktrees or credentials.

```sh
python3 skills/agent-orchestra/scripts/render_requests.py \
  --worktrees ./worktrees --requests ./jobs/requests --output ./jobs/frames \
  --render-command 'python3 tools/video/render.py' --timeout 600
# Publish ./jobs/requests/scene01.json atomically (write temp, then rename):
# {"worktree":"/absolute/path/under/worktrees/scene01","times":[0,1.5,3],"themes":["light","dark"]}
# Read ./jobs/frames/scene01/DONE or ERROR and sheet-light.png/sheet-dark.png.
```

The service validates allowed worktrees, times and themes, handles one request at a time, and renames requests to `.handled`. Its renderer runs with the service's host permissions: start it only with a trusted render command, isolated output directories, and trusted request writers. Do not point it at untrusted code or grant it broader permissions than needed.

After the lead renders final media, the supervisor makes **new** contact sheets from those files, not the service's draft sheets, and checks the numbers independently:

```sh
python3 skills/agent-orchestra/scripts/contact_sheet.py final-light-sheet.png --video final-light.mp4 --every 3
python3 skills/agent-orchestra/scripts/contact_sheet.py final-dark-sheet.png --video final-dark.mp4 --every 3
```

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
- Reserve shared content in one table before launching parallel writers; never overlap active claims.
- Use `timeout` for every agent job; route new lead jobs by actual weekly quota (subscription below about 80%, otherwise API).
- Never use `pkill -f` for job cleanup; verify and signal a PID.
- Append start and end records to the board. Stage only owned files.
- Keep a final output file and log for each worker; verify the work before integration.
- Supervise every 30 minutes and look for new independent work.
- Use shared contracts before parallel features and tested integration lines afterward.
- Regenerate generated artifacts and guard stable default hashes.
- Plan fresh install, docs, browser, layout, and publication checks before the final merge.
- Recover interrupted tasks from the transcript and the existing worktree.

See [SKILL.md](skills/agent-orchestra/SKILL.md) for the operating loop and the reference guides. Scripts print usage with `--help` where applicable.

`board.sh` appends ownership records. `kill_jobs.sh PATTERN` previews matching PIDs and needs `--execute` to signal them. `extract_prompts.py TRANSCRIPT OUTPUT_DIR` recovers interrupted task instructions. `rebuild_with_previews.sh` runs `ORCH_BUILD_CMD` and reattaches directories listed in `ORCH_PREVIEWS_FILE` as tab separated name and source path. `shot.sh` and `contact_sheet.py` support browser and layout review by a leader with local browser access.
