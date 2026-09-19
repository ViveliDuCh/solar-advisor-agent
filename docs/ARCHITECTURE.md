# Solar Advisor architecture

This document describes the code in the current branch. The repository has one
product UI and one Agent Framework integration.

## 1. Runtime overview

```text
Browser
  |
  v
Streamlit product UI (app.py, http://localhost:8501)
  |
  +-- page calculations -----------------------------------------------+
  |   src/solar_agent/domain                                           |
  |   pvlib solar output, household load, scheduling, finance,         |
  |   maintenance simulation, confidence, and charts                   |
  |                                                                   |
  |   src/solar_agent/providers                                        |
  |   synthetic weather and future Aurora artifact boundary            |
  |                                                                   |
  +-- user submits a chat question                                    |
      |                                                               |
      v                                                               |
  app.py:render_advisor_chat                                          |
      |                                                               |
      v                                                               |
  orchestrator.py:handle_message                                      |
      |                                                               |
      v                                                               |
  Agent Framework HandoffBuilder workflow                             |
      |                                                               |
      +--> SolarAdvisor triage Agent                                   |
      +--> ForecastAgent                                               |
      +--> FinancialAgent                                              |
      +--> MaintenanceAgent                                            |
      +--> SafetyAgent                                                 |
      +--> SizingAgent                                                 |
      |                                                               |
      v                                                               |
  agent_client.py:create_chat_client                                   |
      |                                                               |
      v                                                               |
  FoundryChatClient(project_endpoint, model, AzureCliCredential)       |
      |                                                               |
      v                                                               |
  Microsoft Foundry deployment: gpt-4.1-mini                          |
      |                                                               |
      v                                                               |
  Specialist chooses deterministic Python tool(s) ---------------------+
```

The page does not call the language model merely to render existing numbers.
Dashboard values are calculated directly because deterministic functions are
faster, testable, reproducible, and cheaper. **A real Agent Framework request
occurs when the user submits a chat message.** The model chooses the specialist
and tools; Python tools calculate watts, kWh, dollars, and maintenance results.

## 2. Exact model-call path

1. `app.py` calls `handle_message()` after the user selects **Send**.
2. `src/solar_agent/orchestrator.py` builds the `HandoffBuilder` workflow and
   calls:

   ```python
   result = await build_advisor_agent().run(prompt, session=session)
   ```

3. `src/solar_agent/agent_client.py` creates:

   ```python
   FoundryChatClient(
       project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
       model=os.environ["FOUNDRY_MODEL"],
       credential=AzureCliCredential(),
   )
   ```

4. The local `.env` identifies the configured Foundry project and model
   deployment. The file is ignored by Git.
5. Azure CLI authenticates an identity that has access to the configured
   Foundry project.

This is GPT-4.1-mini accessed through Microsoft Foundry. It is not the ChatGPT
consumer application and no OpenAI API key is used.

## 3. Agents versus skills

Only `src/solar_agent/agents` contains agent implementations. The former
top-level `ui_agents` discovery wrappers were removed.

| Component | Responsibility | May calculate numbers? |
|---|---|---|
| `SolarAdvisor` | Understand request and hand off to specialist | No |
| `ForecastAgent` | Explain forecast and appliance timing | No; calls forecast/output/scheduler tools |
| `FinancialAgent` | Explain bills, cost changes and payback | No; calls financial/scenario tools |
| `MaintenanceAgent` | Interpret expected versus inverter output | No; calls telemetry tool |
| `SafetyAgent` | Explain conservative safety boundaries | No electrical design |
| `SizingAgent` | Explain educational energy sizing | No; calls sizing tool |
| `skills` | Agent-callable, deterministic operations | Yes |
| `domain` | Solar, household, finance, and maintenance calculations used by UI and skills | Yes |
| `providers` | Weather input and future Aurora artifact boundaries | No household calculations |
| `demo` | Loads disclosed example inputs from the assumption catalog | No calculations |
| `fallback` | Rule-based local chat when Foundry is unavailable | Uses supplied dashboard results |

