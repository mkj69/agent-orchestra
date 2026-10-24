---
name: agent-orchestra
description: Coordinate a large, concurrent build with a human facing coordinator, judgment focused leaders, and isolated Codex workers. Use for requests such as "orchestrate many agents", "multi agent build", "多 agent 并行", or "Claude 带队 Codex 干活". Do not invoke for ordinary single task edits.
---

# Agent orchestra

Use this skill when several independent tasks, reviews, and integration steps must advance together. Adapt the number of agents to the work and the available permissions. The user's instructions and the current environment's agent policy control whether delegation is allowed. This skill does not itself authorize starting agents, compute, publication, or external actions.

## Roles

- **Coordinator:** Speak with the user, record decisions, assign ownership, maintain the supervision log, and route merges through integrators. Send short Chinese updates when the user prefers Chinese. Ask one decision question at a time.
- **Leaders:** Handle judgment, integration, design review, prose, research synthesis, and browser work. In a tight leader budget, plan, split, review, and decide while workers perform hands-on tasks.
- **Workers:** Use `codex exec` for code, documentation, data, tests, mechanical merges, and read-only critiques. Give each writing task disjoint files and its own worktree and branch. Do not assume a worker can open sockets, use Chrome, or spawn nested Codex jobs.

## Operating loop

1. **Plan:** Break the outcome into tasks with owners, files, dependencies, evidence, and a release gate. Identify work that can start from a snapshot. Record decisions in the supervision log.
2. **Contract:** Before parallel features meet, write one shared schema and registration contract. Include it in every relevant prompt. See [prompts.md](references/prompts.md).
3. **Dispatch:** Create a worktree for each code task. Use `scripts/launch_codex.sh` when its assumptions fit. Append a start record to the shared board before editing, then an end record with status and commit. Keep main branch in-place edits to disjoint documentation files. Stage only owned files.
4. **Monitor:** Check output files, logs, the board, and a dashboard. An output file with content means a Codex run returned, not that its work passed review. Every 30 minutes, run the supervision checklist, verify reports, dispatch newly independent tasks, and update the log. See [communication.md](references/communication.md).
5. **Integrate:** Assign one integrator per line. Merge one branch at a time and test after each. If queues grow, start another line from the same snapshot and later merge the lines. Pre-merge small fixes into one tested branch. Regenerate generated files and guard stable defaults with hashes. See [integration.md](references/integration.md).
6. **Verify:** Start verification tooling while features are built, then run it on integrated snapshots. Cover independent computation, properties, docs and commands, a fresh install, publication dry run, browser pages, and layout. See [verification.md](references/verification.md).
7. **Release:** Review the verified candidate, record remaining risks and user decisions, and perform only actions authorized for this task.

## Budget modes

**Leader-rich:** Assign leaders to design, integration, writing, browser review, and supervision. Their workers own narrow edits and tests.

**Leader-tight:** Leaders write contracts and prompts, inspect evidence, resolve decisions, and integrate. Assign hands-on implementation and read-only critique to workers. Keep at least one leader responsible for each integration line.

## Failure handling

- A changed requirement cannot be sent to a running `codex exec` job. If the change is urgent, identify its PID from `/proc`, stop that PID, append the change to the task file, and relaunch in the same worktree with the resume preamble. Use `scripts/kill_jobs.sh` rather than `pkill -f`.
- For a crash or limit, recover the original Agent prompt and later messages from transcript JSONL with `scripts/extract_prompts.py`. Inspect the worktree, preserve useful edits as a patch, and use the resume preamble.
- If a sandbox blocks commits through linked worktree metadata, leave the edits intact and let the leader commit. Do not widen permissions without authorization.
- If the user sees only one preview port, mount previews under the main site's `preview/` path and reattach them after each rebuild. Use `scripts/rebuild_with_previews.sh`.

## Checklist

- [ ] Ownership, dependency, branch, files, and completion evidence recorded for every task.
- [ ] Shared contracts distributed before parallel implementation.
- [ ] Board has start and end records; dashboard includes all current jobs.
- [ ] Every merge is reviewed and tested; generated outputs are regenerated.
- [ ] Stable defaults and provenance are checked on the integrated branch.
- [ ] Verification evidence, decisions, and release state are logged.
- [ ] User update reflects a concrete change or asks one needed decision.

Read [lessons.md](references/lessons.md) when diagnosing a failure. Read the other references at the phase where they apply. The scripts are aids, not a replacement for reviewing their output.
