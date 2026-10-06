"""Physics tests: each compares the pipeline with an independent analytic result."""

import math

import numpy as np
import pytest
from scipy.optimize import brentq

from app.models import QCSERequest
from app.pipeline import (
    ConfinementError,
    compute_qcse,
    field_to_ev_per_nm,
    make_grid,
    perturbative_energies,
    solve_schrodinger,
)

# hbar^2 / (2 m_e) in eV nm^2, from CODATA 2018 values, written out independently
# of the pipeline so that a wrong constant there is caught here.
C = 0.0380998212


def infinite_well(width_nm: float):
    """Grid strictly inside an infinite well (psi = 0 at +-L/2) and its full spectrum."""
    z = make_grid(width_nm, barrier_nm=0.0)
    return z, solve_schrodinger(z, np.zeros_like(z))


def finite_well_levels(v0_ev: float, width_nm: float) -> list[float]:
    """Bound levels of a finite well from the textbook transcendental equations.

    Even states: k tan(kL/2) = kappa.  Odd states: -k cot(kL/2) = kappa.
    """

    def k(e: float) -> float:
        return math.sqrt(e / C)

    def kappa(e: float) -> float:
        return math.sqrt((v0_ev - e) / C)

    def even(e: float) -> float:
        return k(e) * math.sin(k(e) * width_nm / 2) - kappa(e) * math.cos(k(e) * width_nm / 2)

    def odd(e: float) -> float:
        return k(e) * math.cos(k(e) * width_nm / 2) + kappa(e) * math.sin(k(e) * width_nm / 2)

    # Bracket roots on a fine energy mesh (both functions are smooth in E).
    mesh = np.linspace(1e-9, v0_ev - 1e-9, 20001)
    levels = []
    for f in (even, odd):
        values = [f(e) for e in mesh]
        for a, b, fa, fb in zip(mesh[:-1], mesh[1:], values[:-1], values[1:], strict=True):
            if fa * fb < 0:
                levels.append(brentq(f, a, b, xtol=1e-14))
    return sorted(levels)


def test_infinite_well_energies_match_particle_in_a_box():
    width = 2.0
    _, states = infinite_well(width)
    for n in (1, 2, 3):
        expected = C * math.pi**2 * n**2 / width**2
        assert states.energies[n - 1] == pytest.approx(expected, rel=1e-4)


def test_infinite_well_second_order_shift_matches_closed_form():
    """Full second-order sum for the ground state of an infinite well.

    E1^(2) = -(15 - pi^2) / (24 pi^4) * m e^2 F^2 L^4 / hbar^2. Wikipedia keeps
    only the k = 2 term, -24 (2 / 3 pi)^6 (...), which is 0.14% smaller.
    """
    width = 2.0
    z, states = infinite_well(width)
    ef = field_to_ev_per_nm(500.0)
    _, e1, e2 = perturbative_energies(z, states, ef, index=0)
    m_over_hbar2 = 1.0 / (2.0 * C)
    expected = -(15 - math.pi**2) / (24 * math.pi**4) * m_over_hbar2 * ef**2 * width**4
    assert e1 == pytest.approx(0.0, abs=1e-12)
    assert e2 == pytest.approx(expected, rel=1e-3)
    wikipedia_k2_only = -24 * (2 / (3 * math.pi)) ** 6 * m_over_hbar2 * ef**2 * width**4
    assert abs(e2) > abs(wikipedia_k2_only)


def test_zero_field_energies_match_finite_well_analytic_solution():
    request = QCSERequest(v0_ev=1.0, width_nm=1.5, field_kv_cm=0.0)
    result = compute_qcse(request)
    expected = finite_well_levels(request.v0_ev, request.width_nm)
    assert len(result.states) == 2
    for state, level in zip(result.states, expected, strict=False):
        assert state.energy_ev == pytest.approx(level, rel=1e-3)
        assert state.stark_shift_ev == pytest.approx(0.0, abs=1e-12)


def test_exact_stark_shift_matches_second_order_at_weak_field():
    result = compute_qcse(QCSERequest(v0_ev=1.0, width_nm=3.0, field_kv_cm=100.0))
    for state in result.states:
        pert = state.perturbative
        assert pert is not None
        assert state.stark_shift_ev == pytest.approx(pert.second_order_ev, rel=0.02)
    ground, excited = result.states
    assert ground.stark_shift_ev < 0  # ground state is pushed down
    assert excited.stark_shift_ev > 0  # first excited state is pushed up


@pytest.mark.parametrize("field", [-1500.0, 1500.0])
def test_field_pushes_ground_state_against_the_field(field):
    result = compute_qcse(QCSERequest(v0_ev=1.0, width_nm=2.0, field_kv_cm=field))
    z = np.array(result.z_nm)
    psi = np.array(result.states[0].psi)
    dz = z[1] - z[0]
    mean_z = float(np.sum(z * psi**2) * dz)
    # H' = eFz: F > 0 raises V on the +z side, so the electron moves to -z.
    assert np.sign(mean_z) == -np.sign(field)
    assert float(np.sum(psi**2) * dz) == pytest.approx(1.0, rel=1e-9)


def test_stark_shift_is_even_in_field():
    plus = compute_qcse(QCSERequest(field_kv_cm=800.0)).states[0].energy_ev
    minus = compute_qcse(QCSERequest(field_kv_cm=-800.0)).states[0].energy_ev
    assert plus == pytest.approx(minus, rel=1e-9)


def test_potential_slopes_with_field():
    request = QCSERequest(v0_ev=1.0, width_nm=1.5, field_kv_cm=1000.0)
    result = compute_qcse(request)
    z = np.array(result.z_nm)
    v = np.array(result.potential_ev)
    inside = np.abs(z) < request.width_nm / 2
    slope = np.polyfit(z[inside], v[inside], 1)[0]
    assert slope == pytest.approx(field_to_ev_per_nm(request.field_kv_cm), rel=1e-9)


def test_shallow_narrow_well_has_one_state():
    result = compute_qcse(QCSERequest(v0_ev=0.1, width_nm=0.5, field_kv_cm=0.0))
    assert len(result.states) == 1
    assert result.notes


def test_strong_field_leaves_no_confined_state():
    with pytest.raises(ConfinementError):
        compute_qcse(QCSERequest(v0_ev=0.1, width_nm=5.0, field_kv_cm=3000.0))
