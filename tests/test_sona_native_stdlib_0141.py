import json
from pathlib import Path

import pytest

from sona.interpreter import SonaFunction, SonaUnifiedInterpreter


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "sona" / "stdlib" / "MANIFEST.json"


def call(fn, *args):
    if hasattr(fn, "call"):
        return fn.call(list(args), {})
    return fn(*args)


def load(name):
    interp = SonaUnifiedInterpreter(project_root=ROOT)
    return interp, interp.module_system.import_module(name)


def manifest_entries():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return data, {entry["name"]: entry for entry in data["modules"]}


def test_smod_foundation_importability():
    interp = SonaUnifiedInterpreter(project_root=ROOT)
    modules = [
        "queue", "stack", "sort", "search", "statistics", "matrix",
        "graph", "permissions", "hashing", "random", "uuid", "secrets",
        "password", "jwt", "crypto",
    ]
    for name in modules:
        module = interp.module_system.import_module(name)
        assert module.__name__.endswith(name)


def test_queue_and_stack_empty_behavior():
    _, queue = load("queue")
    q = call(queue.create)
    assert call(queue.dequeue, q) is None
    assert call(queue.peek, q) is None
    call(queue.enqueue, q, 1)
    call(queue.enqueue, q, 2)
    assert call(queue.drain, q) == [1, 2]

    _, stack = load("stack")
    s = call(stack.create)
    assert call(stack.pop, s) is None
    assert call(stack.peek, s) is None
    call(stack.push, s, 1)
    call(stack.push, s, 2)
    assert call(stack.to_list, s) == [2, 1]
    assert call(stack.pop, s) == 2


def test_queue_priority_and_transform_helpers():
    _, queue = load("queue")
    q = call(queue.from_list, [1, 2, 3])
    assert call(queue.to_list, call(queue.reverse, q)) == [3, 2, 1]
    assert call(queue.batch_dequeue, q, 2) == [1, 2]
    assert call(queue.to_list, q) == [3]

    other = call(queue.from_list, [3, 4])
    assert call(queue.to_list, call(queue.merge_queues, q, other)) == [3, 3, 4]
    assert call(queue.to_list, call(queue.filter_queue, other, lambda value: value > 3)) == [4]
    assert call(queue.to_list, call(queue.map_queue, other, lambda value: value * 2)) == [6, 8]

    priority = call(queue.create_priority)
    call(priority["enqueue"], priority, "low", 3)
    call(priority["enqueue"], priority, "first", 1)
    call(priority["enqueue"], priority, "second", 1)
    assert call(priority["peek"], priority) == "first"
    assert [call(priority["dequeue"], priority) for _ in range(4)] == [
        "first", "second", "low", None,
    ]
    call(priority["enqueue"], priority, "reset", 2)
    call(priority["clear"], priority)
    assert call(priority["is_empty"], priority) is True
    assert call(priority["size"], priority) == 0


def test_stack_transform_helpers():
    _, stack = load("stack")
    s = call(stack.from_list, [1, 2, 3])
    assert call(stack.contains, s, 2) is True
    assert call(stack.search, s, 3) == 0
    assert call(stack.to_list, call(stack.reverse, s)) == [1, 2, 3]
    assert call(stack.to_list, call(stack.filter_stack, s, lambda value: value > 1)) == [3, 2]
    assert call(stack.to_list, call(stack.map_stack, s, lambda value: value * 2)) == [6, 4, 2]


def test_sort_and_search_correctness():
    _, sort = load("sort")
    assert call(sort.sort, [3, 1, 2]) == [1, 2, 3]
    assert call(sort.quicksort, [3, 1, 2]) == [1, 2, 3]
    assert call(sort.mergesort, [3, 1, 2]) == [1, 2, 3]
    assert call(sort.stable_sort, [3, 1, 2]) == [1, 2, 3]
    assert call(sort.reverse_sort, [3, 1, 2]) == [3, 2, 1]
    assert call(sort.top_k, [3, 1, 4, 2], 2) == [4, 3]
    assert call(sort.bottom_k, [3, 1, 4, 2], 2) == [1, 2]
    assert call(sort.is_sorted, [1, 2, 3]) is True
    assert call(sort.natural_sort, ["b", "a"]) == ["a", "b"]
    assert call(sort.sort_by_frequency, [1, 2, 2, 3, 2, 1]) == [2, 2, 2, 1, 1, 3]

    _, search = load("search")
    assert call(search.binary_search, [1, 2, 3, 4], 3) == 2
    assert call(search.linear_search, ["a", "b"], "b") == 1
    assert call(search.index_of, [4, 1, 4], 1) == 1
    assert call(search.find_all, [1, 2, 1, 3], 1) == [0, 2]
    assert call(search.contains, [1, 2], 2) is True
    assert call(search.find_first, [1, 2, 3], lambda value: value > 1) == 2
    assert call(search.find_last, [1, 2, 3], lambda value: value < 3) == 2
    assert call(search.find_min, [4, 2, 3]) == 2
    assert call(search.find_max, [4, 2, 3]) == 4
    assert call(search.contains_any, [1, 2], [4, 2]) is True
    assert call(search.contains_all, [1, 2], [2, 1]) is True
    assert call(search.fuzzy_match, "Sona Native", "snt") is True
    assert call(search.levenshtein_distance, "kitten", "sitting") == 3
    assert call(search.levenshtein_distance, "", "abc") == 3


