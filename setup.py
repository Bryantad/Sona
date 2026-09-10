#!/usr/bin/env python3
"""Package build customization for reviewed example assets.

The canonical package metadata lives in pyproject.toml.
"""

import json
from pathlib import Path, PurePosixPath

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithExamples(build_py):
    """Copy manifest-declared sources, without a second maintained source copy."""

    def run(self):
        super().run()
        root = Path(__file__).resolve().parent
        manifest = json.loads((root / "sona/data/examples.json").read_text(encoding="utf-8"))
        assets = {entry["source"] for entry in manifest["examples"]}
        assets.update(asset for entry in manifest["examples"] for asset in entry["assets"])
        self.example_outputs = []
        for name in sorted(assets):
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                raise ValueError("Unsafe example asset in build manifest")
            source = (root / "examples" / name).resolve(strict=True)
            source.relative_to((root / "examples").resolve(strict=True))
            target = Path(self.build_lib) / "sona/_examples" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            self.example_outputs.append(str(target))

    def get_outputs(self, include_bytecode=1):
        return super().get_outputs(include_bytecode) + getattr(self, "example_outputs", [])


setup(cmdclass={"build_py": BuildWithExamples})
