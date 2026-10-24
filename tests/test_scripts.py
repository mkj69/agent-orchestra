"""Offline behavior tests for board, dashboard, and transcript recovery."""

import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/agent-orchestra/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dashboard = load("dashboard")
extract_prompts = load("extract_prompts")


class BoardTests(unittest.TestCase):
    def test_init_append_and_reject_multiline(self):
        with tempfile.TemporaryDirectory() as temp:
            board = Path(temp) / "notes/board.md"
            env = {**os.environ, "ORCH_BOARD": str(board)}

            def run(*args):
                return subprocess.run([str(SCRIPTS / "board.sh"), *args], env=env,
                                      capture_output=True, text=True)

            self.assertEqual(run("init").returncode, 0)
            self.assertEqual(run("init").returncode, 0)
            self.assertEqual(run("start", "t1", "orch/t1", "src/a.py").returncode, 0)
            self.assertEqual(run("end", "t1", "done", "abc123", "tests passed").returncode, 0)
            self.assertNotEqual(run("append", "bad\nrecord").returncode, 0)
            text = board.read_text()
            self.assertEqual(text.count("# Shared task board"), 1)
            self.assertIn("t1 | START | orch/t1 | src/a.py", text)
            self.assertIn("t1 | END | done | abc123 | tests passed", text)
            self.assertNotIn("bad\nrecord", text)


class DashboardTests(unittest.TestCase):
    def test_proc_argv_exact_output_and_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outdir = root / "jobs"
            outdir.mkdir()
            output = outdir / "task.out"
            log = outdir / "task.log"
            log.write_text("thinking\ncodex\nMaking progress\nexec\n")
            proc = root / "proc/123"
            proc.mkdir(parents=True)
            (proc / "cmdline").write_bytes(b"/bin/codex\0exec\0-o\0" + str(output).encode() + b"\0")
            self.assertEqual(dashboard.codex_output_path(["/bin/codex", "exec", "-o", str(output)]), output)
            self.assertIsNone(dashboard.codex_output_path(["/bin/echo", "exec", "-o", str(output)]))
            running = dashboard.running_outputs(root / "proc")
            self.assertEqual(running, {output.resolve()})
            rows = dashboard.collect_rows(outdir, {"jobs": {"task": "Implement feature"}}, running=running)
            self.assertEqual(rows[0][3], "running")
            self.assertEqual(rows[0][5], "Making progress")
            output.write_text("Finished and tested")
            rows = dashboard.collect_rows(outdir, {}, running=set())
            self.assertEqual(rows[0][3], "returned")
            self.assertEqual(rows[0][5], "Finished and tested")
            page = dashboard.render_page(rows, ["<script>alert(1)</script>"], [])
            self.assertIn("&lt;script&gt;", page)
            self.assertNotIn("<script>alert", page)

    def test_leader_last_text_and_atomic_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            taskfile = root / "leader.output"
            taskfile.write_text(json.dumps({"message": {"role": "assistant", "content": [
                {"type": "text", "text": "Integration ready"}]}}) + "\n")
            rows = dashboard.collect_rows(root / "jobs", {"leaders": {
                "leader1": {"label": "Integration", "path": str(taskfile)}}}, running=set())
            self.assertEqual(rows[0][5], "Integration ready")
            board = root / "board.md"
            board.write_text("## Log\nentry\n")
            dest = root / "dashboard/index.html"
            dashboard.generate(root, root / "jobs", board, dest, {})
            self.assertIn("entry", dest.read_text())
            self.assertFalse(dest.with_name("index.html.tmp").exists())


class TranscriptTests(unittest.TestCase):
    def test_agent_prompt_result_and_later_message(self):
        records = [
            {"message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "call1", "name": "Agent", "input": {
                    "description": "Build parser", "prompt": "Implement parser"}}]}},
            {"message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "call1", "content": '{"agentId":"agent-123"}'}]}},
            {"message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "call2", "name": "SendMessage", "input": {
                    "recipient": "agent-123", "content": "Also test empty input"}}]}},
            {"message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "call3", "name": "SendMessage", "input": {
                    "recipient": "unknown", "content": "Other task"}}]}}
        ]
        data = extract_prompts.extract([json.dumps(record) for record in records])
        self.assertEqual(len(data["agents"]), 1)
        self.assertEqual(data["agents"][0]["prompt"], "Implement parser")
        self.assertEqual(data["agents"][0]["followups"][0]["message"], "Also test empty input")
        self.assertEqual(data["unassigned_followups"][0]["target"], "unknown")
        with tempfile.TemporaryDirectory() as temp:
            extract_prompts.write_outputs(data, Path(temp))
            recovered = (Path(temp) / "001_Build_parser.txt").read_text()
            self.assertIn("ORIGINAL PROMPT\n\nImplement parser", recovered)
            self.assertIn("Also test empty input", recovered)


