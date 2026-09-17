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

  document.getElementById("val-current").textContent = `${d.current_output_kw.toFixed(2)} kW`;
  document.getElementById("sub-current").textContent = `expected ~${d.expected_output_kw.toFixed(2)} kW`;

  document.getElementById("val-panels").textContent = d.panels_needed;

  document.getElementById("val-payback").textContent = `${d.payback_years.toFixed(1)} yrs`;
  document.getElementById("sub-payback").textContent = `~$${d.annual_savings_usd.toFixed(0)}/yr savings`;

  renderChart(d.hourly);
  renderAppliances(d.appliances);
}

const TIER_COLORS = {
  peak: "#4ade80",
  medium: "#e0a75e",
  low: "#5b6472",
  none: "#3a3a45",
};

function renderChart(hourly) {
  const labels = hourly.map((h) => new Date(h.timestamp).toLocaleTimeString([], { hour: "numeric" }));
  const p50 = hourly.map((h) => h.p50_kw);
  const barColors = hourly.map((h) => TIER_COLORS[h.tier] || TIER_COLORS.none);
  const ranges = hourly.map((h) => `${h.p10_kw.toFixed(2)}-${h.p90_kw.toFixed(2)} kW range`);

  const ctx = document.getElementById("output-chart");
  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Expected output (kW)",
          data: p50,
          backgroundColor: barColors,
          borderRadius: 4,
          barPercentage: 0.85,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: (item) => ranges[item.dataIndex],
          },
        },
      },
      scales: {
        x: { ticks: { color: "#9a9aab" }, grid: { display: false } },
        y: {
          ticks: { color: "#9a9aab" },
          grid: { color: "#2a2a35" },
          title: { display: true, text: "kW", color: "#9a9aab" },
          beginAtZero: true,
        },
      },
    },
  });
}

function renderAppliances(appliances) {
  const el = document.getElementById("appliance-list");
  if (!appliances) return;
  el.innerHTML = "";
  appliances.forEach((a) => {
    const card = document.createElement("div");
    card.className = "appliance-card";
    card.innerHTML =
      `<div class="appliance-name">${a.name}</div>` +
      `<div class="appliance-kw">${a.kw.toFixed(2)} kW</div>` +
      `<span class="appliance-tag" style="background:${a.color}22;color:${a.color};border:1px solid ${a.color}66;">${a.tier}</span>`;
    el.appendChild(card);
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
