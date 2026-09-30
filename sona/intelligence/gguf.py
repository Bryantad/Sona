"""Bounded, metadata-only reader for the GGUF v2/v3 model container."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

GGUF_SUPPORTED_VERSIONS = (2, 3)
_MAX_ENTRIES = 1_000_000
_MAX_STRING_BYTES = 1_073_741_824
_MAX_KEY_BYTES = 1_048_576
_MAX_DIMENSIONS = 4
_UINT64_MAX = (1 << 64) - 1

_SCALAR_FORMATS: dict[int, tuple[str, int]] = {
    0: ("B", 1),  # UINT8
    1: ("b", 1),  # INT8
    2: ("H", 2),  # UINT16
    3: ("h", 2),  # INT16
    4: ("I", 4),  # UINT32
    5: ("i", 4),  # INT32
    6: ("f", 4),  # FLOAT32
    7: ("B", 1),  # BOOL (validated below)
    10: ("Q", 8),  # UINT64
    11: ("q", 8),  # INT64
    12: ("d", 8),  # FLOAT64
}

_FILE_TYPES = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    4: "Q4_1_SOME_F16",
    5: "Q4_2 (removed)",
    6: "Q4_3 (removed)",
    7: "Q8_0",
    8: "Q5_0",
    9: "Q5_1",
    10: "Q2_K",
    11: "Q3_K_S",
    12: "Q3_K_M",
    13: "Q3_K_L",
    14: "Q4_K_S",
    15: "Q4_K_M",
    16: "Q5_K_S",
    17: "Q5_K_M",
    18: "Q6_K",
}


class GGUFFormatError(ValueError):
    """The file is not a structurally valid supported GGUF model container."""


@dataclass(frozen=True, slots=True)
class GGUFMetadata:
    version: int
    tensor_count: int
    metadata_key_count: int
    architecture: str
    model_name: str | None
    context_length: int | None
    file_type: int | None
    quantization: str | None
    alignment: int


def _read_exact(source: BinaryIO, count: int, file_size: int) -> bytes:
    if count < 0 or source.tell() + count > file_size:
        raise GGUFFormatError("GGUF metadata is truncated or exceeds the file boundary")
    result = source.read(count)
    if len(result) != count:
        raise GGUFFormatError("GGUF metadata is truncated")
    return result


def _unpack(source: BinaryIO, fmt: str, file_size: int) -> int | float:
    size = struct.calcsize("<" + fmt)
    return struct.unpack("<" + fmt, _read_exact(source, size, file_size))[0]


def _read_string(source: BinaryIO, file_size: int, *, decode: bool) -> str | None:
    length = int(_unpack(source, "Q", file_size))
    if length > _MAX_STRING_BYTES or source.tell() + length > file_size:
        raise GGUFFormatError("GGUF string length is invalid or exceeds the file boundary")
    if not decode:
        source.seek(length, 1)
        return None
    if length > _MAX_KEY_BYTES:
        raise GGUFFormatError("GGUF metadata key or selected string exceeds the inspection limit")
    try:
        return _read_exact(source, length, file_size).decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GGUFFormatError("GGUF metadata contains a non-UTF-8 string") from exc


def _read_value(
    source: BinaryIO,
    value_type: int,
    file_size: int,
    *,
    capture: bool,
) -> int | float | str | None:
    if value_type == 8:  # STRING
        return _read_string(source, file_size, decode=capture)
    if value_type == 9:  # ARRAY
        element_type = int(_unpack(source, "I", file_size))
        count = int(_unpack(source, "Q", file_size))
        if count > _MAX_ENTRIES or element_type == 9:
            raise GGUFFormatError("GGUF metadata array exceeds the supported inspection bounds")
        if element_type == 8:
            for _ in range(count):
                _read_string(source, file_size, decode=False)
        else:
            scalar = _SCALAR_FORMATS.get(element_type)
            if scalar is None:
                raise GGUFFormatError("GGUF metadata contains an unknown array element type")
            byte_count = scalar[1] * count
            if byte_count > file_size - source.tell():
                raise GGUFFormatError("GGUF metadata array is truncated")
            source.seek(byte_count, 1)
        return None
    scalar = _SCALAR_FORMATS.get(value_type)
    if scalar is None:
        raise GGUFFormatError("GGUF metadata contains an unknown value type")
    if capture:
        value = _unpack(source, scalar[0], file_size)
        if value_type == 7 and value not in (0, 1):
            raise GGUFFormatError("GGUF boolean metadata must be encoded as zero or one")
        if value_type == 7:
            return bool(value)
        return value
    source.seek(scalar[1], 1)
    if source.tell() > file_size:
        raise GGUFFormatError("GGUF metadata is truncated")
    return None


def read_gguf_metadata(path: str | Path) -> GGUFMetadata:
    """Read GGUF structure and selected metadata without reading tensor weights."""
    artifact = Path(path)
    try:
        file_size = artifact.stat().st_size
        source = artifact.open("rb")
    except OSError as exc:
        raise GGUFFormatError("GGUF artifact is not readable") from exc

    with source:
        try:
            if _read_exact(source, 4, file_size) != b"GGUF":
                raise GGUFFormatError("GGUF magic is invalid")
            version = int(_unpack(source, "I", file_size))
            if version not in GGUF_SUPPORTED_VERSIONS:
                raise GGUFFormatError(
                    f"GGUF version {version} is unsupported; supported versions are 2 and 3"
                )
            tensor_count = int(_unpack(source, "Q", file_size))
            metadata_count = int(_unpack(source, "Q", file_size))
            if tensor_count > _MAX_ENTRIES or metadata_count > _MAX_ENTRIES:
                raise GGUFFormatError("GGUF entry count exceeds the supported inspection bounds")

            selected: dict[str, int | str | bool] = {}
            seen_keys: set[str] = set()
            for _ in range(metadata_count):
                key = _read_string(source, file_size, decode=True)
                if not key:
                    raise GGUFFormatError("GGUF metadata contains an empty key")
                if key in seen_keys:
                    raise GGUFFormatError("GGUF metadata contains a duplicate key")
                seen_keys.add(key)
                value_type = int(_unpack(source, "I", file_size))
                capture = key in {
                    "general.architecture",
                    "general.name",
                    "general.alignment",
                    "general.file_type",
                } or key.endswith(".context_length")
                value = _read_value(source, value_type, file_size, capture=capture)
                if key == "general.architecture":
                    if not isinstance(value, str) or not value:
                        raise GGUFFormatError("GGUF is missing a valid general.architecture string")
                    selected[key] = value
                elif key == "general.name":
                    if not isinstance(value, str):
                        raise GGUFFormatError("GGUF general.name metadata must be a string")
                    selected[key] = value
                elif key == "general.alignment":
                    if not isinstance(value, int) or isinstance(value, bool):
                        raise GGUFFormatError("GGUF general.alignment metadata must be an integer")
                    selected[key] = value
                elif key == "general.file_type":
                    if not isinstance(value, int) or isinstance(value, bool):
                        raise GGUFFormatError("GGUF general.file_type metadata must be an integer")
                    selected[key] = value
                elif key.endswith(".context_length"):
                    if not isinstance(value, int) or isinstance(value, bool):
                        raise GGUFFormatError("GGUF architecture context_length must be an integer")
                    selected[key] = value

            architecture = selected.get("general.architecture")
            if not isinstance(architecture, str) or not architecture:
                raise GGUFFormatError("GGUF is missing a valid general.architecture string")
            model_name = selected.get("general.name")
            raw_file_type = selected.get("general.file_type")

            alignment = selected.get("general.alignment", 32)
            if (
                not isinstance(alignment, int)
                or isinstance(alignment, bool)
                or alignment < 8
                or alignment & (alignment - 1)
            ):
                raise GGUFFormatError("GGUF general.alignment must be a power of two of at least 8")

            max_tensor_offset = -1
            tensor_names: set[str] = set()
            for _ in range(tensor_count):
                name = _read_string(source, file_size, decode=True)
                if not name:
                    raise GGUFFormatError("GGUF tensor has an empty name")
                if name in tensor_names:
                    raise GGUFFormatError("GGUF tensor names must be unique")
                tensor_names.add(name)
                dimension_count = int(_unpack(source, "I", file_size))
                if not 1 <= dimension_count <= _MAX_DIMENSIONS:
                    raise GGUFFormatError("GGUF tensor dimension count is unsupported")
                dimensions = [int(_unpack(source, "Q", file_size)) for _ in range(dimension_count)]
                if any(dimension == 0 for dimension in dimensions):
                    raise GGUFFormatError("GGUF tensor dimensions must be positive")
                _unpack(source, "I", file_size)  # ggml_type; kept numeric for forward compatibility
                tensor_offset = int(_unpack(source, "Q", file_size))
                if tensor_offset % alignment:
                    raise GGUFFormatError("GGUF tensor data offset violates the declared alignment")
                max_tensor_offset = max(max_tensor_offset, tensor_offset)

            metadata_end = source.tell()
            data_start = (metadata_end + alignment - 1) & ~(alignment - 1)
            if tensor_count and (
                data_start >= file_size or max_tensor_offset >= file_size - data_start
            ):
                raise GGUFFormatError("GGUF tensor data offsets exceed the artifact boundary")

            architecture_context = selected.get(f"{architecture}.context_length")
            if architecture_context is None:
                architecture_context = selected.get("llm.context_length")
            if architecture_context is not None and (
                not isinstance(architecture_context, int)
                or isinstance(architecture_context, bool)
                or architecture_context <= 0
            ):
                raise GGUFFormatError("GGUF architecture context_length must be a positive integer")

            file_type = (
                raw_file_type
                if isinstance(raw_file_type, int) and not isinstance(raw_file_type, bool)
                else None
            )
            quantization = _FILE_TYPES.get(file_type) if file_type is not None else None
            if quantization is None and file_type is not None:
                quantization = f"file_type_{file_type}"
            return GGUFMetadata(
                version=version,
                tensor_count=tensor_count,
                metadata_key_count=metadata_count,
                architecture=architecture,
                model_name=model_name if isinstance(model_name, str) else None,
                context_length=(
                    architecture_context if isinstance(architecture_context, int) else None
                ),
                file_type=file_type,
                quantization=quantization,
                alignment=alignment,
            )
        except OSError as exc:
            raise GGUFFormatError("GGUF artifact could not be read") from exc
