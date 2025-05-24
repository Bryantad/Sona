from sona.interpreter import run_code

with open('comprehensive_v0.5.0_test.sona', 'r') as f:
    run_code(f.read(), debug_enabled=True)
