# Prompt templates

Use real paths and a bounded task in each prompt. Include the shared contract when tasks must interoperate. Quote heredoc delimiters when writing prompt files.

## Write task preamble

```text
You own task <ID> on branch <BRANCH> in worktree <WORKTREE>.
Read <BOARD> before editing. Append START with task ID, branch, and files. Claim only <FILES>. Append END with done or blocked and the commit hash.
Read the repository guidance and relevant source. Implement <OUTCOME>. Preserve <INVARIANTS>. Run <TESTS> and report commands and results.
Stage only your files. Commit if permitted. If commit is blocked, leave the worktree intact and report the reason. Do not push.
```

## Read-only review preamble

```text
Review <SCOPE> without changing repository files. Use scratch space only under <SCRATCH>.
Report verified findings with path and line, evidence, impact, and a concrete fix. If an area is clean, name what you checked. Do not infer a pass from another agent's report.
```

## Resume preamble

```text
You take over task <ID> at <WORKTREE>. Original instructions: <ORIGINAL>.
Later instructions, in order: <FOLLOWUPS>. The latest instruction wins on conflict.
First inspect git status, diff, log, untracked files, and prior output. Save the WIP diff to <PATCH>. Read the board and append a resume record. Preserve good work, finish missing work, verify yourself, then append an end record.
```

## Leader instruction

```text
Lead <AREA>. Own judgments, scope, review, and integration. Split disjoint mechanical work into worker tasks if delegation is authorized. Record decisions and evidence in <SUPERVISION_LOG>. Review actual files and test output. Keep user updates short and specific. Escalate one decision question at a time.
```

## Shared contract skeleton

```text
Version and owner: <VERSION>, <OWNER>
Purpose: <WHAT MUST PLUG TOGETHER>
Inputs and schema: <FIELDS, TYPES, VALIDATION>
Registration API: <FUNCTION, ARGUMENTS, ERROR BEHAVIOR>
Files and ownership: <PATHS, GENERATORS, CONSUMERS>
Style and accessibility: <TOKENS, VIEWPORTS, KEYBOARD RULES>
Compatibility: <DEFAULTS AND STABLE OUTPUTS>
Contract tests: <COMMANDS AND EXPECTED ASSERTIONS>
Change process: <WHO APPROVES AND HOW WORKERS LEARN>
```

## Critique personas

- **Correctness reviewer:** Reproduce behavior through an independent path and probe boundary cases.
- **Integration reviewer:** Check contracts, imports, generated artifacts, default hashes, and merge side effects.
- **Documentation reviewer:** Run commands and compare names, defaults, links, and claims with source.
- **Design reviewer:** Inspect actual screenshots at desktop and mobile widths, keyboard access, contrast, and layout.
- **Release reviewer:** Inspect package contents, private paths, email exposure, artifact size, and install from a clean environment.

Critiques need evidence and exact fixes. A reviewer should state what was checked when no issue is found.
