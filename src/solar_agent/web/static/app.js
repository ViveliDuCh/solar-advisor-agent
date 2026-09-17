let currentAgent = "sizing";

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
