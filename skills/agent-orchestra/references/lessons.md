# Lessons and fixes

Run the examples from the repository root. Replace sample task names and paths with the current ones.

## Separate code tasks

**Symptom:** Agents overwrite edits or stage unrelated work. **Cause:** They share a checkout or file. **Fix:** Give each code task a branch and worktree. Allow in place edits only for disjoint documentation files, and stage owned files by name. **Example:** `git worktree add ../worktrees/parser -b task/parser HEAD && git -C ../worktrees/parser add src/parser.py tests/test_parser.py`

## Grant linked worktree metadata deliberately

**Symptom:** A worker can edit code but cannot commit. **Cause:** The linked worktree stores Git metadata in the main repository. Its index lock may still be read only. **Fix:** Add the main `.git` directory, the board directory, and `/tmp` to writable directories. If a commit still fails, leave the edits for the leader to commit. **Example:** `codex exec -s workspace-write -C ../worktrees/parser --add-dir "$PWD/.git" --add-dir "$PWD/notes" --add-dir /tmp -o notes/jobs/parser.out - < tasks/parser.txt`

## Keep browser work with an agent that can run a browser

**Symptom:** A worker cannot open a socket, capture a page, or start another worker. **Cause:** Its sandbox restricts those operations. **Fix:** Assign browser review and recording to a leader with access. Do not make nested Codex a task dependency. **Example:** `ORCH_CHROME=chromium skills/agent-orchestra/scripts/shot.sh http://localhost:8765/ notes/shots/home.png 1440 3200`

## Distinguish return from completion

**Symptom:** A dashboard shows a finished job whose edits have not passed review. **Cause:** A nonempty `-o` file means the command returned. **Fix:** Save the final message and log, then inspect the diff, tests, and commit before marking the board done. **Example:** `test -s notes/jobs/parser.out && tail -n 20 notes/jobs/parser.log && git -C ../worktrees/parser diff --check`

## Signal a verified PID

**Symptom:** A restart command kills its own shell. **Cause:** `pkill -f` matches the command line containing its own pattern. **Fix:** Preview numeric PIDs from `/proc`, check the process name, exclude callers and ancestors, then signal by PID. **Example:** `skills/agent-orchestra/scripts/kill_jobs.sh parser && skills/agent-orchestra/scripts/kill_jobs.sh parser --execute`

## Quote prompt heredocs

**Symptom:** Prompt text runs a shell command while the task file is being written. **Cause:** An unquoted heredoc expands backticks and substitutions. **Fix:** Quote the delimiter. **Example:**

```sh
cat <<'PROMPT' > tasks/parser.txt
Write the parser.
PROMPT
```

## Record file ownership before editing

**Symptom:** Two agents change the same shared file. **Cause:** Neither checked active claims. **Fix:** Read the append only board, record task ID, branch, and files at start, then record status and commit at end. **Example:** `skills/agent-orchestra/scripts/board.sh start parser task/parser src/parser.py`

## Register and refresh the dashboard

**Symptom:** Running work is missing or shows stale progress. **Cause:** The job was not registered, or the page was not regenerated. **Fix:** Register each job, refresh about every 30 seconds, identify Codex by its `-o` argument in `/proc`, and use leader output file time plus last assistant text for leader status. **Example:** `ORCH_CONFIG=notes/dashboard.json python3 skills/agent-orchestra/scripts/dashboard.py --once`

## Supervise on a schedule

**Symptom:** Returned jobs wait unattended while other cores sit idle. **Cause:** No regular check verifies reports, integrates work, or finds new parallel tasks. **Fix:** Every 30 minutes inspect reports and diffs, run tests, rebuild, update the log, dispatch the next tasks, and reconsider dependencies. **Example:** `git status --short && python3 -m pytest -q -p no:cacheprovider`

## Use tested integration lines

**Symptom:** A merge queue grows and failures are hard to locate. **Cause:** Too many branches enter one line without a test between merges. **Fix:** Give each line one integrator. Merge one branch, test, and record the commit before the next. Start a second line from the same snapshot when needed, then merge both into a final branch. **Example:** `git switch integration/a && git merge --no-ff task/parser && python3 -m pytest -q -p no:cacheprovider`

## Combine small fixes before the final merge

**Symptom:** The final integrator repeats small conflict resolutions. **Cause:** Related fixes arrive as many branches. **Fix:** Premerge them into one tested fixes branch, then merge that branch once. **Example:** `git switch -c integration/fixes "$SNAPSHOT" && git merge --no-ff fix/parser && git merge --no-ff fix/cli && python3 -m pytest -q -p no:cacheprovider`

