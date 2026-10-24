# Lessons and fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Agents overwrite each other | Several writers share one checkout or file | Give each code task a branch and worktree. Allow in-place main branch edits only for disjoint documentation files. Stage named files, never `git add -A`. |
| Commit fails from a worktree | Linked worktree metadata lives in the main repository's `.git`; its lock may remain read-only | Launch workspace-write with `--add-dir <repo>/.git`, plus writable `/tmp` and the notes directory when needed. If the index lock still fails, leave edits for a leader to commit. |
| Worker cannot test a page or start another worker | Worker sandbox restricts sockets, Chrome, or nested Codex | Assign browser checks, screenshots, and recording to a leader. Do not plan nested Codex as a dependency. |
| Dashboard marks a job as finished before review | The nonempty `-o` file records the final message only | Treat it as returned. Verify edits, tests, and commit separately. Always write both an output file and a log. |
| A restart command kills its own shell | `pkill -f` matches its command line | Select numeric PIDs through `/proc`, check `/proc/<pid>/comm`, exclude the caller and ancestors, then signal by PID. |
| Prompt text runs shell commands unexpectedly | Unquoted heredoc delimiters expand backticks and substitutions | Use quoted delimiters such as `<<'EOF'` and feed prompts through files or stdin. |
| An agent edits another agent's files | No common ownership record | Append a start line with task ID, branch, and files, then an end line with status and commit. Read the board before shared edits. Keep the log append-only. |
| Progress is opaque | Job registration and last messages are missing | Register jobs in dashboard configuration. Refresh HTML about every 30 seconds. Find Codex PIDs through `/proc/*/cmdline` and their `-o` paths. Use output mtime and last assistant text for leader task files. |
| A long run stalls silently | No scheduled supervision | Every 30 minutes check reports, verify, integrate, test, rebuild, log decisions, dispatch next work, and search for new parallelism. Report only concrete changes or decisions. |
| Merge queue becomes a bottleneck | One integration branch receives too many branches | Use one integrator per line, merge and test one at a time, open a second line from the same snapshot, then merge lines in a final branch. Pre-merge small fixes. |
| Generated files conflict or defaults drift | Artifacts are merged as source, or config keys affect hashes | Regenerate after merges. Keep default output byte-identical where required and guard with hash tests, including provenance hashes. |
| Parallel modules disagree on interfaces | Each worker invents its own schema | Publish one contract covering data, registration API, style variables, and file names; include it in every prompt. |
| Requirements change while a worker runs | `codex exec` has no live message channel | If early and consequential, stop by PID, append a RESUMING note to the task file, and relaunch in the same worktree. SendMessage may update leader agents. |
| A limited or crashed agent loses instructions | Original prompt and later guidance are scattered | Extract Agent tool input and SendMessage follow-ups from transcript JSONL, save the WIP diff as a patch, inspect state, and resume without discarding good work. |
| A rebuild erases previews | The site output directory is recreated | Mount previews under the main site's `preview/` path after each rebuild. Use a single reachable port. |
| Browser shots go blank after scrolling | Headless Chrome's capture behavior after scroll | Use a tall viewport, avoid anchors and scrolling, and clip to element bounds when using browser automation. |
| Release looks fine in one test path | Cross-checks and publication checks started too late | Build independent computation checks, property tests, docs-to-code checks, fresh install, publication dry run, browser smoke tests, and layout contact sheets early. Run them on an integrated snapshot. |
| User decisions diverge across agents | Updates are not recorded and propagated | Record each decision in memory and supervision log, revise the phase timeline in the user's time zone, and notify every affected running agent promptly. |
