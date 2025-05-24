from sona.interpreter import run_code

# Define a minimal test for function scoping
minimal_test = """
func add(a, b) {
    return a + b
}

print("Result: " + add(3, 4))
"""

# Run the test
run_code(minimal_test, debug_enabled=True)
