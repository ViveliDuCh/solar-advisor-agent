# Solar Advisor user manual

## Start the product

```powershell
cd solar-advisor-agent
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501`. This is the only product interface.

## Chat status

The banner above **Ask Solar Advisor** reports the active mode:

- **Live multi-agent mode:** Streamlit is calling Microsoft Agent Framework
  and the configured Foundry GPT model.
- **Offline fallback:** Foundry settings or authentication are unavailable,
  so supported questions use local deterministic responses.

The live call occurs only after selecting **Send**. The dashboard does not call
the model simply to display calculations.

## Foundry configuration

Local `.env`:

```dotenv
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=<deployment-name>
AZURE_CONFIG_DIR=<optional Azure CLI profile directory>
```

Authenticate the account that has Foundry User in the Foundry tenant:

```powershell
$env:AZURE_CONFIG_DIR = "<same profile directory>"
az login --tenant "<Foundry tenant ID>"
```

Never commit `.env`, Azure CLI profiles, passwords, tokens, or API keys.

## Data shown

Editable inputs are in the sidebar. Remaining demo defaults are documented in:

```text
src\solar_agent\data\demo_assumptions.json
```

The primary weather source is currently synthetic. Aurora work remains in
`docs\AURORA_FUTURE_WORK.md` and is not represented as active.

## Review the integration

- `app.py` — calls `handle_message()` when Send is selected
- `src\solar_agent\orchestrator.py` — Agent Framework handoff workflow
- `src\solar_agent\agent_client.py` — `FoundryChatClient` and GPT deployment
- `src\solar_agent\agents\` — specialist agents
- `src\solar_agent\skills\` — agent-callable deterministic tools
- `src\solar_agent\domain\` — real calculation engine shared with the dashboard
- `src\solar_agent\providers\` — weather and future Aurora provider boundaries
- `src\solar_agent\demo\` — disclosed example inputs
- `src\solar_agent\fallback\` — local rule-based chat when Foundry is unavailable
- `docs\ARCHITECTURE.md` — complete execution diagram

## Validate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```
