# 0001: Numerical method for the QCSE

## Decision

Solve the 1D effective-mass Schrodinger equation directly by second-order finite
differences, and alongside it compute Rayleigh-Schrodinger perturbation theory
in H' = eFz to second order. Both come from `src/app/pipeline.py`.

- Model: free-electron mass m_e, V = 0 for |z| < L/2 and V0 outside, plus eFz
  (the sign convention of the Wikipedia QCSE page). An academic example with no real material.
- Grid: 1600 interior points spanning the well plus 4 nm of barrier per side,
  with psi = 0 at the ends. The cell straddling each well edge gets a potential
  weighted by its fraction outside the well. Without this, the effective well
  width is rounded to the grid and energies are off by about 0.5%.
- Exact result: the lowest 24 eigenpairs of the tilted-well matrix
  (`scipy.linalg.eigh_tridiagonal`).
- Perturbative result: the second-order sum runs over *all* eigenstates of the
  zero-field grid matrix, a complete basis on the grid. Wikipedia's closed form
  keeps only the k = 2 term. The full sum for an infinite well is
  -(15 - pi^2)/(24 pi^4) m e^2 F^2 L^4 / hbar^2, which the tests check.
- "Confined" state: energy below the lower barrier top at the well edges,
  V0 - |eF| L/2, and more probability inside the well than in the classically
  allowed region outside it. This rejects states of the finite grid that live
  in the field-lowered far barrier.

## Limits

- Tunnelling is ignored. At strong fields the states are really quasi-bound
  resonances; here the 4 nm barrier ends in hard walls. The page says so.
- Free-electron mass, the same in well and barrier. There is no hole and no
  exciton, so this is not a model of a device's absorption edge.
