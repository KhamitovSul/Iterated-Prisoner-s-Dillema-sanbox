const API_URL = "http://127.0.0.1:8000";
const $ = (selector) => document.querySelector(selector);
const selected = new Set(["TitForTat", "Grudger", "Cooperator", "Defector"]);
let latest = null;
let strategies = [];

function value(id) { return Number($(`#${id}`).value); }
function setupRanges() {
  ["turns", "repetitions", "noise"].forEach(id => {
    const input = $(`#${id}`), out = $(`#${id}-output`);
    const paint = () => out.textContent = id === "noise" ? `${input.value}%` : input.value;
    input.addEventListener("input", paint); paint();
  });
}
function renderCount() {
  $("#count").textContent = `${selected.size} selected`;
  $("#run").disabled = selected.size < 2;
  $("#clear-selection").hidden = selected.size === 0;
}
function renderStrategies() {
  const query = $("#strategy-search").value.trim().toLocaleLowerCase();
  const visible = strategies.filter(({ name, description }) => `${name} ${description}`.toLocaleLowerCase().includes(query));
  const list = $("#strategy-list"), template = $("#strategy-template");
  list.replaceChildren();
  $("#visible-count").textContent = query ? `${visible.length} matches out of ${strategies.length}` : `${strategies.length} available strategies`;
  visible.forEach(({ name, description }) => {
    const node = template.content.cloneNode(true), input = node.querySelector("input");
    input.checked = selected.has(name);
    input.setAttribute("aria-label", name);
    node.querySelector("b").textContent = name;
    node.querySelector("small").textContent = description;
    input.addEventListener("change", () => {
      if (input.checked && selected.size >= 8) {
        input.checked = false;
        setStatus("MAX 8");
        $("#result-subtitle").textContent = "A tournament supports no more than eight selected strategies.";
        return;
      }
      input.checked ? selected.add(name) : selected.delete(name);
      renderCount(); renderStrategies();
    });
    list.append(node);
  });
}

async function loadStrategies() {
  const response = await fetch(`${API_URL}/api/strategies`);
  if (!response.ok) throw new Error("Could not load the strategy catalogue. Start FastAPI on port 8000.");
  strategies = await response.json();
  renderStrategies(); renderCount();
}

function setStatus(text, busy = false) { $("#status").textContent = text; $("#status").classList.toggle("busy", busy); }
function scoreBar(score, max) { return `<i style="width:${Math.max(5, score / max * 100)}%"></i>`; }
function renderResults(data) {
  latest = data; const rows = data.ranking, max = rows[0].total_score;
  $("#empty").hidden = true; $("#result-content").hidden = false;
  $("#result-subtitle").textContent = `${data.meta.turns} turns · ${data.meta.repetitions} repetitions · noise ${Math.round(data.meta.noise * 100)}%`;
  $("#podium").innerHTML = rows.slice(0, 3).map((r, i) => `<div class="place p${i + 1}"><em>${i + 1}</em><b>${r.name}</b><span>${r.total_score}</span></div>`).join("");
  $("#chart").innerHTML = rows.map(r => `<div class="bar"><span>${r.name}</span><div>${scoreBar(r.total_score, max)}</div><b>${r.total_score}</b></div>`).join("");
  $("#ranking").innerHTML = rows.map(r => `<tr><td>${r.rank}</td><td><b>${r.name}</b></td><td>${r.total_score}</td><td>${r.mean_wins}</td><td><button class="match-btn" data-name="${r.name}">Match</button></td></tr>`).join("");
  document.querySelectorAll(".match-btn").forEach(button => button.addEventListener("click", () => openMatch(button.dataset.name)));
}
async function runTournament() {
  const button = $("#run"); button.disabled = true; setStatus("RUNNING…", true);
  try {
    const response = await fetch(`${API_URL}/api/tournament`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ strategies: [...selected], turns: value("turns"), repetitions: value("repetitions"), noise: value("noise") / 100 }) });
    if (!response.ok) throw new Error(`Tournament could not be completed (HTTP ${response.status}).`);
    renderResults(await response.json()); setStatus("READY");
  } catch (error) { $("#result-subtitle").textContent = error.message; setStatus("ERROR"); }
  finally { renderCount(); }
}
async function openMatch(name) {
  const opponent = latest.ranking.find(row => row.name !== name)?.name; if (!opponent) return;
  const panel = $("#match-panel"); panel.hidden = false; $("#match-title").textContent = `${name} × ${opponent}`; $("#match-score").textContent = "Simulating match…"; $("#timeline").innerHTML = ""; panel.scrollIntoView({ behavior: "smooth", block: "start" });
  try {
    const response = await fetch(`${API_URL}/api/match`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ left: name, right: opponent, turns: Math.min(value("turns"), 100), noise: value("noise") / 100 }) });
    if (!response.ok) throw new Error(`Match could not be completed (HTTP ${response.status}).`);
    const data = await response.json();
    $("#match-score").textContent = `Final score: ${data.left} ${data.totals.left} — ${data.totals.right} ${data.right}`;
    $("#timeline").innerHTML = data.rounds.map(r => `<div class="round"><small>${r.round}</small><span class="move ${r.left}">${r.left}</span><span class="move ${r.right}">${r.right}</span><b>${r.left_total} : ${r.right_total}</b></div>`).join("");
  } catch (error) { $("#match-score").textContent = error.message; }
}

$("#run").addEventListener("click", runTournament);
$("#close-match").addEventListener("click", () => $("#match-panel").hidden = true);
$("#strategy-search").addEventListener("input", renderStrategies);
$("#clear-selection").addEventListener("click", () => { selected.clear(); renderCount(); renderStrategies(); });
setupRanges(); loadStrategies().catch(error => { $("#result-subtitle").textContent = error.message; setStatus("ERROR"); });