def test_statistics_results_and_edge_cases():
    _, statistics = load("statistics")
    assert call(statistics.count, [1, 2, 3]) == 3
    assert call(statistics.sum_values, [1, 2, 3]) == pytest.approx(6.0)
    assert call(statistics.mean, [1, 2, 3]) == pytest.approx(2.0)
    assert call(statistics.median, [3, 1, 2]) == 2
    assert call(statistics.median_low, [1, 2, 3, 4]) == 2
    assert call(statistics.median_high, [1, 2, 3, 4]) == 3
    assert call(statistics.min, [1, 2, 3, 4]) == 1
    assert call(statistics.max, [1, 2, 3, 4]) == 4
    assert call(statistics.range, [1, 2, 3, 4]) == 3
    assert call(statistics.range_value, [2, 5]) == 3
    assert call(statistics.variance, [1, 2, 3]) == pytest.approx(2 / 3)
    assert call(statistics.stdev, [1, 2, 3]) == pytest.approx((2 / 3) ** 0.5)
    assert call(statistics.pvariance, [1, 2, 3, 4]) == pytest.approx(1.25)
    assert call(statistics.pstdev, [1, 2, 3, 4]) == pytest.approx(1.25 ** 0.5)
    assert call(statistics.quantile, [1, 2, 3, 4], 0.5) == pytest.approx(2.5)
    assert call(statistics.quantiles, [1, 2, 3, 4], 4) == pytest.approx([1.75, 2.5, 3.25])
    assert call(statistics.correlation, [1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
    assert call(statistics.mode, [1, 2, 2, 3]) == 2
    assert call(statistics.geometric_mean, [1, 4]) == pytest.approx(2.0)
    assert call(statistics.harmonic_mean, [1, 2]) == pytest.approx(4 / 3)
    assert call(statistics.z_score, 4, [1, 2, 3, 4]) == pytest.approx(1.3416407865)
    assert call(statistics.mean, []) is None
    assert call(statistics.range, []) is None
    assert call(statistics.variance, [1], True) is None
    assert call(statistics.quantile, [1, 2], 2) is None
    assert call(statistics.geometric_mean, [-1, 4]) is None
    assert call(statistics.harmonic_mean, [0, 2]) is None


def test_matrix_determinant_minor_and_helpers():
    _, matrix = load("matrix")
    mat = call(matrix.create, [[1, 2], [3, 4]])
    mat3 = call(matrix.create, [[6, 1, 1], [4, -2, 5], [2, 8, 7]])
    assert call(matrix.identity, 2)["data"] == [[1, 0], [0, 1]]
    assert call(matrix.zeros, 2, 3)["data"] == [[0, 0, 0], [0, 0, 0]]
    assert call(matrix.ones, 1, 2)["data"] == [[1, 1]]
    assert call(matrix.diagonal, [2, 3])["data"] == [[2, 0], [0, 3]]
    assert call(matrix.determinant, mat) == pytest.approx(-2)
    assert call(matrix.determinant, mat3) == pytest.approx(-306)
    assert call(matrix._get_minor, [[1, 2, 3], [4, 5, 6], [7, 8, 9]], 0, 1) == [[4, 6], [7, 9]]
    assert call(matrix.flatten, mat) == [1, 2, 3, 4]
    assert call(matrix.trace, mat) == 5
    assert call(matrix.dot, [1, 2, 3], [4, 5, 6]) == 32
    assert call(matrix.norm, [3, 4]) == pytest.approx(5.0)
    assert call(mat["get"], mat, 0, 1) == 2
    call(mat["set"], mat, 0, 1, 9)
    assert call(mat["to_list"], mat) == [[1, 9], [3, 4]]
    assert call(mat["add"], mat, call(matrix.create, [[5, 6], [7, 8]]))["data"] == [[6, 15], [10, 12]]
    assert call(mat["transpose"], mat)["data"] == [[1, 3], [9, 4]]
    assert call(mat["scalar_multiply"], mat, 2)["data"] == [[2, 18], [6, 8]]
    assert call(matrix.reshape, mat, 1, 4)["data"] == [[1, 9, 3, 4]]


def test_graph_traversal_and_paths():
    _, graph = load("graph")
    g = call(graph.create, False)
    call(g["add_edge"], g, "A", "B")
    call(g["add_edge"], g, "B", "C")
    assert call(g["neighbors"], g, "B") == ["A", "C"]
    assert call(graph.bfs, g, "A") == ["A", "B", "C"]
    assert call(graph.dfs, g, "A") == ["A", "B", "C"]
    assert call(g["shortest_path"], g, "A", "C") == ["A", "B", "C"]
    assert call(g["has_edge"], g, "A", "B") is True
    assert call(g["get_weight"], g, "A", "B") == 1
    assert call(graph.degree, g, "B") == 2
    assert call(graph.is_connected, g) is True
    assert call(graph.find_components, g) == [["A", "B", "C"]]
    assert call(graph.dijkstra, g, "A") == [
        {"node": "A", "distance": 0},
        {"node": "B", "distance": 1},
        {"node": "C", "distance": 2},
    ]

    directed = call(graph.create, True)
    call(directed["add_edge"], directed, "A", "B")
    call(directed["add_edge"], directed, "B", "C")
    assert call(graph.topological_sort, directed) == ["A", "B", "C"]

    restored = call(graph.from_dict, {"directed": True, "nodes": ["X", "Y"], "edges": []})
    assert restored["nodes"] == ["X", "Y"]


def test_permissions_manager_behavior():
    _, permissions = load("permissions")
    manager = call(permissions.create_manager)
    read = call(manager["define_permission"], manager, "read", "Read access")
    role = call(manager["create_role"], manager, "reader", ["read"])
    user = call(manager["create_user"], manager, "user-1", ["reader"], [])
    assert read["name"] == "read"
    assert role["name"] == "reader"
    assert user["id"] == "user-1"
    assert call(manager["check"], manager, "user-1", "read") is True
    assert call(manager["check"], manager, "user-1", "write") is False
    call(user["remove_role"], user, role)
    assert call(manager["check"], manager, "user-1", "read") is False


def test_hashing_random_uuid_and_secrets_wrappers():
    _, hashing = load("hashing")
    assert call(hashing.sha256, "abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert len(call(hashing.sha512, "abc")) == 128
    assert call(hashing.hash, "abc") == call(hashing.sha256, "abc")
    assert len(call(hashing.hmac_sha256, "key", "abc")) == 64
    assert call(hashing.digest, "abc", {"algorithm": "sha512"}) == call(hashing.sha512, "abc")
    assert call(hashing.md5, "abc") is None

    _, random = load("random")
    call(random.seed, 123)
    first = call(random.randint, 1, 100)
    call(random.seed, 123)
    assert call(random.randint, 1, 100) == first
    assert call(random.choice, []) is None
    source = [1, 2, 3]
    shuffled = call(random.shuffle, source)
    assert source == [1, 2, 3]
    assert sorted(shuffled) == [1, 2, 3]
    assert len(call(random.sample, source, 2)) == 2
    assert 1.0 <= call(random.uniform, 1.0, 2.0) <= 2.0
    assert len(call(random.choices, ["a", "b"], {"k": 3})) == 3
    assert len(call(random.randbytes, 4)) == 4
    assert isinstance(call(random.coin_flip), bool)
    assert 1 <= call(random.dice, 6) <= 6

    _, uuid = load("uuid")
    value = call(uuid.v4)
    assert call(uuid.is_valid, value) is True
    assert len(value) == 36
    assert value[8] == value[13] == value[18] == value[23] == "-"
    assert call(uuid.v3, uuid.NAMESPACE_DNS, "sona")[14] == "3"
    assert call(uuid.v5, uuid.NAMESPACE_DNS, "sona")[14] == "5"
    assert call(uuid.from_bytes, call(uuid.to_bytes, value)) == value
    assert len(call(uuid.short)) == 8
    assert call(uuid.nil) == "00000000-0000-0000-0000-000000000000"

    _, secrets = load("secrets")
    assert call(secrets.choice, []) is None
    assert len(call(secrets.token_hex, 4)) == 8
    assert len(call(secrets.token_urlsafe, 4)) == 6
    assert 0 <= call(secrets.randbelow, 10) < 10
    assert 0 <= call(secrets.randbits, 16) <= 65535
    secret_source = [1, 2, 3]
    assert sorted(call(secrets.shuffle, secret_source)) == secret_source
    assert secret_source == [1, 2, 3]
    assert call(secrets.compare, "same", "same") is True
    assert call(secrets.compare, "same", "different") is False


def test_password_and_jwt_verification_paths():
    _, password = load("password")
    hashed = call(password.hash, "secret")
    assert call(password.verify, "secret", hashed) is True
    assert call(password.verify, "wrong", hashed) is False
    assert len(call(password.generate, 12)) == 12
    assert call(password.strength, "ValidPass123!")["score"] >= 4
    assert call(password.validate_policy, "ValidPass123!") is True
    assert len(call(password.generate_memorable, 3).split("-")) == 3
    assert call(password.is_weak, "password") is True

    _, jwt = load("jwt")
    token = call(jwt.create_token, "user-1", "secret", 60)
    assert call(jwt.verify_token, token, "secret") == "user-1"
    assert call(jwt.verify_token, token, "bad") is None
    expired = call(jwt.create_token, "user-2", "secret", -1)
    assert call(jwt.verify_token, expired, "secret") is None
    assert call(jwt.is_expired, expired) is True
    assert call(jwt.get_payload_unverified, token)["sub"] == "user-1"
    refreshed = call(jwt.refresh_token, token, "secret", 60)
    assert call(jwt.verify_token, refreshed, "secret") == "user-1"


def test_crypto_preview_wrapper_behavior():
    _, crypto = load("crypto")
    assert call(crypto.hash, "abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert len(call(crypto.hash, "abc", "sha512")) == 128
    assert len(call(crypto.hmac, "key", "abc")) == 64
    assert len(call(crypto.random_bytes, 4)) == 4
    assert len(call(crypto.random_token, 4)) == 64
    assert len(call(crypto.random_string, 6)) == 6
    assert call(crypto.compare_digest, "same", "same") is True
    encrypted = call(crypto.encrypt_simple, "abc", "legacy-key")
    assert call(crypto.decrypt_simple, encrypted, "legacy-key") == "abc"
    assert len(call(crypto.derive_key, "password", "salt", 1, 8)) == 16
    assert call(crypto.hash_file, "not-supported") is None


def test_manifest_source_and_stability_classifications():
    data, entries = manifest_entries()
    assert data["version"] == "0.15.1"
    assert data["manifest_hash"] == "0150_cognitive_runtime_guardian"
    assert {entry["source"] for entry in data["modules"]} <= {"sona", "sona+intrinsic", "intrinsic"}

    for name in ["queue", "stack", "sort", "search", "statistics", "matrix", "graph", "permissions"]:
        assert entries[name]["source"] == "sona"
        assert entries[name]["stability"] == "core"

    for name in ["hashing", "random", "uuid", "secrets", "password", "jwt", "crypto"]:
        assert entries[name]["source"] == "sona+intrinsic"

    assert entries["intrinsics"]["source"] == "intrinsic"
    assert entries["intrinsics"]["user_facing"] is False


def test_private_intrinsics_and_native_bridge_are_hidden():
    interp = SonaUnifiedInterpreter(project_root=ROOT)
    for name in ["intrinsics", "native_intrinsics", "native_bridge"]:
        with pytest.raises(ImportError):
            interp.module_system.import_module(name)

    data, entries = manifest_entries()
    user_facing = {
        entry["name"]
        for entry in data["modules"]
        if entry.get("user_facing", True) and not entry["name"].startswith("native")
    }
    assert "intrinsics" not in user_facing
    assert "native_bridge" not in user_facing


def test_sona_source_modules_use_sona_functions_not_python_legacy():
    for name, public in {
        "queue": "create",
        "stack": "create",
        "sort": "sort",
        "search": "binary_search",
        "statistics": "mean",
        "matrix": "create",
        "graph": "create",
        "permissions": "create_manager",
    }.items():
        _, module = load(name)
        assert isinstance(getattr(module, public), SonaFunction)
