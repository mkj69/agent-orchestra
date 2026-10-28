# Template: Claude lead with Codex workers

Copy this brief into a task file and replace placeholders. This is a template, not permission to delegate or publish; follow the user's and host's agent policies. Do not paste credentials into prompts or logs.

## Where things are

- Lead integration worktree/branch: `<lead-worktree>` / `<lead-branch>`; source, scene map, generated files, asset references, renderer, tests: `<paths and commands>`.
- Existing visual references (including any approved prior design), current artifact, and accessibility/style rules: `<paths>`.
- Worker worktree root, job output, notes, request/output directories: `<paths>`.

## What the user said

- Quote or faithfully summarize each current request and earlier constraints that still apply: `<requirements>`.
- Separate non-negotiables from suggestions; record open decisions for the supervisor: `<decisions>`.

## Quality bar

- One clear idea per scene; motion communicates it rather than hiding changes behind fades. Use purposeful pacing and legible type at the target and reduced sizes.
- Check composition, spelling, continuity, contrast, overlaps, and clipping across **every scene**, in **both themes** and at transitions; preserve approved branding and visual language.
- Verify every displayed number against an independent source or by hand, not just the renderer's data. Record expected outputs and provenance.

## Team rules

- Lead owns the shared scene contract, storyboard, global helpers, review, and integration. Split scene files and tests into disjoint worker reservations *before* launching parallel jobs. Keep **one** reservation table (`task | worktree | owned files/scenes | start | release`); update it before dispatch and on completion. No overlapping reservations, including shared assets or generated files.
- Each worker gets its own git worktree and branch from the same approved base, a bounded prompt, owned files, quality bar, renderer interface, test command, and concrete acceptance criteria. Set `ORCH_WORKER_NO_COMMIT=1` with `scripts/launch_codex.sh` when Git metadata is read-only for workers; they leave edits for the lead, who reviews, stages only owned paths, commits, and integrates serially. Workers cannot start Chrome in their sandbox. Do not grant broader permissions just to make commits possible.
- Wrap **every** lead/worker agent job in `timeout`; retain PID, log, and final output. If stopping a stuck job, check its PID and signal that PID only; never use `pkill -f` (its pattern can match the supervisor's own shell).
- The lead runs headless via `claude -p "<brief or task>" --permission-mode acceptEdits --allowedTools '<approved tools>'` (or a configured API gateway). The supervisor monitors its log, process and milestones, not individual scene implementation. Use subscription capacity while weekly usage is below about 80%, then route **new** jobs to an API gateway using the wrapper; do not silently switch a running job. Keep credentials out of the brief.
- If workers cannot render, the lead hosts `scripts/render_requests.py` **outside** their sandbox with a trusted render command. Workers submit atomic JSON requests and inspect returned frames/contact sheets; the lead still does its own visual review. Keep the browser/runtime and render-service permissions outside worker sandboxes.

## Review loop (lead, not delegated)

1. For **every** scene, render and inspect frames through its whole motion (entrance, transitions, holds, exit) in light and dark. Look at actual frames, not just code or a single thumbnail. Treat round 1 as a real rejection gate: reject shortcomings with concrete scene/time/theme-specific notes (e.g. clipped label, unmotivated fade, incorrect value) and request a revised pass. Repeat until each scene is accepted; do not accept a flawed scene just to satisfy a round count.
2. Integrate accepted edits one worktree at a time; the lead commits reviewed changes. Rerender complete media in both themes and check duration, captions, poster, scene boundaries, and tests. Generate contact sheets **from the final media files**, not preliminary scene PNGs.
3. The supervisor independently checks final-media contact sheets and verifies displayed numbers **by hand** against independent expected values, then tests and reviews diffs before merging. A lead report alone is not approval to merge.

## Rules

- Work only in assigned worktrees. Do not publish, push, merge into the final branch, use secrets, or change unrelated files without explicit authorization. Observe time, resource and tool limits: `<limits>`.
- Record brief progress events in `<notes-file>`; escalate blocked decisions and partial results rather than guessing.

## Report

Write `<report-file>` with changes by scene, review rounds and fixes, final-media paths and contact sheets for both themes, reviewed commit list, test commands/results, numbers checked, unfinished work, and risks. Give the supervisor the report and final artifacts for independent verification before any merge.
