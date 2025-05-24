from sona.interpreter import run_code

with open('test_func_params.sona', 'r') as f:
    run_code(f.read(), debug_enabled=True)
