# syntax=docker/dockerfile:1
#
# Four stages (see ARCHITECTURE.md):
#   uv-tools    Python + uv; `make lock` runs `uv lock` here (needs no lock)
#   node-tools  Node + npm; `make lock` runs `npm install --package-lock-only` here
#   frontend    installs the frontend libraries exactly as package-lock.json records
#   runtime     the development image: Python deps from uv.lock + frontend files
#
# The image never copies src/: the repository is mounted at /work at run time.

ARG PYTHON_IMAGE=python:3.14-slim
ARG NODE_IMAGE=node:24-slim
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.9

FROM ${UV_IMAGE} AS uv-binary

# --- Stage 1: Python tooling --------------------------------------------------
FROM ${PYTHON_IMAGE} AS uv-tools
COPY --from=uv-binary /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy
WORKDIR /work/docker

# --- Stage 2: Node tooling ----------------------------------------------------
FROM ${NODE_IMAGE} AS node-tools
WORKDIR /work/docker

# --- Stage 3: frontend libraries, from the lock only --------------------------
FROM node-tools AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund \
    || (echo "docker/package-lock.json does not match docker/package.json: run 'make lock' and commit both files." >&2; exit 1)

# --- Stage 4: development runtime ---------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/work/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENDOR_DIR=/opt/vendor

WORKDIR /opt/deps
COPY pyproject.toml uv.lock ./
RUN --mount=from=uv-binary,source=/uv,target=/bin/uv \
    uv sync --locked --no-install-project \
    || (echo "docker/uv.lock does not match docker/pyproject.toml: run 'make lock' and commit both files." >&2; exit 1)

# Frontend libraries live outside /work, which the repository mount would hide.
COPY --from=frontend /build/node_modules/plotly.js-dist-min/plotly.min.js /opt/vendor/plotly.min.js

WORKDIR /work
EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