class LauncherAndPreviewTests(unittest.TestCase):
    def test_launcher_creates_isolated_worktree_and_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "README").write_text("baseline\n")
            subprocess.run(["git", "-C", str(repo), "add", "README"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c",
                            "user.email=none", "commit", "-qm", "initial"], check=True)
            prompt = root / "task.txt"
            prompt.write_text("Create a file\n")
            codex = root / "codex"
            codex.write_text("#!/bin/sh\nwhile [ $# -gt 0 ]; do\n"
                             "  if [ \"$1\" = -o ]; then shift; printf 'returned\\n' > \"$1\"; exit 0; fi\n"
                             "  shift\ndone\nexit 1\n")
            codex.chmod(0o755)
            env = {**os.environ, "ORCH_REPO": str(repo), "ORCH_WORKTREES": str(root / "trees"),
                   "ORCH_OUTPUT_DIR": str(root / "jobs"), "ORCH_BOARD": str(root / "board.md"),
                   "ORCH_CODEX_BIN": str(codex), "ORCH_FILES": "src/new.py"}
            result = subprocess.run([str(SCRIPTS / "launch_codex.sh"), "task01", str(prompt)],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "trees/task01/.git").exists())
            self.assertIn("task01 | START | orch/task01 | src/new.py", (root / "board.md").read_text())
            output = root / "jobs/task01.out"
            for _ in range(100):
                if output.exists() and output.stat().st_size:
                    break
                import time
                time.sleep(0.01)
            self.assertEqual(output.read_text(), "returned\n")

    def test_rebuild_reattaches_preview_after_output_is_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "preview-source"
            source.mkdir()
            (source / "index.html").write_text("preview")
            site = root / "site"
            build = root / "build.sh"
            build.write_text("#!/bin/sh\nrm -rf \"$ORCH_SITE_DIR\"\nmkdir -p \"$ORCH_SITE_DIR\"\nprintf site > \"$ORCH_SITE_DIR/index.html\"\n")
            build.chmod(0o755)
            manifest = root / "previews.tsv"
            manifest.write_text(f"sample\t{source}\n")
            env = {**os.environ, "ORCH_REPO": str(root), "ORCH_SITE_DIR": str(site),
                   "ORCH_BUILD_CMD": str(build), "ORCH_PREVIEWS_FILE": str(manifest)}
            for _ in range(2):
                result = subprocess.run([str(SCRIPTS / "rebuild_with_previews.sh")], env=env,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((site / "preview/sample/index.html").read_text(), "preview")

    def test_pid_killer_previews_then_signals_only_matching_process(self):
        marker = f"orchestra_test_[{os.getpid()}]"
        command = [sys.executable, "-u", "-c",
                   "import time; print('ready', flush=True); time.sleep(120)"]
        child = subprocess.Popen([*command, marker], stdout=subprocess.PIPE, text=True)
        other = subprocess.Popen([*command, "unrelated_job"], stdout=subprocess.PIPE, text=True)
        try:
            for process in (child, other):
                ready, _, _ = select.select([process.stdout], [], [], 30)
                self.assertTrue(ready, "child did not start")
                self.assertEqual(process.stdout.readline(), "ready\n")
            preview = subprocess.run([str(SCRIPTS / "kill_jobs.sh"), marker],
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn(f"would send TERM to {child.pid}", preview.stdout)
            self.assertNotIn(f"to {other.pid} (", preview.stdout)
            self.assertIsNone(child.poll())
            self.assertIsNone(other.poll())
            actual = subprocess.run([str(SCRIPTS / "kill_jobs.sh"), marker, "--execute"],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(actual.returncode, 0, actual.stderr)
            child.wait(timeout=30)
            self.assertEqual(child.returncode, -15)
            self.assertIsNone(other.poll())
        finally:
            for process in (child, other):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=30)
                process.stdout.close()

    def test_contact_sheet_tiles_images(self):
        from PIL import Image

        sheet = load("contact_sheet")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(3):
                Image.new("RGB", (100, 50), (index * 40, 0, 0)).save(root / f"{index}.png")
            output = root / "sheet.png"
            sheet.build_sheet(sorted(root.glob("[0-9].png")), output, columns=2, thumb_width=100)
            with Image.open(output) as result:
                self.assertEqual(result.size, (200, 160))


if __name__ == "__main__":
    unittest.main()
