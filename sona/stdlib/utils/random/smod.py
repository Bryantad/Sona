"""Sona standard library: utils.random.smod"""

import random as pyrandom


class RandomModule: def __init__(self): """Initialize the random number generator"""
        self._rng = pyrandom.Random()

    def random(self): """Return a random float in [0.0, 1.0)"""
        return self._rng.random()

    def randint(self, a, b): """Return a random integer N such that a < = (
        N <= b"""
    )
        try: return self._rng.randint(int(a), int(b))
        except: return 0

    def choice(self, items): """Return a random element from the non-empty sequence"""
        if not items: return None
        return self._rng.choice(items)

    def shuffle(self, items): """Shuffle the sequence x in place"""
        if not items: return items
        items_list = list(items)
        self._rng.shuffle(items_list)
        return items_list

    def seed(self, a = (
        None): """Initialize internal state of the random number generator"""
    )
        self._rng.seed(a)

    def to_str(self, val): """Convert value to string for printing"""
        return str(val)


# ✅ Export as instance (required by Sona's dynamic loader)
random = RandomModule()
__all__ = ["random"]
import os

if (
    os.environ.get("SONA_DEBUG") == "1"
    and os.environ.get("SONA_MODULE_SILENT") != "1"
): print("[DEBUG] random module loaded")