An **agent** is the language-model reasoning layer: instructions, conversation
context, handoffs, and tool selection. A **skill/tool** is ordinary Python that
accepts structured input and returns structured output. Numeric calculations
stay outside the model so they can be tested.

## 4. Inputs and assumptions

Demo defaults are centralized in:

```text
src/solar_agent/data/demo_assumptions.json
```

That file contains the example household, mixed solar array, appliances,
electricity rate, installed cost, simulated underperformance, scenario defaults,
and weather mode. The Streamlit sidebar exposes the principal household and
array values for editing.

| Classification | Examples | Treatment |
|---|---|---|
| User input | Annual kWh, array sections, inverter limit, electricity rate | Passed into calculations and chat context |
| Demo default | Appliance power/duration, freezer 500 kWh/year, water heating 3,000 kWh/year | Loaded from the catalog and explicitly disclosed |
| Simulation | Synthetic weather, 12% inverter underperformance | Clearly labeled; never represented as measured |
| Computed result | Solar output, opportunity score, cost change | Produced by deterministic domain functions or skills |

Production behavior must replace a demo default with measured/user-provided
data or show the default and confidence impact. The agent is instructed not to
invent missing numeric inputs.

## 5. Forecast and Aurora boundary

The primary dashboard currently uses `SyntheticForecastProvider` for a stable
48-hour demonstration. It is explicitly labeled as synthetic.

Aurora remains part of the architecture:

```text
Atmospheric source
  -> Aurora-compatible t=-6h and t=0 batch
  -> Aurora inference in Foundry or suitable GPU compute
  -> validated global forecast artifact
  -> location extraction and irradiance conversion
  -> CachedAuroraForecastProvider
  -> same pvlib and scheduling core
```

The detailed variables, pressure levels, batch construction, validation, Blob
Storage flow, and operational-weather migration are preserved in
`docs/AURORA_FUTURE_WORK.md`. Aurora is a weather model; GPT-4.1-mini is the
conversation/tool-selection model. They are separate deployments.

## 6. Privacy and safety

- No utility statement, account number, payment information, or exact address is
  required by the demo.
- Email addresses and phone numbers are redacted before live model requests.
- The model receives a compact dashboard summary rather than the complete
  Streamlit session.
- No language model performs electrical calculations or certifies a circuit.
- The application does not provide wiring, breaker, string, grounding, rooftop,
  permitting, interconnection, or installation instructions.
- Inverter telemetry and maintenance diagnoses are simulated until a read-only
  vendor adapter is connected.

## 7. Repository layout

```text
app.py                              # only product UI
src/solar_agent/
  agent_client.py                   # FoundryChatClient construction
  orchestrator.py                   # Agent Framework handoff workflow
  agents/                           # five specialist Agent definitions
  skills/                           # deterministic Agent-callable tools
  domain/                           # real solar, household, finance, and maintenance logic
  providers/                        # weather and future Aurora boundaries
  demo/                             # disclosed assumptions and fixture builders
  fallback/                         # offline rule-based chat
  adapters/                         # simulated and future inverter boundaries
  security/                         # input redaction
  data/demo_assumptions.json        # visible demo defaults
docs/
  ARCHITECTURE.md                   # this runtime design
  USER_MANUAL.md                    # setup and operation
  AURORA_FUTURE_WORK.md             # retained Aurora implementation plan
tests/                              # deterministic and runtime configuration tests
```

## 8. Current completion state

Working:

- One Streamlit product UI
- Live GPT-4.1-mini access through Foundry
- Agent Framework multi-agent handoffs
- Deterministic solar, scheduling, scenario, finance, and maintenance tools
- Mixed-array modeling and explicit confidence
- Local synthetic-weather demonstration

Not production-complete:

- Aurora or another validated live provider in the primary UI
- Smart-meter interval data
- Real inverter telemetry
- Versioned utility tariffs and export credits
- Production authentication, persistence, monitoring, deployment and evaluation
