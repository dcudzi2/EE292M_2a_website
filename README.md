# EE292M_2a_website

HW 2a for EE292M: an interactive web page on the **quantum-confined Stark effect (QCSE)**.

The page explains the QCSE for engineers, and why it matters for LEDs and
electro-absorption modulators. Below that is a live plot of a 1D finite quantum
well: the potential energy, the ground state and the first excited state. Sliders
set the barrier height V0 (eV), the well width L (nm) and the electric field F
(kV/cm). Each change is sent to the backend, which solves the Schrodinger
equation numerically and also applies second-order perturbation theory.

This is an idealised academic model: free-electron mass, a well floor at 0 eV, barriers at V0.

## Requirements

Only **Docker** (Docker Desktop on Windows/macOS), **GNU Make** and **git**.
Nothing else is installed on your machine; everything runs in a container.

## Quick start

```sh
git clone https://github.com/dcudzi2/EE292M_2a_website.git
cd EE292M_2a_website
make build     # build the image (first time takes a few minutes)
make up        # start the app
```

Open <http://127.0.0.1:8000>. The API contract is at <http://127.0.0.1:8000/docs>.
Stop it with `make down`.

## Everyday commands

| Command        | What it does                                              |
| -------------- | --------------------------------------------------------- |
| `make help`    | list every target                                         |
| `make build`   | build everything into the image                           |
| `make up`      | start the app on 127.0.0.1 (port from `APP_PORT`, default 8000) |
| `make down`    | stop the app                                              |
| `make verify`  | lint, tests and a smoke test of the running app: the gate |
| `make clean`   | remove this project's containers, images and caches       |
| `make test` / `make lint` / `make fmt` | tests; check style; fix style     |
| `make logs` / `make shell` | follow the server output; shell in the container |
| `make lock`    | after changing a dependency in `docker/`, re-record the locks |

To use another port, copy `.env.example` to `.env` and change `APP_PORT`.

## How it works

- `src/app/pipeline.py`: the physics (finite differences plus perturbation theory).
- `src/app/api.py`: one endpoint, `POST /api/qcse`.
- `src/web/`: the page. It draws what the API returns and computes nothing itself.
- `tests/`: checks against analytic results. These are the infinite-well
  levels, the finite-well transcendental equations, and the closed-form
  second-order Stark shift.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design and
[docs/0001-numerical-method.md](docs/0001-numerical-method.md) for the method and its limits.
