"""Typed request and response models for the API (the contract shown at /docs)."""

from pydantic import BaseModel, ConfigDict, Field

# Slider ranges. Validated here, at the API boundary.
V0_MIN_EV, V0_MAX_EV = 0.1, 3.0
WIDTH_MIN_NM, WIDTH_MAX_NM = 0.5, 5.0
FIELD_MAX_KV_CM = 3000.0


class QCSERequest(BaseModel):
    """Parameters of the 1D finite quantum well and the applied field."""

    model_config = ConfigDict(extra="forbid")

    v0_ev: float = Field(
        default=1.0,
        ge=V0_MIN_EV,
        le=V0_MAX_EV,
        description="Barrier height V0 outside the well, in eV (the well floor is 0 eV).",
    )
    width_nm: float = Field(
        default=1.5,
        ge=WIDTH_MIN_NM,
        le=WIDTH_MAX_NM,
        description="Well width L, in nm.",
    )
    field_kv_cm: float = Field(
        default=0.0,
        ge=-FIELD_MAX_KV_CM,
        le=FIELD_MAX_KV_CM,
        description="Uniform electric field F along z, in kV/cm.",
    )


class PerturbativeEnergy(BaseModel):
    """Energy of one state from Rayleigh-Schrodinger perturbation theory in eFz."""

    zeroth_order_ev: float = Field(description="E^(0): zero-field energy, eV.")
    first_order_ev: float = Field(description="E^(1) = <n|eFz|n>, eV (zero by symmetry).")
    second_order_ev: float = Field(description="E^(2) = sum_k |<k|eFz|n>|^2 / (E_n - E_k), eV.")
    total_ev: float = Field(description="E^(0) + E^(1) + E^(2), eV.")


class BoundState(BaseModel):
    """One confined state, exact (numerical) and perturbative."""

    index: int = Field(description="1 for the ground state, 2 for the first excited state.")
    energy_ev: float = Field(description="Energy from direct numerical solution at field F, eV.")
    zero_field_energy_ev: float = Field(description="Exact energy at F = 0, eV.")
    stark_shift_ev: float = Field(description="energy_ev - zero_field_energy_ev, eV.")
    perturbative: PerturbativeEnergy | None = Field(
        description="Perturbation theory result, if the state is bound at F = 0."
    )
    psi: list[float] = Field(description="Wavefunction at field F on the grid z, nm^-1/2.")
    psi_zero_field: list[float] | None = Field(
        description="Wavefunction at F = 0 on the grid z, nm^-1/2, if bound at F = 0."
    )
    probability_in_well: float = Field(description="Integral of |psi|^2 over |z| < L/2.")


class QCSEResponse(BaseModel):
    """Potential landscape and the lowest two confined states."""

    z_nm: list[float] = Field(description="Grid positions, nm; the well is |z| < L/2.")
    potential_ev: list[float] = Field(description="V(z) = V_well(z) + eFz, eV.")
    states: list[BoundState] = Field(description="Up to two confined states, lowest first.")
    notes: list[str] = Field(description="Plain-language caveats about these results.")
