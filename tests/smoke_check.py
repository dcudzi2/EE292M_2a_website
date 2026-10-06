"""Smoke check, run by `make smoke` inside the running app container.

Waits for the server, requests a real result and checks it is physically sensible.
Not collected by pytest (the file name does not start with test_).
"""

import json
import math
import sys
import time
import urllib.request

URL = "http://127.0.0.1:8000/api/qcse"
HBAR2_OVER_2M_EV_NM2 = 0.0380998


def post(payload: dict[str, float]) -> dict:
    """POST a JSON payload to the API and return the decoded response."""
    request = urllib.request.Request(
        URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        return json.load(response)


def main() -> int:
    """Return 0 if the API gives a sensible result within 60 s, else 1."""
    deadline = time.monotonic() + 60
    while True:
        try:
            body = post({"v0_ev": 1.0, "width_nm": 1.5, "field_kv_cm": 1000.0})
            break
        except OSError as exc:
            if time.monotonic() > deadline:
                print(f"smoke: server did not answer: {exc}", file=sys.stderr)
                return 1
            time.sleep(1)

    ground, excited = body["states"]
    infinite_well_e1 = HBAR2_OVER_2M_EV_NM2 * math.pi**2 / 1.5**2
    checks = {
        "0 < E1 < E2 < V0": 0 < ground["energy_ev"] < excited["energy_ev"] < 1.0,
        "E1 below infinite-well value": ground["zero_field_energy_ev"] < infinite_well_e1,
        "ground state Stark shift is negative": ground["stark_shift_ev"] < 0,
    }
    for name, ok in checks.items():
        print(f"smoke: {'ok  ' if ok else 'FAIL'} {name}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
