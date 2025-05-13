import math as _py
import pytest
import stdlib.math as m

def test_sin_cos_tan():
    assert pytest.approx(m.sin(_py.pi/2), rel=1e-6) == 1
    assert pytest.approx(m.cos(0),        rel=1e-6) == 1
    assert pytest.approx(m.tan(0),        rel=1e-6) == 0

def test_sqrt_and_pow():
    assert m.sqrt(9) == 3
    assert m.pow(2, 3) == 8

def test_log_variants():
    # natural log
    assert pytest.approx(m.log(_py.e),   rel=1e-6) == 1
    # base‑10 log
    assert pytest.approx(m.log10(100),   rel=1e-6) == 2

def test_floor_and_ceil():
    assert m.floor(3.7) == 3
    assert m.ceil(3.2)  == 4

def test_abs_and_exp():
    assert pytest.approx(m.abs(-3.5), rel=1e-6) == _py.fabs(-3.5)
    assert pytest.approx(m.exp(1),   rel=1e-6) == _py.e

def test_hypot_and_gcd():
    assert pytest.approx(m.hypot(3, 4), rel=1e-6) == 5
    # gcd should match Python's
    assert m.gcd(54, 24) == _py.gcd(54, 24)

def test_factorial_and_edge_cases():
    assert m.factorial(5) == 120
    with pytest.raises(ValueError):
        m.factorial(-1)       # Python’s math.factorial rejects negative

def test_round_trip_power():
    # make sure pow and exp/log are inverses
    for base, exponent in [(2,5), (10,0.3), (_py.e, 1.7)]:
        assert pytest.approx(m.pow(base, exponent), rel=1e-6) == base**exponent
        # test using log and exp
        assert pytest.approx(m.exp(m.log(base)), rel=1e-6) == base
