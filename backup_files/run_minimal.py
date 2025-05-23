from sona.interpreter import run_code

with open('func_test.sona', 'r') as f:
    run_code(f.read(), debug_enabled=True)
