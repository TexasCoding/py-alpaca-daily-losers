import hypothesis.strategies as st
import pytest
from hypothesis import given

from alpaca_daily_losers.calc import square


@given(x=st.one_of(st.integers(), st.floats(allow_nan=False)))
def test_on_valid_input(x):
    assert square(x) == (x * x)


def test_for_nan():
    with pytest.raises(ValueError):
        square(float("NaN"))


@pytest.mark.parametrize("x", ["text", None, [42], (9, 1, 1), {"key": "value"}])
def test_for_invalid_types(x):
    with pytest.raises(TypeError):
        square(x)
