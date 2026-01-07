import textwrap

from sona.interpreter import SonaUnifiedInterpreter


def test_basic_arithmetic():
    code = textwrap.dedent(
        """
        let x = 40;
        let y = 2;
        x + y
        """
    ).strip()

    result = SonaUnifiedInterpreter().interpret(code)

    assert result == 42


def test_import_math_module():
    code = textwrap.dedent(
        """
        import math;
        math.sqrt(25)
        """
    ).strip()

    result = SonaUnifiedInterpreter().interpret(code)

    assert result == 5.0
