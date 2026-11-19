import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("setup", Path(__file__).parents[1] / "setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ghostty test ")
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / "config.ghostty"

    def test_roundtrip_preserves_bytes_and_unrelated_files(self):
        for original in (b"", b"font-size = 19", b"# local\r\nfont-size = 19\r\n"):
            with self.subTest(original=original):
                self.config.write_bytes(original)
                other = self.config.parent / "themes/my-theme"
                other.parent.mkdir(exist_ok=True)
                other.write_text("untouched")
                managed = setup.deploy("apply", self.config)
                first = self.config.read_bytes()
                setup.deploy("apply", self.config)
                self.assertEqual(self.config.read_bytes(), first)
                self.assertTrue(first.endswith(original))
                self.assertFalse((managed / "common.ghostty").is_symlink())
                (managed / "stale").touch()
                setup.deploy("apply", self.config)
                self.assertFalse((managed / "stale").exists())
                setup.deploy("unapply", self.config)
                setup.deploy("unapply", self.config)
                self.assertEqual(self.config.read_bytes(), original)
                self.assertFalse(managed.exists())
                self.assertEqual(other.read_text(), "untouched")

    def test_missing_config(self):
        setup.deploy("unapply", self.config)
        self.assertFalse(self.config.exists())
        setup.deploy("apply", self.config)
        setup.deploy("unapply", self.config)
        self.assertEqual(self.config.read_bytes(), b"")

    def test_symlinks_refused(self):
        target = self.config.parent / "original"
        target.write_text("untouched")
        self.config.symlink_to(target)
        with self.assertRaises(ValueError):
            setup.deploy("apply", self.config)
        self.assertEqual(target.read_text(), "untouched")
        self.config.unlink()
        (self.config.parent / "repo-managed").symlink_to(self.config.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            setup.deploy("unapply", self.config)

    def test_unapply_preserves_other_includes(self):
        local_include = b"config-file = ?local.ghostty\n"
        self.config.write_bytes(local_include)
        setup.deploy("apply", self.config)
        setup.deploy("unapply", self.config)
        self.assertEqual(self.config.read_bytes(), local_include)

    def test_macos_entry_loads_shared_then_platform_settings(self):
        managed = setup.deploy("apply", self.config, platform="darwin")
        entry_lines = (managed / "config.ghostty").read_text().splitlines()
        theme = managed / "themes" / setup.DEFAULT_THEME
        self.assertTrue(theme.is_file())
        self.assertEqual(entry_lines, [
            f"theme = {theme}",
            "config-file = common.ghostty",
            "config-file = macos.ghostty",
        ])
        self.assertTrue((managed / "macos.ghostty").is_file())

    def test_linux_omits_macos_settings(self):
        managed = setup.deploy("apply", self.config, platform="linux")
        self.assertNotIn("macos", (managed / "config.ghostty").read_text())
        self.assertFalse((managed / "macos.ghostty").exists())


if __name__ == "__main__":
    unittest.main()
