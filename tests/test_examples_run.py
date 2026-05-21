from tools.run_examples import OFFICIAL_EXAMPLES, run_examples


def test_official_examples_run(capsys):
    assert "hello.sona" in OFFICIAL_EXAMPLES
    assert "calculator.sona" in OFFICIAL_EXAMPLES
    assert run_examples(verbose=False) == 0

    output = capsys.readouterr().out
    assert f"Running {len(OFFICIAL_EXAMPLES)} examples..." in output
    assert "OK hello.sona" in output
    assert "All examples passed." in output
