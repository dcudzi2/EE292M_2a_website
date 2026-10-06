// Draws what the API returns and handles the sliders. It computes no physics:
// every energy, potential and wavefunction comes from POST /api/qcse.
"use strict";

const DEFAULTS = { v0: 1.0, width: 1.5, field: 0 };
const DEBOUNCE_MS = 60;
const COLORS = { potential: "#222", states: ["#1f77b4", "#d62728"] };

const inputs = {
  v0: document.getElementById("v0"),
  width: document.getElementById("width"),
  field: document.getElementById("field"),
};
const outputs = {
  v0: document.getElementById("v0-value"),
  width: document.getElementById("width-value"),
  field: document.getElementById("field-value"),
};
const showZero = document.getElementById("show-zero");
const plotEl = document.getElementById("plot");
const errorEl = document.getElementById("error");
const tableBody = document.querySelector("#results tbody");
const notesEl = document.getElementById("notes");

let timer = null;
let inFlight = null;
let lastResult = null;

function readParams() {
  return {
    v0_ev: Number(inputs.v0.value),
    width_nm: Number(inputs.width.value),
    field_kv_cm: Number(inputs.field.value),
  };
}

function showSliderValues() {
  outputs.v0.textContent = `${Number(inputs.v0.value).toFixed(2)} eV`;
  outputs.width.textContent = `${Number(inputs.width.value).toFixed(2)} nm`;
  outputs.field.textContent = `${Number(inputs.field.value).toFixed(0)} kV/cm`;
}

// Display formatting only. Below 1e-9 eV is solver round-off, shown as 0.
function fmt(value) {
  if (Math.abs(value) < 1e-9) return "0";
  return Math.abs(value) < 1e-3 ? value.toExponential(3) : value.toFixed(4);
}

function clearResult() {
  lastResult = null;
  Plotly.purge(plotEl);
  tableBody.replaceChildren();
  notesEl.replaceChildren();
}

function showError(message) {
  clearResult();
  errorEl.textContent = message;
  errorEl.hidden = false;
}

// Visual height given to each wavefunction: a fraction of the level spacing,
// so neighbouring curves do not overlap. Purely a drawing choice.
function drawScale(result, v0) {
  const s = result.states;
  const gap = s.length > 1 ? s[1].energy_ev - s[0].energy_ev : v0 - s[0].energy_ev;
  const peak = Math.max(...s[0].psi.map(Math.abs));
  return (0.4 * gap) / peak;
}

function draw(result, params) {
  const z = result.z_nm;
  const scale = drawScale(result, params.v0_ev);
  const halfWidth = params.width_nm / 2;
  const traces = [
    {
      x: z, y: result.potential_ev, name: "V(z)", mode: "lines",
      line: { color: COLORS.potential, width: 2.5 },
      hovertemplate: "z = %{x:.2f} nm<br>V = %{y:.3f} eV<extra></extra>",
    },
  ];
  result.states.forEach((state, i) => {
    const color = COLORS.states[i];
    const label = i === 0 ? "ψ₁ (ground)" : "ψ₂ (1st excited)";
    traces.push({
      x: [z[0], z[z.length - 1]], y: [state.energy_ev, state.energy_ev],
      mode: "lines", line: { color, width: 1, dash: "dot" }, showlegend: false,
      hovertemplate: `E${i + 1} = ${fmt(state.energy_ev)} eV<extra></extra>`,
    });
    traces.push({
      x: z, y: state.psi.map((p) => state.energy_ev + scale * p),
      name: label, mode: "lines", line: { color, width: 2 },
      hovertemplate: `${label}<br>z = %{x:.2f} nm<extra></extra>`,
    });
    if (showZero.checked && state.psi_zero_field) {
      const e0 = state.zero_field_energy_ev;
      traces.push({
        x: z, y: state.psi_zero_field.map((p) => e0 + scale * p),
        name: `${label}, F = 0`, mode: "lines",
        line: { color, width: 1.5, dash: "dash" }, opacity: 0.5,
        hoverinfo: "skip",
      });
    }
  });
  const layout = {
    margin: { l: 60, r: 20, t: 20, b: 50 },
    xaxis: { title: { text: "Position z (nm)" }, zeroline: false },
    yaxis: { title: { text: "Energy (eV)" }, zeroline: false },
    legend: { orientation: "h", y: -0.18 },
    shapes: [-halfWidth, halfWidth].map((x) => ({
      type: "line", x0: x, x1: x, yref: "paper", y0: 0, y1: 1,
      line: { color: "#bbb", width: 1, dash: "dot" },
    })),
  };
  Plotly.react(plotEl, traces, layout, { responsive: true, displaylogo: false });
}

function fillTable(result) {
  const rows = result.states.map((state) => {
    const tr = document.createElement("tr");
    const second = state.perturbative ? fmt(state.perturbative.second_order_ev) : "–";
    for (const text of [`ψ${state.index}`, fmt(state.energy_ev), fmt(state.stark_shift_ev), second]) {
      const td = document.createElement("td");
      td.textContent = text;
      tr.appendChild(td);
    }
    return tr;
  });
  tableBody.replaceChildren(...rows);
  notesEl.replaceChildren(...result.notes.map((note) => {
    const li = document.createElement("li");
    li.textContent = note;
    return li;
  }));
}

async function update() {
  const params = readParams();
  if (inFlight) inFlight.abort();
  const controller = new AbortController();
  inFlight = controller;
  let response;
  let body;
  try {
    response = await fetch("/api/qcse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
      signal: controller.signal,
    });
    body = await response.json().catch(() => ({}));
  } catch (err) {
    if (err.name !== "AbortError") {
      console.error(err);
      showError("Could not reach the server.");
    }
    return;
  } finally {
    if (inFlight === controller) inFlight = null;
  }
  if (!response.ok) {
    showError(typeof body.detail === "string" ? body.detail : `Request failed (${response.status}).`);
    return;
  }
  try {
    errorEl.hidden = true;
    errorEl.textContent = "";
    lastResult = { result: body, params };
    draw(body, params);
    fillTable(body);
  } catch (err) {
    console.error(err);
    showError("Could not draw the result.");
  }
}

function scheduleUpdate() {
  showSliderValues();
  clearTimeout(timer);
  timer = setTimeout(update, DEBOUNCE_MS);
}

Object.values(inputs).forEach((el) => el.addEventListener("input", scheduleUpdate));
showZero.addEventListener("change", () => {
  if (lastResult) draw(lastResult.result, lastResult.params);
});
document.getElementById("reset").addEventListener("click", () => {
  for (const [key, value] of Object.entries(DEFAULTS)) inputs[key].value = value;
  scheduleUpdate();
});

showSliderValues();
update();
