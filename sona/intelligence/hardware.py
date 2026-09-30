"""Best-effort host inventory for model preflight; never a resource guarantee."""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from typing import ClassVar

from .contracts import HardwareProfile
from .llama_cpp_runtime import discover_runtime


def _physical_memory_bytes() -> int | None:
    if sys.platform == "win32":

        class _MemoryStatusEx(ctypes.Structure):
            _fields_: ClassVar[list[tuple[str, object]]] = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = _MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        try:
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullTotalPhys)
        except (AttributeError, OSError):
            return None
        return None

    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", encoding="ascii") as source:
                for line in source:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) * 1024
        except (OSError, ValueError, IndexError):
            return None
        return None

    if sys.platform == "darwin":
        sysctl = shutil.which("sysctl")
        if sysctl is None:
            return None
        try:
            result = subprocess.run(
                [sysctl, "-n", "hw.memsize"],
                capture_output=True,
                check=False,
                text=True,
                timeout=1.5,
            )
            return int(result.stdout.strip()) if result.returncode == 0 else None
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return None
    return None


def _cpu_model() -> str | None:
    value = platform.processor().strip() or os.environ.get("PROCESSOR_IDENTIFIER", "").strip()
    if value:
        return value
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo", encoding="ascii", errors="replace") as source:
                for line in source:
                    if line.lower().startswith(("model name", "hardware")):
                        _, model = line.split(":", 1)
                        return model.strip() or None
        except (OSError, ValueError):
            return None
    return None


def _nvidia_accelerator() -> tuple[str | None, int | None]:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None, None
    try:
        result = subprocess.run(
            [
                executable,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    if result.returncode != 0:
        return None, None
    first = next((line.strip() for line in result.stdout.splitlines() if line.strip()), None)
    if first is None or "," not in first:
        return None, None
    name, memory_mib = (part.strip() for part in first.rsplit(",", 1))
    try:
        memory_bytes = int(memory_mib) * 1024 * 1024
    except ValueError:
        memory_bytes = None
    return name or "NVIDIA GPU", memory_bytes


def discover_hardware_profile(*, runtime_available: bool | None = None) -> HardwareProfile:
    """Collect small, local, read-only probes; unknown facts remain unset."""
    if runtime_available is None:
        runtime = discover_runtime()
        runtime_available = runtime.available and runtime.cpu_supported
    accelerator_name, accelerator_memory = _nvidia_accelerator()
    accelerator = "nvidia-cuda" if accelerator_name is not None else None
    if (
        accelerator is None
        and sys.platform == "darwin"
        and platform.machine().lower()
        in {
            "arm64",
            "aarch64",
        }
    ):
        accelerator = "apple-silicon-unified"
        accelerator_name = "Apple Silicon (unified memory)"
    runtimes = ("llama-cpp",) if runtime_available else ()
    return HardwareProfile(
        cpu_model=_cpu_model(),
        logical_cpu_count=os.cpu_count(),
        physical_memory_bytes=_physical_memory_bytes(),
        accelerator=accelerator,
        accelerator_name=accelerator_name,
        accelerator_memory_bytes=accelerator_memory,
        supported_runtimes=runtimes,
        observed_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
