"""API tests: the contract, validation and error messages."""

import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_default_request_returns_two_states():
    response = client.post("/api/qcse", json={})
    assert response.status_code == 200
    body = response.json()
    assert len(body["z_nm"]) == len(body["potential_ev"])
    assert [s["index"] for s in body["states"]] == [1, 2]
    for state in body["states"]:
        assert len(state["psi"]) == len(body["z_nm"])
        assert 0.0 < state["energy_ev"] < 1.0


@pytest.mark.parametrize(
    "payload",
    [
        {"v0_ev": 0.0},
        {"v0_ev": 10.0},
        {"width_nm": 0.1},
        {"width_nm": 50.0},
        {"field_kv_cm": 1e6},
        {"field_kv_cm": "strong"},
        {"unknown": 1},
    ],
)
def test_invalid_input_is_rejected_with_one_plain_message(payload):
    response = client.post("/api/qcse", json=payload)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_unconfined_parameters_give_a_plain_message():
    response = client.post("/api/qcse", json={"v0_ev": 0.1, "width_nm": 5.0, "field_kv_cm": 3000.0})
    assert response.status_code == 422
    assert "No state is confined" in response.json()["detail"]


def test_page_and_vendor_library_are_served():
    page = client.get("/")
    assert page.status_code == 200
    assert "Quantum-confined Stark effect" in page.text
    assert client.get("/vendor/plotly.min.js").status_code == 200
