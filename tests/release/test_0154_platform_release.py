from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tools.release import platform_release_0154 as release

METADATA = (
    b"Metadata-Version: 2.1\n"
    b"Name: sona-lang\n"
    b"Version: 0.15.4\n"
    b"Requires-Python: >=3.11,<3.13\n"
    b"\n"
)


class PlatformReleaseTests(unittest.TestCase):
    def _portable_fixtures(self, root: Path, epoch: int = 1_700_000_000) -> tuple[Path, Path, Path]:
        wheel = root / release.WHEEL_NAME
        release._write_zip(
            wheel,
            [
                ("sona/stdlib/MANIFEST.json", b'{"version":"0.15.4"}\n', 0o644),
                ("sona_lang-0.15.4.dist-info/METADATA", METADATA, 0o644),
            ],
            epoch=epoch,
        )
        sdist = root / release.SDIST_NAME
        release._write_tar_gz(
            sdist,
            [
                ("sona_lang-0.15.4/PKG-INFO", METADATA, 0o644),
                ("sona_lang-0.15.4/sona/__init__.py", b'__version__ = "0.15.4"\n', 0o644),
            ],
            epoch=epoch,
        )
        vsix = root / release.VSIX_NAME
        package = json.dumps(
            {
                "name": "sona-ai-native-programming",
                "version": "0.15.4",
                "main": "./out/extension.js",
            },
            sort_keys=True,
        ).encode("utf-8")
        release._write_zip(
            vsix,
            [
                ("extension/assets/icon.png", b"png", 0o644),
                ("extension/out/extension.js", b"module.exports = {};\n", 0o644),
                ("extension/package.json", package, 0o644),
            ],
            epoch=epoch,
        )
        return wheel, sdist, vsix

    def test_exact_desktop_matrix_and_artifact_names(self) -> None:
        self.assertEqual(
            set(release.NATIVE_SPECS),
            {
                ("windows", "x86_64"),
                ("linux", "x86_64"),
                ("linux", "aarch64"),
                ("macos", "x86_64"),
                ("macos", "aarch64"),
            },
        )
        self.assertEqual(len(release.NATIVE_ASSETS), 5)
        self.assertIn("sona-native-0.15.4-macos-aarch64.tar.gz", release.NATIVE_ASSETS)
        self.assertIn("sona-native-0.15.4-linux-aarch64-musl.tar.gz", release.NATIVE_ASSETS)

    def test_native_archives_are_deterministic_single_executable_packages(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            binary = root / "input-binary"
            binary.write_bytes(b"synthetic-sona-native")
            for spec in release.NATIVE_SPECS.values():
                first_dir = root / "first" / spec.platform / spec.architecture
                second_dir = root / "second" / spec.platform / spec.architecture
                first_dir.mkdir(parents=True)
                second_dir.mkdir(parents=True)
                first = first_dir / spec.archive_name
                second = second_dir / spec.archive_name
                release._build_native_archive(binary, spec, first, 1_700_000_000)
                release._build_native_archive(binary, spec, second, 1_700_000_000)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                inspection = release.inspect_native_archive(first, spec)
                self.assertEqual(inspection["members"], 1)
                self.assertEqual(inspection["binary_sha256"], release._sha256(binary))

    def test_portable_artifact_inspection_and_test_kit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            wheel, sdist, vsix = self._portable_fixtures(root)
            self.assertEqual(release.inspect_wheel(wheel)["status"], "pass")
            self.assertEqual(release.inspect_sdist(sdist)["status"], "pass")
            self.assertEqual(release.inspect_vsix(vsix)["status"], "pass")
            kit = root / release.TEST_KIT_NAME
            inspected = release._build_test_kit(kit, 1_700_000_000)
            self.assertEqual(inspected["members"], 3)

    def _assembly_input(self, root: Path) -> str:
        commit = "1" * 40
        portable = root / "portable"
        portable.mkdir()
        wheel, sdist, vsix = self._portable_fixtures(portable)
        kit = portable / release.TEST_KIT_NAME
        release._build_test_kit(kit, 1_700_000_000)
        portable_inspections = {
            release.WHEEL_NAME: release.inspect_wheel(wheel),
            release.SDIST_NAME: release.inspect_sdist(sdist),
            release.VSIX_NAME: release.inspect_vsix(vsix),
            release.TEST_KIT_NAME: {
                "status": "pass",
                "filename": release.TEST_KIT_NAME,
                "sha256": release._sha256(kit),
            },
        }
        (portable / release.PORTABLE_REPORT_NAME).write_text(
            json.dumps(
                {
                    "schema_id": release.PORTABLE_REPORT_SCHEMA,
                    "sona_version": release.VERSION,
                    "source_commit": commit,
                    "artifacts": portable_inspections,
                    "status": "pass",
                }
            ),
            encoding="utf-8",
        )
        binary = root / "synthetic-native"
        binary.write_bytes(b"synthetic-native")
        for spec in release.NATIVE_SPECS.values():
            destination = root / "native" / spec.platform / spec.architecture
            destination.mkdir(parents=True)
            archive = destination / spec.archive_name
            release._build_native_archive(binary, spec, archive, 1_700_000_000)
            inspection = release.inspect_native_archive(archive, spec)
            (destination / spec.report_name).write_text(
                json.dumps(
                    {
                        "schema_id": release.NATIVE_REPORT_SCHEMA,
                        "sona_version": release.VERSION,
                        "source_commit": commit,
                        "host": {"platform": spec.platform, "architecture": spec.architecture},
                        "target": release.asdict(spec),
                        "build": {"mode": "source"},
                        "dependency_inspection": {"status": "pass"},
                        "smoke": {"status": "pass"},
                        "artifact": inspection,
                        "status": "pass",
                    }
                ),
                encoding="utf-8",
            )
        return commit

    def test_assembly_requires_all_host_evidence_and_writes_checksum_authority(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            commit = self._assembly_input(root)
            output = root / "assembled"
            with mock.patch.object(
                release,
                "_repository_version",
                return_value=release.VERSION,
            ):
                result = release.command_assemble(
                    argparse.Namespace(input_root=root, output_dir=output)
                )
            self.assertEqual(result["source_commit"], commit)
            expected = release.RELEASE_ASSETS | {
                release.RELEASE_MANIFEST_NAME,
                "SHA256SUMS.txt",
            }
            self.assertEqual({path.name for path in output.iterdir()}, expected)
            checksum_lines = (output / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines()
            self.assertEqual(len(checksum_lines), len(expected) - 1)
            self.assertFalse(any(line.endswith("  SHA256SUMS.txt") for line in checksum_lines))
            manifest = json.loads(
                (output / release.RELEASE_MANIFEST_NAME).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema_id"], release.RELEASE_MANIFEST_SCHEMA)
            self.assertEqual(len(manifest["desktop_support"]), 5)

    def test_workflow_is_host_matched_and_does_not_publish(self) -> None:
        workflow = (release.ROOT / ".github/workflows/release-platforms-0154.yml").read_text(
            encoding="utf-8"
        )
        for fragment in (
            "windows-2025",
            "ubuntu-24.04",
            "ubuntu-24.04-arm",
            "macos-15-intel",
            "macos-15",
            "x86_64-unknown-linux-musl",
            "aarch64-unknown-linux-musl",
            "x86_64-apple-darwin",
            "aarch64-apple-darwin",
            "aarch64-linux-android",
            "aarch64-apple-ios",
            "platform_release_0154.py verify",
        ):
            self.assertIn(fragment, workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("continue-on-error: true", workflow)
        self.assertIn("needs: [portable, native, desktop-verify]", workflow)
        self.assertNotIn("needs: [portable, native, desktop-verify, mobile-compile]", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("gh release", workflow)
        self.assertNotIn("softprops/action-gh-release", workflow)


if __name__ == "__main__":
    unittest.main()
