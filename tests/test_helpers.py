"""Focused native-Windows helper tests; never commit or modify a real profile."""

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
SDD = ROOT / "skills" / "subagent-driven-development" / "scripts"
COMPANION = ROOT / "skills" / "brainstorming" / "scripts"


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FORMATTER = load_script("optional_formatter", ROOT / "hooks" / "clang-format" / "post-tool-use.py")
STOPPER = load_script("companion_stopper", COMPANION / "stop-server.py")


def run_script(path, *args, cwd, **kwargs):
    env = os.environ.copy()
    # Force the Korean legacy locale even when the test runner uses UTF-8.
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "cp949"
    # The elevated clone is owned by the desktop user, not the sandbox user.
    count = int(env.get("GIT_CONFIG_COUNT", "0"))
    env[f"GIT_CONFIG_KEY_{count}"] = "safe.directory"
    env[f"GIT_CONFIG_VALUE_{count}"] = ROOT.as_posix()
    env["GIT_CONFIG_COUNT"] = str(count + 1)
    return subprocess.run(
        [sys.executable, str(path), *map(str, args)], cwd=cwd, env=env,
        text=True, encoding="utf-8", errors="replace", capture_output=True,
        timeout=30, **kwargs,
    )


class NativeHelpersTests(unittest.TestCase):
    def test_task_brief_ignores_fenced_task_and_preserves_unicode(self):
        with tempfile.TemporaryDirectory(prefix="도우미 🧪 공간 ") as temporary:
            root = Path(temporary)
            plan = root / "계획 파일.md"
            output = root / "결과 파일.md"
            plan.write_text(
                "# Plan\n## Task 1: 첫 작업\n본문\n```markdown\n## Task 2: example only\n```\n"
                "### Task 2: second\nbody\n## Task 11: different task\n", encoding="utf-8",
            )
            result = run_script(SDD / "task-brief", plan, 1, output, cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            content = output.read_text(encoding="utf-8")
            self.assertIn("첫 작업", content)
            self.assertIn("example only", content)
            self.assertNotIn("second", content)
            self.assertNotIn("different task", content)

    def test_missing_task_does_not_truncate_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, output = root / "plan.md", root / "out.md"
            plan.write_text("## Task 11: eleven\n", encoding="utf-8")
            output.write_text("keep me", encoding="utf-8")
            result = run_script(SDD / "task-brief", plan, 1, output, cwd=root)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep me")

    def test_default_workspace_is_per_worktree_and_self_ignored(self):
        with tempfile.TemporaryDirectory(prefix="작업 🧪 공간 ") as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
            result = run_script(SDD / "sdd-workspace", cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            workspace = Path(result.stdout.strip())
            self.assertEqual(workspace, root.resolve() / ".superpowers" / "sdd")
            self.assertEqual((workspace / ".gitignore").read_text(encoding="utf-8"), "*\n")
            (workspace / "report.md").write_text("scratch", encoding="utf-8")
            ignored = subprocess.run(["git", "check-ignore", "--quiet", str(workspace / "report.md")], cwd=root)
            self.assertEqual(ignored.returncode, 0)

    def test_workspace_help_is_non_mutating_outside_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = run_script(SDD / "sdd-workspace", "--help", cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(any(root.iterdir()))

    def test_review_existing_revision_and_reject_option_injection(self):
        with tempfile.TemporaryDirectory(prefix="리뷰 공간 ") as temporary:
            output = Path(temporary) / "리뷰.diff"
            result = run_script(SDD / "review-package", "HEAD", "HEAD", output, cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("## Diff", output.read_text(encoding="utf-8"))
            self.assertIn("0 commit(s)", result.stdout)
            bad = run_script(SDD / "review-package", "--", "--help", "HEAD", output, cwd=ROOT)
            self.assertEqual(bad.returncode, 2)

    def test_polluter_handles_unicode_test_paths_without_a_shell(self):
        with tempfile.TemporaryDirectory(prefix="오염 테스트 ") as temporary:
            root = Path(temporary)
            (root / "1 clean.py").write_text("pass\n", encoding="utf-8")
            (root / "2 오염.py").write_text("from pathlib import Path\nPath('pollution').touch()\n", encoding="utf-8")
            result = run_script(
                ROOT / "skills" / "systematic-debugging" / "find-polluter.py",
                "pollution", "*.py", "--command", sys.executable, cwd=root,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("2 오염.py", result.stdout)
            self.assertTrue((root / "pollution").is_file())

    def test_formatter_apply_patch_and_legacy_payload(self):
        with tempfile.TemporaryDirectory(prefix="포맷 공간 ") as temporary:
            root = Path(temporary)
            (root / ".clang-format").write_text("BasedOnStyle: LLVM\n", encoding="utf-8")
            code = root / "한글 🧪 파일.cpp"
            code.write_text("int main(){}\n", encoding="utf-8")
            patch = "*** Begin Patch\n*** Update File: 한글 🧪 파일.cpp\n@@\n-old\n+new\n*** End Patch\n"
            with mock.patch.object(FORMATTER.shutil, "which", return_value="clang-format"), mock.patch.object(FORMATTER.subprocess, "run") as run:
                self.assertEqual(FORMATTER.format_files({"cwd": str(root), "tool_input": {"input": patch}}), 1)
                run.assert_called_once_with(["clang-format", "-i", str(code.resolve())], check=True, cwd=root.resolve())
                run.reset_mock()
                self.assertEqual(FORMATTER.format_files({"cwd": str(root), "tool_input": {"file_path": str(code)}}), 1)
                self.assertEqual(run.call_count, 1)
                run.reset_mock()
                self.assertEqual(FORMATTER.format_files({"cwd": str(root), "tool_input": {"command": patch}}), 1)
                self.assertEqual(run.call_count, 1)
                run.reset_mock()
                serialized = json.dumps({"command": patch}, ensure_ascii=False)
                self.assertEqual(FORMATTER.format_files({"cwd": str(root), "tool_input": serialized}), 1)
                self.assertEqual(run.call_count, 1)
            self.assertEqual(FORMATTER.format_files({"tool_input": {}}), 0)

    def test_formatter_reads_utf8_event_under_cp949_stream(self):
        payload = {"cwd": "C:/작업 🧪", "tool_input": {"command": "*** Update File: 한글 🧪.cpp"}}
        stream = io.TextIOWrapper(io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8")), encoding="cp949")
        with mock.patch.object(sys, "stdin", stream), mock.patch.object(sys, "stdout", io.StringIO()), mock.patch.object(FORMATTER, "format_files", return_value=0) as formatter:
            self.assertEqual(FORMATTER.main(), 0)
            formatter.assert_called_once_with(payload)

    def test_formatter_rejects_outside_paths_before_any_formatting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.object(FORMATTER.subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    FORMATTER.format_files({"cwd": str(root), "tool_input": {"file_path": "../outside.cpp"}})
                run.assert_not_called()

    def test_stopper_preserves_metadata_when_identity_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            state = session / "state"
            state.mkdir()
            (state / "server.pid").write_text("12345\n", encoding="ascii")
            (state / "server-instance-id").write_text("a" * 43, encoding="ascii")
            with mock.patch.object(sys, "argv", ["stop-server.py", str(session)]), mock.patch.object(sys, "stdout", io.StringIO()), mock.patch.object(STOPPER, "process_alive", return_value=True), mock.patch.object(STOPPER, "command_line", return_value=""), mock.patch.object(STOPPER.os, "kill") as kill:
                self.assertEqual(STOPPER.main(), 1)
                kill.assert_not_called()
            self.assertTrue((state / "server.pid").is_file())
            self.assertTrue((state / "server-instance-id").is_file())
            with mock.patch.object(sys, "argv", ["stop-server.py", str(session)]), mock.patch.object(sys, "stdout", io.StringIO()), mock.patch.object(STOPPER, "process_alive", side_effect=PermissionError("access denied")), mock.patch.object(STOPPER.os, "kill") as kill:
                self.assertEqual(STOPPER.main(), 1)
                kill.assert_not_called()
            self.assertTrue((state / "server.pid").is_file())

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed for the optional companion")
    def test_companion_authentication_and_native_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix="화면 테스트 ") as temporary:
            root = Path(temporary)
            result = run_script(COMPANION / "start-server.py", "--project-dir", root, "--background", cwd=root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            info = json.loads(result.stdout)
            state = Path(info["state_dir"])
            try:
                origin = info["url"].split("?", 1)[0]
                with self.assertRaises(urllib.error.HTTPError) as blocked:
                    urllib.request.urlopen(origin, timeout=3)
                self.assertEqual(blocked.exception.code, 403)
                with urllib.request.urlopen(info["url"], timeout=3) as response:
                    self.assertEqual(response.status, 200)
            finally:
                stopped = run_script(COMPANION / "stop-server.py", state.parent, cwd=root)
                self.assertEqual(stopped.returncode, 0, stopped.stdout + stopped.stderr)
                self.assertEqual(json.loads(stopped.stdout)["status"], "stopped")
            self.assertFalse((state / "server.pid").exists())
            self.assertTrue((state / "server-stopped").is_file())


if __name__ == "__main__":
    unittest.main()