## Regenerate derived artifacts

**Symptom:** A hand resolved generated file disagrees with its source. **Cause:** Generated output was treated as independent source during a merge. **Fix:** Merge source, rerun the generator, then inspect the generated diff. **Example:** `./tools/build_site.sh && git diff --check`

## Guard defaults and provenance

**Symptom:** Existing seeded output or provenance hashes change after an unrelated config merge. **Cause:** New keys enter serialization or hash inputs. **Fix:** Keep default output byte identical when required and compare it with a frozen fixture. Add a focused hash regression test. **Example:** `sha256sum tests/fixtures/default-output.json && python3 -m pytest -q tests/test_provenance.py`

## Share one feature contract

**Symptom:** Parallel modules disagree on JSON fields, registration calls, or styles. **Cause:** Each worker guessed its own interface. **Fix:** Write one contract with schema, API, CSS variables, and file names before dispatch, then include it in every prompt. **Example:** `cat notes/worlds_contract.txt >> tasks/grid.txt`

## Restart workers after an early requirement change

**Symptom:** A running worker follows an obsolete instruction. **Cause:** `codex exec` has no live message channel. **Fix:** Preview and stop its PID, append a `RESUMING` note, and relaunch in the same worktree. Send a direct message to a leader when that channel exists. **Example:** `skills/agent-orchestra/scripts/kill_jobs.sh grid --execute && printf '\nRESUMING: add the new field.\n' >> tasks/grid.txt`

## Recover interrupted work from evidence

**Symptom:** A replacement worker loses the original task and later decisions. **Cause:** Instructions are split across transcript records. **Fix:** Extract the Agent prompt and later SendMessage text, save a work in progress patch, inspect the existing worktree, and resume useful edits. **Example:** `python3 skills/agent-orchestra/scripts/extract_prompts.py session.jsonl notes/recovered && git -C ../worktrees/grid diff > notes/grid.patch`

## Reattach previews after every rebuild

**Symptom:** A preview disappears when the site rebuilds. **Cause:** The build replaces its output directory. **Fix:** Mount previews under the main site's `preview/` path and copy them back after every build so one reachable port suffices. **Example:** `ORCH_BUILD_CMD=./tools/build_site.sh ORCH_PREVIEWS_FILE=notes/previews.tsv skills/agent-orchestra/scripts/rebuild_with_previews.sh`

## Capture pages without scrolling

**Symptom:** Headless Chrome returns a blank screenshot after navigation or scrolling. **Cause:** Its capture state becomes unreliable after a scroll. **Fix:** Use a tall viewport, avoid anchors, and clip to known element bounds when needed. **Example:** `ORCH_CLIP=0,0,1200,900 skills/agent-orchestra/scripts/shot.sh http://localhost:8765/ notes/shots/top.png 1200 3200`

## Build verification tools early

**Symptom:** Release checks reveal errors too late to fix calmly. **Cause:** Independent computation checks, properties, documentation checks, fresh install, publication dry run, browser smoke, and layout review began after integration. **Fix:** Build those tools in parallel with features and run them on a named integrated commit. **Example:** `git rev-parse HEAD > notes/verified-commit.txt && python3 -m pytest -q -p no:cacheprovider`

## Propagate decisions and timelines

**Symptom:** Agents implement different versions of a user decision. **Cause:** The change was not logged and sent to each affected task. **Fix:** Record the exact decision in the supervision log, notify active leaders, update worker prompts, and revise the phase timeline in the user's time zone. Give the user one decision question at a time. **Example:** `printf '%s\n' 'Decision: use the shared schema for every world.' >> notes/supervision.md`

## Treat file time as a hint

**Symptom:** A leader appears finished or active when its output file only stopped changing or was touched. **Cause:** File modification time is an observation, not a completion signal. **Fix:** Read the last assistant text and task report, then confirm the branch and tests. **Example:** `stat -c '%y %n' notes/leaders/integration.output && git log -1 --oneline integration/a`

## Audit public artifacts separately

**Symptom:** A passing test suite still leaves local paths or oversized files in a package or site. **Cause:** Build filters and generated assets are outside unit test scope. **Fix:** Inspect the actual distribution and site before publication. **Example:** `python3 -m build && tar -tf dist/*.tar.gz | head`
