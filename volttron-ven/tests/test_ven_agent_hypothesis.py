import pytest
from hypothesis import given, strategies as st, assume
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ven_agent
import math

@given(st.floats(min_value=0.0, max_value=100.0), st.floats(min_value=0.0, max_value=100.0))
def test_next_power_reading_range(min_kw, max_kw):
    assume(min_kw <= max_kw)
    ven_agent._meter_base_min_kw = min_kw
    ven_agent._meter_base_max_kw = max_kw
    result = ven_agent._next_power_reading()
    tol = 0.01
    assert (min_kw - tol) <= result <= (max_kw + tol)

@given(st.floats(min_value=1.0, max_value=300.0), st.floats(min_value=0.0, max_value=0.5))
def test_next_voltage_reading_range(nominal, jitter):
    ven_agent._voltage_nominal = nominal
    ven_agent._voltage_jitter_pct = jitter
    result = ven_agent._next_voltage_reading()
    assert result >= 1.0
    # If jitter is zero, allow for floating point tolerance
    # Compute expected bounds using same rounding as simulation
    lower = round(max(1.0, nominal * (1.0 - jitter)), 1)
    upper = round(max(1.0, nominal * (1.0 + jitter)), 1)
    assert lower <= result <= upper
