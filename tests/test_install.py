"""Installer integration checks use isolated profiles, never the real user home."""

from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import install


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex 설치 ")
        self.base = Path(self.temporary.name)
        self.source = self.base / "source bundle"
        self.home = self.base / "개인 profile"
        self.codex = self.home / ".codex"
        self.put(self.source / "skills/alpha/SKILL.md", b"---\nname: alpha\n---\nPersonal skill.\n")
        self.put(self.source / "skills/alpha/helper.py", b"print('hello')\n")
        self.put(self.source / "codex/AGENTS.md", b"Respect existing personal policies.\n")
        self.put(self.source / "scripts/install.py", b"")

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def put(path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    def plan(self, guidance=False):
        return install.plan_install(self.source, self.home, self.codex, guidance)

    def cli(self, args, environment=None):
        output = io.StringIO()
        with patch.object(install, "__file__", str(self.source / "scripts/install.py")), patch.dict(os.environ, environment or {}, clear=True), redirect_stdout(output), redirect_stderr(output):
            status = install.main(args)
        return status, output.getvalue()

    def test_default_preview_makes_no_profile_or_files(self):
        status, output = self.cli(["--home", str(self.home), "--with-guidance"])
        self.assertEqual(status, 0, output)
        self.assertIn("PREVIEW", output)
        self.assertFalse(self.home.exists())

    def test_apply_installs_resources_and_is_idempotent(self):
        writes, unchanged = self.plan()
        self.assertEqual(unchanged, 0)
        self.assertIsNone(install.apply(writes, self.codex))
        self.assertEqual((self.home / ".agents/skills/alpha/helper.py").read_bytes(), b"print('hello')\n")
        again, unchanged = self.plan()
        self.assertEqual(again, [])
        self.assertEqual(unchanged, 2)
        self.assertIsNone(install.apply(again, self.codex))
        self.assertFalse((self.codex / "backups").exists())

    def test_personal_skills_are_opt_in_and_install_resources(self):
        self.put(self.source / "personal-skills/beta/SKILL.md", b"---\nname: beta\n---\nOptional personal skill.\n")
        self.put(self.source / "personal-skills/beta/references/guide.md", b"Keep the reference.\n")
        status, preview = self.cli(["--home", str(self.home)])
        self.assertEqual(status, 0, preview)
        self.assertNotIn("beta", preview)
        self.assertFalse(self.home.exists())
        status, output = self.cli(["--home", str(self.home), "--with-personal-skills", "--apply"])
        self.assertEqual(status, 0, output)
        self.assertEqual((self.home / ".agents/skills/beta/references/guide.md").read_bytes(), b"Keep the reference.\n")
        status, output = self.cli(["--home", str(self.home), "--with-personal-skills"])
        self.assertEqual(status, 0, output)
        self.assertIn("Changed files: 0;", output)

    def test_personal_bundle_duplicate_name_aborts_before_writes(self):
        self.put(self.source / "personal-skills/alpha/SKILL.md", b"A conflicting source.")
        with self.assertRaisesRegex(install.InstallError, "Duplicate source skill"):
            install.plan_install(self.source, self.home, self.codex, with_personal_skills=True)
        self.assertFalse(self.home.exists())

    def test_missing_personal_bundle_reports_error_without_writes(self):
        with self.assertRaisesRegex(install.InstallError, "Personal skill source"):
            install.plan_install(self.source, self.home, self.codex, with_personal_skills=True)
        self.assertFalse(self.home.exists())

    def test_existing_unique_legacy_skill_is_reused(self):
        legacy = self.codex / "skills/alpha/SKILL.md"
        self.put(legacy, (self.source / "skills/alpha/SKILL.md").read_bytes())
        writes, _ = self.plan()
        install.apply(writes, self.codex)
        self.assertTrue((legacy.parent / "helper.py").is_file())
        self.assertFalse((self.home / ".agents/skills/alpha").exists())

    def test_duplicate_installations_abort_before_any_writes(self):
        self.put(self.source / "skills/zeta/SKILL.md", b"Zeta")
        self.put(self.home / ".agents/skills/zeta/SKILL.md", b"Zeta")
        self.put(self.codex / "skills/zeta/SKILL.md", b"Zeta")
        with self.assertRaisesRegex(install.InstallError, "Duplicate skill 'zeta'"):
            self.plan()
        self.assertFalse((self.home / ".agents/skills/alpha").exists())
        self.assertFalse((self.codex / "backups").exists())

    def test_conflict_requires_replace_and_backups_preserve_original(self):
        destination = self.codex / "skills/alpha/SKILL.md"
        self.put(destination, b"My modified original\r\n")
        extra = destination.parent / "private-notes.txt"
        self.put(extra, b"Keep this")
        writes, _ = self.plan()
        with self.assertRaisesRegex(install.InstallError, "--replace"):
            install.apply(writes, self.codex)
        self.assertEqual(destination.read_bytes(), b"My modified original\r\n")
        self.assertFalse((destination.parent / "helper.py").exists())
        self.assertFalse((self.codex / "backups").exists())
        backup = install.apply(writes, self.codex, replace=True)
        self.assertIsNotNone(backup)
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        saved = next(item for item in manifest if item["destination"] == str(destination))
        self.assertEqual((backup / saved["backup"]).read_bytes(), b"My modified original\r\n")
        self.assertEqual(extra.read_bytes(), b"Keep this")

    def test_guidance_preserves_user_content_bom_newlines_and_config(self):
        user = b"\xef\xbb\xbf# My preferences\r\nUse Korean.\r\n"
        self.put(self.codex / "AGENTS.md", user)
        config = b'[plugins.example]\nenabled = true\n'
        self.put(self.codex / "config.toml", config)
        writes, _ = self.plan(guidance=True)
        backup = install.apply(writes, self.codex)
        actual = (self.codex / "AGENTS.md").read_bytes()
        self.assertTrue(actual.startswith(user))
        self.assertNotIn(b"\n", actual.replace(b"\r\n", b""))
        self.assertEqual(actual.count(install.BEGIN.encode()), 1)
        self.assertEqual((self.codex / "config.toml").read_bytes(), config)
        self.assertTrue((backup / "manifest.json").is_file())
        self.assertEqual(self.plan(guidance=True)[0], [])

    def test_existing_managed_guidance_change_requires_replace(self):
        install.apply(self.plan(guidance=True)[0], self.codex)
        self.put(self.source / "codex/AGENTS.md", b"Updated personal policies.\n")
        writes, _ = self.plan(guidance=True)
        with self.assertRaisesRegex(install.InstallError, "--replace"):
            install.apply(writes, self.codex)
        install.apply(writes, self.codex, replace=True)
        self.assertIn("Updated personal policies.", (self.codex / "AGENTS.md").read_text(encoding="utf-8"))

    def test_broken_guidance_markers_abort_without_installing_skills(self):
        self.put(self.codex / "AGENTS.md", install.BEGIN.encode())
        with self.assertRaisesRegex(install.InstallError, "markers"):
            self.plan(guidance=True)
        self.assertFalse((self.home / ".agents/skills/alpha").exists())

    def test_explicit_home_ignores_inherited_codex_home(self):
        unrelated = self.base / "actual live profile"
        status, output = self.cli(["--home", str(self.home), "--apply", "--with-guidance"], {"CODEX_HOME": str(unrelated)})
        self.assertEqual(status, 0, output)
        self.assertTrue((self.codex / "AGENTS.md").exists())
        self.assertFalse(unrelated.exists())

    def test_codex_home_environment_and_explicit_override(self):
        environment_home = self.base / "environment codex"
        explicit = self.base / "selected codex"
        with patch.object(Path, "home", return_value=self.home):
            status, output = self.cli(["--apply", "--with-guidance"], {"CODEX_HOME": str(environment_home)})
        self.assertEqual(status, 0, output)
        self.assertTrue((environment_home / "AGENTS.md").exists())
        status, output = self.cli(["--home", str(self.home), "--codex-home", str(explicit), "--apply", "--with-guidance"], {"CODEX_HOME": str(environment_home)})
        self.assertEqual(status, 0, output)
        self.assertTrue((explicit / "AGENTS.md").exists())

    def test_concurrent_destination_change_is_not_overwritten(self):
        writes, _ = self.plan()
        destination = writes[0].path
        self.put(destination, b"Written by another process")
        with self.assertRaisesRegex(install.InstallError, "changed after preview"):
            install.apply(writes, self.codex, replace=True)
        self.assertEqual(destination.read_bytes(), b"Written by another process")

    def test_linked_profile_is_refused(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.home.mkdir()
        link = self.home / ".agents"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            if os.name != "nt":
                self.skipTest(f"Symlink creation unavailable: {error}")
            # Junctions require no developer-mode privilege on Windows.
            quoted_link = str(link).replace("'", "''")
            quoted_target = str(outside).replace("'", "''")
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                 f"$ErrorActionPreference = 'Stop'; New-Item -ItemType Junction -Path '{quoted_link}' -Target '{quoted_target}' | Out-Null"],
                capture_output=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        try:
            with self.assertRaisesRegex(install.InstallError, "symlink or reparse"):
                self.plan()
            self.assertEqual(list(outside.iterdir()), [])
        finally:
            # Remove the known link itself, never traverse into its target.
            if link.is_symlink():
                link.unlink()
            else:
                link.rmdir()


if __name__ == "__main__":
    unittest.main()
