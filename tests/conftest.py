from __future__ import annotations

import os
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def write_gguf():
    """Write a tiny structurally valid GGUF v3 file for metadata/runtime tests."""

    def write(
        path: Path,
        *,
        architecture: str = "llama",
        model_name: str = "Sona test model",
        context_length: int = 8192,
        file_type: int = 15,
        version: int = 3,
        tensor: bool = True,
        tensor_offset: int = 0,
        tensor_dimensions: int = 1,
        with_tokenizer_array: bool = False,
    ) -> Path:
        def encoded_string(value: str) -> bytes:
            raw = value.encode("utf-8")
            return struct.pack("<Q", len(raw)) + raw

        metadata = [
            encoded_string("general.architecture")
            + struct.pack("<I", 8)
            + encoded_string(architecture),
            encoded_string("general.name")
            + struct.pack("<I", 8)
            + encoded_string(model_name),
            encoded_string(f"{architecture}.context_length")
            + struct.pack("<I", 10)
            + struct.pack("<Q", context_length),
            encoded_string("general.file_type")
            + struct.pack("<I", 4)
            + struct.pack("<I", file_type),
        ]
        if with_tokenizer_array:
            metadata.append(
                encoded_string("tokenizer.ggml.tokens")
                + struct.pack("<I", 9)
                + struct.pack("<IQ", 8, 2)
                + encoded_string("token")
                + encoded_string("izer")
            )
        payload = bytearray(b"GGUF")
        payload.extend(struct.pack("<IQQ", version, int(tensor), len(metadata)))
        for item in metadata:
            payload.extend(item)
        if tensor:
            payload.extend(encoded_string("token_embd.weight"))
            payload.extend(struct.pack("<I", tensor_dimensions))
            payload.extend(struct.pack("<" + "Q" * tensor_dimensions, *([1] * tensor_dimensions)))
            payload.extend(struct.pack("<IQ", 0, tensor_offset))
            payload.extend(b"\0" * ((-len(payload)) % 32))
            payload.extend(b"\0\0\0\0")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    return write


@pytest.fixture(scope="session")
def native_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the real locked Native CLI once for cross-implementation gates."""

    cargo = shutil.which("cargo")
    assert cargo is not None, "cargo is mandatory for the active native gates"
    target = tmp_path_factory.mktemp("native-target")
    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = str(target)
    environment["SONA_SOURCE_COMMIT"] = "1" * 40
    process = subprocess.run(
        [
            cargo,
            "build",
            "--manifest-path",
            str(ROOT / "native" / "Cargo.toml"),
            "--release",
            "--locked",
            "-p",
            "sona-cli",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
        timeout=180,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    binary = target / "release" / ("sona.exe" if os.name == "nt" else "sona")
    assert binary.is_file()
    return binary
