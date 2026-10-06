"""Quantum-confined Stark effect in a 1D finite square well.

Model (academic, no real material):

* An electron of free-electron mass m_e moves along z.
* The well floor is 0 eV for |z| < L/2; the barriers are V0 elsewhere.
* A uniform field F adds the perturbation H' = eFz (as on the Wikipedia page
  "Quantum-confined Stark effect"), so V(z) = V_well(z) + eFz. F > 0 raises
  the potential on the +z side and pushes the electron towards -z.

Two independent results are computed:

1. Exact (to grid accuracy): the time-independent Schrodinger equation
   -hbar^2/(2m) psi'' + V psi = E psi is discretised with second-order finite
   differences on a uniform grid that spans the well plus a barrier of
   BARRIER_NM on each side, with psi = 0 at the grid ends, and the resulting
   tridiagonal matrix is diagonalised.
2. Perturbative: Rayleigh-Schrodinger perturbation theory in eFz around the
   zero-field states, to second order. The sum over intermediate states runs
   over every eigenstate of the zero-field grid Hamiltonian, which is a
   complete basis on the grid (bound states and the discretised continuum).

The entry point used by the API is :func:`compute_qcse`.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from numpy.typing import NDArray
from scipy import constants
from scipy.linalg import eigh_tridiagonal

from app.models import BoundState, PerturbativeEnergy, QCSERequest, QCSEResponse

FloatArray = NDArray[np.float64]

# hbar^2 / (2 m_e) in eV nm^2 (about 0.0381).
HBAR2_OVER_2M_EV_NM2: float = constants.hbar**2 / (2.0 * constants.m_e) / constants.e * 1e18
# Electron charge times 1 kV/cm, in eV/nm: 1 kV/cm = 1e5 V/m = 1e-4 V/nm.
EV_PER_NM_PER_KV_CM: float = 1e-4

BARRIER_NM: float = 4.0  # barrier thickness kept on each side of the well
GRID_POINTS: int = 1600  # interior grid points
MAX_STATES: int = 2  # ground state and first excited state
CANDIDATE_STATES: int = 24  # lowest eigenstates searched for confined ones


class ConfinementError(ValueError):
    """Raised when the field is so strong that no state stays confined."""


@dataclass(frozen=True)
class Eigenstates:
    """Eigen-energies (eV, ascending) and normalised wavefunctions (columns, nm^-1/2)."""

    energies: FloatArray
    psis: FloatArray


def field_to_ev_per_nm(field_kv_cm: float) -> float:
    """Return eF in eV/nm for a field given in kV/cm."""
    return field_kv_cm * EV_PER_NM_PER_KV_CM


def make_grid(width_nm: float, barrier_nm: float = BARRIER_NM, n: int = GRID_POINTS) -> FloatArray:
    """Return n interior grid points spanning the well and a barrier on each side.

    The end points z = +-(L/2 + barrier) are excluded: psi vanishes there.
    """
    half = width_nm / 2.0 + barrier_nm
    return np.linspace(-half, half, n + 2)[1:-1]


def potential(z_nm: FloatArray, width_nm: float, v0_ev: float, efield_ev_nm: float) -> FloatArray:
    """Return V(z) in eV: 0 inside |z| < L/2, V0 outside, plus the field term eFz.

    Each grid point stands for a cell of width dz. The cell that straddles a
    well edge gets V0 weighted by the fraction of the cell outside the well, so
    the effective well width is exactly L rather than rounded to the grid.
    """
    dz = float(z_nm[1] - z_nm[0])
    half = width_nm / 2.0
    overlap = np.minimum(z_nm + dz / 2, half) - np.maximum(z_nm - dz / 2, -half)
    inside_fraction = np.clip(overlap / dz, 0.0, 1.0)
    return v0_ev * (1.0 - inside_fraction) + efield_ev_nm * z_nm


def _fix_sign(psi: FloatArray) -> FloatArray:
    """Choose the overall sign so the first appreciable lobe (from -z) is positive.

    The sign of an eigenvector is arbitrary; this keeps plots continuous as
    parameters change.
    """
    threshold = 0.1 * np.max(np.abs(psi))
    first = int(np.argmax(np.abs(psi) > threshold))
    return psi if psi[first] >= 0 else -psi


def solve_schrodinger(
    z_nm: FloatArray, v_ev: FloatArray, n_states: int | None = None
) -> Eigenstates:
    """Solve -hbar^2/(2m) psi'' + V psi = E psi on a uniform grid with psi = 0 at both ends.

    Args:
        z_nm: Uniformly spaced interior grid points, nm.
        v_ev: Potential energy at each grid point, eV.
        n_states: Number of lowest states to return; all of them if None.

    Returns:
        Energies in ascending order and wavefunctions normalised so that
        sum(|psi|^2) * dz = 1.
    """
    if z_nm.shape != v_ev.shape or z_nm.ndim != 1 or z_nm.size < 3:
        raise ValueError("z and V must be 1D arrays of the same length (at least 3 points)")
    dz = float(z_nm[1] - z_nm[0])
    t = HBAR2_OVER_2M_EV_NM2 / dz**2
    diagonal = 2.0 * t + v_ev
    off_diagonal = np.full(z_nm.size - 1, -t)
    if n_states is None:
        energies, vectors = eigh_tridiagonal(diagonal, off_diagonal)
    else:
        energies, vectors = eigh_tridiagonal(
            diagonal, off_diagonal, select="i", select_range=(0, n_states - 1)
        )
    psis = vectors / np.sqrt(dz)
    for i in range(psis.shape[1]):
        psis[:, i] = _fix_sign(psis[:, i])
    return Eigenstates(energies=energies, psis=psis)


def perturbative_energies(
    z_nm: FloatArray, zero_field: Eigenstates, efield_ev_nm: float, index: int
) -> tuple[float, float, float]:
    """Return (E0, E1, E2) for zero-field state `index` (0-based) under H' = eFz.

    E1 = eF <n|z|n> and E2 = (eF)^2 sum_{k != n} |<k|z|n>|^2 / (E_n - E_k),
    summed over every eigenstate in `zero_field`.
    """
    dz = float(z_nm[1] - z_nm[0])
    psi_n = zero_field.psis[:, index]
    z_kn = zero_field.psis.T @ (z_nm * psi_n) * dz  # <k|z|n> for every k
    e_n = zero_field.energies[index]
    others = np.arange(zero_field.energies.size) != index
    e1 = efield_ev_nm * z_kn[index]
    e2 = efield_ev_nm**2 * np.sum(z_kn[others] ** 2 / (e_n - zero_field.energies[others]))
    return float(e_n), float(e1), float(e2)


def probability_in(z_nm: FloatArray, psi: FloatArray, half_width_nm: float) -> float:
    """Return the integral of |psi|^2 over |z| < half_width_nm."""
    dz = float(z_nm[1] - z_nm[0])
    return float(np.sum(psi[np.abs(z_nm) < half_width_nm] ** 2) * dz)


def confined_indices(
    z_nm: FloatArray, states: Eigenstates, width_nm: float, v0_ev: float, efield_ev_nm: float
) -> list[int]:
    """Return the indices of states confined by the (tilted) well, lowest first.

    A state is confined when (a) its energy lies below the lower of the two
    barrier tops at the well edges, V0 - |eF| L/2, and (b) it has more
    probability inside the well than in the classically allowed region outside
    it (where V(z) < E). Condition (b) rejects states that live in the far,
    field-lowered part of a barrier, which the finite grid also contains.
    """
    dz = float(z_nm[1] - z_nm[0])
    v = potential(z_nm, width_nm, v0_ev, efield_ev_nm)
    in_well = np.abs(z_nm) < width_nm / 2.0
    barrier_top = v0_ev - abs(efield_ev_nm) * width_nm / 2.0
    confined = []
    for i, energy in enumerate(states.energies):
        if energy >= barrier_top:
            continue
        density = states.psis[:, i] ** 2
        p_well = float(np.sum(density[in_well]) * dz)
        p_outside_allowed = float(np.sum(density[~in_well & (v < energy)]) * dz)
        if p_well > p_outside_allowed:
            confined.append(i)
    return confined


@lru_cache(maxsize=64)
def _zero_field_states(width_nm: float, v0_ev: float) -> Eigenstates:
    """Return the full zero-field spectrum (cached: it does not depend on F)."""
    z = make_grid(width_nm)
    return solve_schrodinger(z, potential(z, width_nm, v0_ev, 0.0))


def compute_qcse(request: QCSERequest) -> QCSEResponse:
    """Compute the potential and the lowest two confined states, exactly and perturbatively.

    Raises:
        ConfinementError: if no state is confined at the requested field.
    """
    width, v0 = request.width_nm, request.v0_ev
    efield = field_to_ev_per_nm(request.field_kv_cm)
    z = make_grid(width)
    v = potential(z, width, v0, efield)

    zero = _zero_field_states(width, v0)
    zero_bound = [i for i in confined_indices(z, zero, width, v0, 0.0) if zero.energies[i] < v0]

    with_field = solve_schrodinger(z, v, n_states=CANDIDATE_STATES)
    field_bound = confined_indices(z, with_field, width, v0, efield)
    if not field_bound:
        raise ConfinementError(
            "No state is confined at this field: the field tilts the barrier below every "
            "level. Reduce the field, or make the well deeper or narrower."
        )

    n_shown = min(MAX_STATES, len(field_bound), len(zero_bound))
    states: list[BoundState] = []
    for n in range(n_shown):
        i_field, i_zero = field_bound[n], zero_bound[n]
        e0, e1, e2 = perturbative_energies(z, zero, efield, i_zero)
        energy = float(with_field.energies[i_field])
        states.append(
            BoundState(
                index=n + 1,
                energy_ev=energy,
                zero_field_energy_ev=e0,
                stark_shift_ev=energy - e0,
                perturbative=PerturbativeEnergy(
                    zeroth_order_ev=e0, first_order_ev=e1, second_order_ev=e2, total_ev=e0 + e1 + e2
                ),
                psi=with_field.psis[:, i_field].tolist(),
                psi_zero_field=zero.psis[:, i_zero].tolist(),
                probability_in_well=probability_in(z, with_field.psis[:, i_field], width / 2.0),
            )
        )

    notes: list[str] = []
    if n_shown < MAX_STATES:
        notes.append(
            "Only one state is confined for these parameters, so no first excited state is shown."
        )
    if efield != 0.0:
        notes.append(
            "With a field the states are quasi-bound: an electron could tunnel out through the "
            f"thinned barrier. The model ignores this by ending the barrier {BARRIER_NM:g} nm "
            "from each side of the well."
        )

    return QCSEResponse(z_nm=z.tolist(), potential_ev=v.tolist(), states=states, notes=notes)
