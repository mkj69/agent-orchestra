# Communication and supervision

## Status update

Use the user's language. For a Chinese update, a useful compact format is:

```text
已完成：<可核对的成果与提交>。
正在做：<当前阶段、负责人、预计时间，按用户时区>。
阻塞：<具体原因与下一步>。
需要决定：<一个问题与选项，仅在必要时>。
```

Send an update when evidence, timing, risk, or a required decision changes. Revise phase estimates honestly. Do not imply completion from a worker's final message alone.

## Decision log

Append each decision to the supervision log with timestamp and time zone, decision, reason or user wording, affected tasks, and who was notified. Preserve superseded decisions with a pointer to the replacement. Propagate changes to active leaders immediately. A running `codex exec` job requires a stop and resume if the change must reach it before completion.

## Thirty minute supervision pass

1. Read board, output files, logs, and previous supervision entry.
2. Confirm which agents reported and inspect their actual changes and tests.
3. Queue one verified branch at a time for each integrator. Run tests, rebuild previews, and record commit hashes.
4. Dispatch the next wave. Look for tasks that can start from an existing snapshot, large tasks that split by file, and idle capacity.
5. Update the log with status, decisions, evidence, next check, and phase estimates.
6. Inform the user only of concrete changes or a decision that needs their input.

The supervision schedule is an operational reminder. Configure it in the host scheduler only when authorized by the user and environment.
