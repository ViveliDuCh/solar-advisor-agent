let currentAgent = "sizing";
let chart = null;

async function loadAgents() {
  const res = await fetch("/api/agents");
  const agents = await res.json();
  const list = document.getElementById("agent-list");
  list.innerHTML = "";
  agents.forEach((a, i) => {
    const btn = document.createElement("button");
    btn.className = "agent-btn" + (i === 0 ? " active" : "");
    btn.dataset.id = a.id;
    btn.innerHTML = `${a.name}<span class="blurb">${a.blurb}</span>`;
    btn.onclick = () => selectAgent(a.id);
    list.appendChild(btn);
  });
}

function selectAgent(id) {
  currentAgent = id;
  document.querySelectorAll(".agent-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.id === id);
  });
  document.getElementById("messages").innerHTML = "";
}

async function loadUser() {
  const res = await fetch("/api/user");
  const u = await res.json();
  document.getElementById("user-card").innerHTML =
    `<strong>${u.user.name}</strong><br/>${u.user.location_label}<br/>` +
    `${u.existing_system.panel_count} x ${u.existing_system.panel_rated_w}W panels<br/>` +
    `~${u.consumption.avg_daily_kwh} kWh/day (synthetic demo data)`;
}

async function loadDashboard() {
  const res = await fetch("/api/dashboard");
  const d = await res.json();

  const healthEl = document.getElementById("val-health");
  healthEl.textContent = d.health_status === "ok" ? "Healthy" : "Needs attention";
  healthEl.className = "card-value " + d.health_status;
  document.getElementById("sub-health").textContent = d.fault_code || "";

  document.getElementById("val-current").textContent = `${d.current_output_w.toFixed(0)} W`;
  document.getElementById("sub-current").textContent = `expected ~${d.expected_output_w.toFixed(0)} W`;

  document.getElementById("val-panels").textContent = d.panels_needed;

  document.getElementById("val-payback").textContent = `${d.payback_years.toFixed(1)} yrs`;
  document.getElementById("sub-payback").textContent = `~$${d.annual_savings_usd.toFixed(0)}/yr savings`;

  renderChart(d.hourly);
}

function renderChart(hourly) {
  const labels = hourly.map((h) => new Date(h.timestamp).toLocaleTimeString([], { hour: "numeric" }));
  const p10 = hourly.map((h) => h.p10_w);
  const p50 = hourly.map((h) => h.p50_w);
  const p90 = hourly.map((h) => h.p90_w);

  const ctx = document.getElementById("output-chart");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "P90 (optimistic)",
          data: p90,
          borderColor: "rgba(108,92,231,0.15)",
          backgroundColor: "rgba(108,92,231,0.12)",
          fill: "+1",
          pointRadius: 0,
          tension: 0.3,
        },
        {
          label: "P50 (expected)",
          data: p50,
          borderColor: "#6c5ce7",
          backgroundColor: "rgba(108,92,231,0.25)",
          fill: false,
          pointRadius: 0,
          tension: 0.3,
          borderWidth: 2,
        },
        {
          label: "P10 (conservative)",
          data: p10,
          borderColor: "rgba(108,92,231,0.15)",
          backgroundColor: "rgba(108,92,231,0.12)",
          fill: false,
          pointRadius: 0,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#9a9aab" } } },
      scales: {
        x: { ticks: { color: "#9a9aab" }, grid: { color: "#2a2a35" } },
        y: { ticks: { color: "#9a9aab" }, grid: { color: "#2a2a35" }, title: { display: true, text: "Watts", color: "#9a9aab" } },
      },
    },
  });
}

function addMessage(text, who) {
  const el = document.createElement("div");
  el.className = "msg " + who;
  el.textContent = text;
  document.getElementById("messages").appendChild(el);
  el.scrollIntoView({ behavior: "smooth" });
}

document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("message-input");
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, "user");
  input.value = "";
  addMessage("…thinking…", "agent");

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent: currentAgent, message }),
  });
  const data = await res.json();
  const nodes = document.querySelectorAll(".msg.agent");
  nodes[nodes.length - 1].textContent = data.reply;
});

loadAgents();
loadUser();
loadDashboard();
