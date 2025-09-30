"""Array utilities for Sona programs."""

from __future__ import annotations

import os
from typing import Any


class ArrayModule:
    def __init__(self) -> None:
        self._arrays: dict[int, list[Any]] = {}
        self._counter = 0

    def new(self) -> int:
        self._counter += 1
        self._arrays[self._counter] = []
        return self._counter

    def get(self, array_id: int, index: int) -> Any:
        array = self._require(array_id)
        return array[index]

    def set(self, array_id: int, index: int, value: Any) -> Any:
        array = self._require(array_id)
        if index < 0:
            raise IndexError("Negative index not allowed")
        while index >= len(array):
            array.append(None)
        array[index] = value
        return value

    def push(self, array_id: int, value: Any) -> int:
        array = self._require(array_id)
        array.append(value)
        return len(array)

    def pop(self, array_id: int) -> Any:
        array = self._require(array_id)
        if not array:
            raise IndexError("Cannot pop from empty array")
        return array.pop()

    def length(self, array_id: int) -> int:
        array = self._require(array_id)
        return len(array)

    def to_list(self, array_id: int) -> list[Any]:
        array = self._require(array_id)
        return array.copy()

    def _require(self, array_id: int) -> list[Any]:
        if array_id not in self._arrays:
            raise ValueError(f"Array {array_id} does not exist")
        return self._arrays[array_id]


array = ArrayModule()
__all__ = ["array"]


if (
    os.environ.get("SONA_DEBUG") == "1"
    and os.environ.get("SONA_MODULE_SILENT") != "1"
):
    print("[DEBUG] array module loaded")
