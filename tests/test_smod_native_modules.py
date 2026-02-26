import textwrap

from sona.interpreter import SonaUnifiedInterpreter


def _run(code: str):
    return SonaUnifiedInterpreter().interpret(textwrap.dedent(code).strip())


def test_queue_module_loads_via_smod_and_behaves():
    result = _run(
        """
        import queue;
        let q = queue.Queue();
        queue.enqueue(q, "first");
        q.enqueue("second");
        let popped = queue.dequeue(q);
        [popped, q.size(), queue.module_format]
        """
    )

    assert result == ["first", 1, "smod-runtime"]


def test_stack_module_loads_via_smod_and_behaves():
    result = _run(
        """
        import stack;
        let s = stack.Stack();
        s.push(10);
        stack.push(s, 20);
        let popped = stack.pop(s);
        [popped, stack.peek(s), stack.module_format]
        """
    )

    assert result == [20, 10, "smod-runtime"]


def test_random_module_loads_via_smod_and_seed_is_stable():
    result = _run(
        """
        import random;
        random.seed(42);
        let a = random.randint(1, 100);
        let b = random.randint(1, 100);
        random.seed(42);
        let c = random.randint(1, 100);
        let d = random.randint(1, 100);
        [a, b, c, d, random.module_format]
        """
    )

    assert result[0] == result[2]
    assert result[1] == result[3]
    assert result[4] == "smod-runtime"


def test_uuid_module_loads_via_smod_and_behaves():
    result = _run(
        """
        import uuid;
        let id = uuid.uuid4();
        let deterministic_a = uuid.v5(uuid.NAMESPACE_DNS, "sona");
        let deterministic_b = uuid.v5(uuid.NAMESPACE_DNS, "sona");
        [
            uuid.is_valid(id),
            len(id),
            deterministic_a == deterministic_b,
            uuid.is_valid(deterministic_a),
            uuid.module_format
        ]
        """
    )

    assert result == [True, 36, True, True, "smod-runtime"]


def test_regex_module_loads_via_smod_and_core_search_works():
    result = _run(
        """
        import regex;
        let found = regex.search("fox", "the fox jumps");
        let escaped = regex.escape("a+b");
        [
            found["matched"],
            found["span"][0],
            found["span"][1],
            escaped,
            regex.module_format
        ]
        """
    )

    assert result == [True, 4, 7, "a\\\\+b", "smod-runtime"]


def test_hashing_module_loads_via_smod_and_sha256_matches_vectors():
    result = _run(
        """
        import hashing;
        [
            hashing.module_format,
            hashing.runtime_backend,
            hashing.sha256(""),
            hashing.sha256("abc"),
            hashing.sha256("hello world"),
            hashing.sha256("Sona 0.10.0")
        ]
        """
    )

    assert result == [
        "smod-runtime",
        "smod-bridge",
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
        "645ffa69eaa33316aef5e1b49e66325e995bfdbe64351dc1dbabe840054e3c71",
    ]
