# Solar Advisor Agent

A consumer-focused solar advisor built with Microsoft Agent Framework,
GPT-4.1-mini in Microsoft Foundry, deterministic solar calculations, and a
Streamlit product UI.

## Run

```powershell
cd C:\Users\ebeltrnreyes\source\repos\solar-advisor-agent
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m streamlit run app.py
```

Open `http://localhost:8501`.

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

Dashboard calculations run directly through the same deterministic core; the
language model is called when a user submits a chat question.

## Documentation

- `docs\ARCHITECTURE.md` — exact runtime and model-call path
- `docs\USER_MANUAL.md` — setup and operation
- `docs\AURORA_FUTURE_WORK.md` — preserved Aurora implementation plan
- `docs\PRESENTATION_NOTES.md` — demo claims and limitations

## Tests

```powershell
python -m pytest -q
python -m ruff check .
```
