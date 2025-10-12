"""
Quick validation test for collection.* namespace modules.
Tests that the modules can be imported and basic functions work.
"""

import sys
from pathlib import Path

# Add sona to path
sona_path = Path(__file__).parent / "sona"
if str(sona_path) not in sys.path:
    sys.path.insert(0, str(sona_path))

from sona.stdlib.collection import list as clist
from sona.stdlib.collection import dict as cdict
from sona.stdlib.collection import set as cset
from sona.stdlib.collection import tuple as ctuple


def test_collection_list():
    """Test collection.list functions"""
    # Test chunk
    assert clist.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert clist.chunk("hello", 2) == ["he", "ll", "o"]
    
    # Test flatten
    assert clist.flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]
    
    # Test unique
    assert clist.unique([1, 2, 1, 3, 2]) == [1, 2, 3]
    
    # Test window
    assert clist.window([1, 2, 3, 4, 5], 3) == [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
    assert clist.window([1, 2, 3, 4, 5], 2, step=2) == [[1, 2], [3, 4]]
    
    print("✅ collection.list tests passed")


def test_collection_dict():
    """Test collection.dict functions"""
    # Test safe_get
    d = {"a": 1, "b": 2}
    assert cdict.safe_get(d, "a") == 1
    assert cdict.safe_get(d, "c", 0) == 0
    
    # Test merge
    assert cdict.merge({"x": 1}, {"y": 2}) == {"x": 1, "y": 2}
    assert cdict.merge({"x": 1}, {"x": 2})["x"] == 2  # prefer_right
    assert cdict.merge({"x": 1}, {"x": 2}, "prefer_left")["x"] == 1
    
    # Test remap
    assert cdict.remap({"a": 1, "b": 2}, {"a": "x"}) == {"x": 1, "b": 2}
    
    print("✅ collection.dict tests passed")


def test_collection_set():
    """Test collection.set functions"""
    # Test union
    assert cset.union([1, 2], [2, 3]) == [1, 2, 3]
    assert cset.union([1, 2], [3, 4], [5, 6]) == [1, 2, 3, 4, 5, 6]
    
    # Test intersect
    assert cset.intersect([1, 2, 3], [2, 3, 4]) == [2, 3]
    assert cset.intersect([1, 2], [2, 3], [2, 4]) == [2]
    
    # Test diff
    assert cset.diff([1, 2, 3], [2, 3, 4]) == [1]
    assert cset.diff([1, 2], [3, 4]) == [1, 2]
    
    print("✅ collection.set tests passed")


def test_collection_tuple():
    """Test collection.tuple functions"""
    # Test zipn
    assert ctuple.zipn([1, 2, 3], ["a", "b", "c"]) == [(1, "a"), (2, "b"), (3, "c")]
    assert ctuple.zipn([1, 2], [10, 20, 30]) == [(1, 10), (2, 20)]
    
    # Test unzip
    assert ctuple.unzip([(1, "a"), (2, "b")]) == [[1, 2], ["a", "b"]]
    assert ctuple.unzip([(1, 2, 3), (4, 5, 6)]) == [[1, 4], [2, 5], [3, 6]]
    
    # Test head_tail
    assert ctuple.head_tail((1, 2, 3)) == (1, [2, 3])
    assert ctuple.head_tail([1]) == (1, [])
    
    print("✅ collection.tuple tests passed")


if __name__ == "__main__":
    print("Testing collection.* namespace modules...")
    print()
    
    test_collection_list()
    test_collection_dict()
    test_collection_set()
    test_collection_tuple()
    
    print()
    print("🎉 All collection.* modules validated successfully!")
    print("   4/4 modules working: list, dict, set, tuple")
