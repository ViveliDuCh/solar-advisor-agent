# Solar Advisor Agent

A consumer-focused solar advisor built with Microsoft Agent Framework,
GPT-4.1-mini in Microsoft Foundry, deterministic solar calculations, and a
Streamlit product UI.

## Clone and first-time setup

```powershell
git clone <repository-url>
cd solar-advisor-agent
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

If the repository is already cloned, start with `cd solar-advisor-agent`.
The `.venv` directory persists after the terminal closes. Repeat this setup only
when creating a fresh checkout or after the project dependencies change.

## Start the app

From the repository directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

No virtual-environment activation or package installation is required. Open
`http://localhost:8501` if Streamlit does not open it automatically.

PowerShell one-liner from the repository directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Foundry chat

Copy `.env.example` to `.env` and set:

```dotenv
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=<deployment-name>
AZURE_CONFIG_DIR=<optional isolated Azure CLI profile>
```

Authenticate with Azure CLI in the Foundry resource tenant. When configured,
chat messages follow this path:

```text
Streamlit -> Agent Framework HandoffBuilder -> specialist Agent
          -> deterministic tool -> GPT-4.1-mini response
```

Dashboard calculations run directly through the deterministic domain functions;
the language model is called when a user submits a chat question.

## Code layout

- `src\solar_agent\agents\` — Agent Framework specialist definitions
- `src\solar_agent\skills\` — deterministic tools exposed to agents
- `src\solar_agent\domain\` — real solar, household, finance, and maintenance calculations
- `src\solar_agent\providers\` — synthetic weather and future Aurora provider boundaries
- `src\solar_agent\demo\` — visible demonstration assumptions and fixture builders
- `src\solar_agent\fallback\` — local rule-based chat used only when Foundry is unavailable

## Documentation

- `docs\ARCHITECTURE.md` — exact runtime and model-call path
- `docs\USER_MANUAL.md` — setup and operation
- `docs\AURORA_FUTURE_WORK.md` — preserved Aurora implementation plan
- `docs\PRESENTATION_NOTES.md` — demo claims and limitations

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```
