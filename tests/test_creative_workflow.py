import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/agent-orchestra/scripts"


class LeadRoutingTests(unittest.TestCase):
    def test_subscription_then_gateway_at_threshold_and_arguments(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("subscription", "gateway"):
                script = root / name
                script.write_text(f"#!/bin/sh\nprintf '%s\\n' {name}\nprintf '%s\\n' \"$@\"\n")
                script.chmod(0o755)
            env = {**os.environ, "ORCH_SUBSCRIPTION_CLAUDE": str(root / "subscription"),
                   "ORCH_API_CLAUDE": str(root / "gateway")}
            for usage, expected in (("79", "subscription"), ("80", "gateway"), ("100", "gateway")):
                result = subprocess.run([str(SCRIPTS / "route_lead.sh"), "-p", "hello world"],
                                        env={**env, "ORCH_WEEKLY_USAGE_PERCENT": usage},
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [expected, "-p", "hello world"])

    def test_invalid_quota_missing_gateway_and_timeout_are_errors(self):
        for settings in ({"ORCH_WEEKLY_USAGE_PERCENT": "none"},
                         {"ORCH_WEEKLY_USAGE_PERCENT": "101"},
                         {"ORCH_WEEKLY_USAGE_PERCENT": "80"},
                         {"ORCH_WEEKLY_USAGE_PERCENT": "0", "ORCH_LEAD_TIMEOUT": "invalid"}):
            env = {**os.environ, "ORCH_API_CLAUDE": "", **settings}
            result = subprocess.run([str(SCRIPTS / "route_lead.sh"), "-p", "task"],
                                    env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_lead_job_is_bounded_by_timeout(self):
        with tempfile.TemporaryDirectory() as temp:
            sleeper = Path(temp) / "sleeper"
            sleeper.write_text("#!/bin/sh\nexec sleep 10\n")
            sleeper.chmod(0o755)
            result = subprocess.run([str(SCRIPTS / "route_lead.sh"), "-p", "task"],
                                    env={**os.environ, "ORCH_WEEKLY_USAGE_PERCENT": "0",
                                         "ORCH_SUBSCRIPTION_CLAUDE": str(sleeper),
                                         "ORCH_LEAD_TIMEOUT": "0.1s"},
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 124)

    def test_worker_launcher_omits_git_grant_in_no_commit_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "README").write_text("baseline\n")
            subprocess.run(["git", "-C", str(repo), "add", "README"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test",
                            "-c", "user.email=none", "commit", "-qm", "initial"], check=True)
            prompt = root / "task.txt"
            prompt.write_text("Implement scene\n")
            codex = root / "codex"
            codex.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$ORCH_CAPTURE\"\n")
            codex.chmod(0o755)
            capture = root / "argv.txt"
            env = {**os.environ, "ORCH_REPO": str(repo),
                   "ORCH_WORKTREES": str(root / "trees"),
                   "ORCH_OUTPUT_DIR": str(root / "jobs"), "ORCH_BOARD": str(root / "board.md"),
                   "ORCH_CODEX_BIN": str(codex), "ORCH_CAPTURE": str(capture),
                   "ORCH_WORKER_NO_COMMIT": "1", "ORCH_JOB_TIMEOUT": "1h"}
            result = subprocess.run([str(SCRIPTS / "launch_codex.sh"), "scene", str(prompt)],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for _ in range(100):
                if capture.exists():
                    break
                time.sleep(0.01)
            self.assertTrue(capture.exists())
            self.assertNotIn(str(repo / ".git"), capture.read_text())
            self.assertIn("exec\n", capture.read_text())


class RenderRequestTests(unittest.TestCase):
    def run_service(self, root, command):
        return subprocess.run([
            sys.executable, str(SCRIPTS / "render_requests.py"), "--once",
            "--worktrees", str(root / "trees"), "--requests", str(root / "requests"),
            "--output", str(root / "frames"), "--render-command", command,
        ], capture_output=True, text=True, timeout=10)

    def test_renders_allowed_worktree_and_both_sheets(self):
        try:
            __import__("PIL")
        except ImportError:
            self.skipTest("Pillow is optional; install the images extra")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tree = root / "trees/scene01"
            tree.mkdir(parents=True)
            request_dir = root / "requests"
            request_dir.mkdir()
            (request_dir / "scene01.json").write_text(json.dumps({
                "worktree": str(tree), "times": [0, 1.5], "themes": ["light", "dark"],
            }))
            renderer = root / "renderer.py"
            renderer.write_text(
                "import sys\nfrom pathlib import Path\nfrom PIL import Image\n"
                "args = sys.argv[1:]\nassert args[1] == '--at'\n"
                "breakpoint = args.index('--themes')\n"
                "for theme in args[breakpoint + 1:]:\n"
                "    target = Path(args[0]) / theme\n    target.mkdir(parents=True)\n"
                "    for index, time in enumerate(args[2:breakpoint]):\n"
                "        Image.new('RGB', (40, 30), (index * 90, 0, 0)).save(target / f'at-{index}.png')\n"
            )
            result = self.run_service(root, f"{sys.executable} {renderer}")
            self.assertEqual(result.returncode, 0, result.stderr)
            output = root / "frames/scene01"
            self.assertEqual((output / "DONE").read_text(), "ok\n")
            self.assertFalse((output / "ERROR").exists())
            for theme in ("light", "dark"):
                self.assertTrue((output / f"sheet-{theme}.png").is_file())
            self.assertTrue((request_dir / "scene01.json.handled").exists())

    def test_rejects_outside_worktree_and_invalid_times_without_rendering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "trees").mkdir()
            (root / "outside").mkdir()
            requests = root / "requests"
            requests.mkdir()
            for name, spec in (
                ("outside", {"worktree": str(root / "outside"), "times": [1]}),
                ("root", {"worktree": str(root / "trees"), "times": [1]}),
                ("bad-time", {"worktree": str(root / "trees"), "times": [-1]}),
                ("bad-theme", {"worktree": str(root / "trees"), "times": [1],
                               "themes": ["other"]}),
            ):
                (requests / f"{name}.json").write_text(json.dumps(spec))
            result = self.run_service(root, "/bin/false")
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ("outside", "root", "bad-time", "bad-theme"):
                self.assertTrue((root / f"frames/{name}/ERROR").exists())
                self.assertFalse((root / f"frames/{name}/DONE").exists())

    def test_renderer_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "trees/scene").mkdir(parents=True)
            (root / "requests").mkdir()
            (root / "requests/scene.json").write_text(json.dumps({
                "worktree": str(root / "trees/scene"), "times": [1],
            }))
            result = self.run_service(root, "/bin/false")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("render exited", (root / "frames/scene/ERROR").read_text())


if __name__ == "__main__":
    unittest.main()
