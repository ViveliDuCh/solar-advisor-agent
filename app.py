from __future__ import annotations

import asyncio
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from agent_framework import AgentSession

from solar_agent.agent_client import agent_framework_mode
from solar_agent.core.chat import AdvisorContext, answer_question
from solar_agent.core.demo import demo_appliances, demo_household
from solar_agent.core.energy import (
    TIMEZONE,
    classify_appliance_usage,
    energy_flows,
    estimate_solar_power,
    household_load_profile,
    opportunity_score,
    schedule_appliances,
)
from solar_agent.core.finance import simple_financial_estimate
from solar_agent.core.forecast import SyntheticForecastProvider
from solar_agent.core.maintenance import diagnose_maintenance, simulate_inverter_telemetry
from solar_agent.core.models import ArraySection, SolarSystem
from solar_agent.orchestrator import handle_message

st.set_page_config(page_title="Solar Advisor AI", page_icon="☀️", layout="wide")


def format_clock(value: pd.Timestamp, include_day: bool = False) -> str:
    pattern = "%a %I:%M %p" if include_day else "%I:%M %p"
    return value.strftime(pattern).replace(" 0", " ").lstrip("0")


def render_advisor_chat(context: AdvisorContext) -> None:
    st.subheader("Ask Solar Advisor")
    mode = agent_framework_mode()
    if mode == "offline":
        st.warning(
            "**Offline fallback.** Agent Framework is installed, but no chat deployment is "
            "configured. Answers use the local deterministic calculator until "
            "`FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` are set."
        )
    else:
        provider = "Microsoft Foundry" if mode == "foundry" else "OpenAI"
        st.success(
            f"**Live multi-agent mode:** Microsoft Agent Framework is connected through "
            f"{provider}. Questions are handed to Forecast, Financial, Maintenance, Safety, "
            "or Sizing agents, which call deterministic tools for numbers."
        )
    with st.expander("Exactly what feeds this chat"):
        st.markdown(
            f"""
            - **Household input:** {context.annual_consumption_kwh:,.0f} kWh/year
            - **Modeled solar production:** {context.annual_production_kwh:,.0f} kWh/year
            - **Solar-array capacity:** {context.system_capacity_kw:.1f} kW DC
            - **Illustrative electricity value:** ${context.electricity_rate:.2f}/kWh
            - **Weather source:** synthetic 48-hour demonstration forecast
            - **Agent runtime:** {mode}
            - **Calculation tools:** deterministic Python skills and `src/solar_agent/core`

            No uploaded statement, personal utility account, or live inverter is being read.
            Before a live model receives a question, email addresses and phone numbers are
            redacted. Do not enter account numbers, exact addresses, or payment information.
            """
        )
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "I can calculate supported household scenarios and explain the dashboard. "
                    "For example: **“What if I add a freezer?”** followed by "
                    "**“How would that change my costs?”**"
                ),
            }
        ]

    previous_user_question = next(
        (
            message["content"]
            for message in reversed(st.session_state.messages)
            if message["role"] == "user"
        ),
        None,
    )

    conversation = st.container(height=360)
    with st.form("solar_advisor_question", clear_on_submit=True):
        question = st.text_input(
            "Your question",
            placeholder="Ask a dashboard question or household scenario",
        )
        submitted = st.form_submit_button("Send", type="primary")

    if submitted and question.strip():
        st.session_state.messages.append({"role": "user", "content": question})
        if mode == "offline":
            response = answer_question(question, context, previous_user_question)
        else:
            if "agent_session" not in st.session_state:
                st.session_state.agent_session = AgentSession()
            dashboard_context = (
                f"Annual household use: {context.annual_consumption_kwh:.0f} kWh. "
                f"Modeled annual solar: {context.annual_production_kwh:.0f} kWh. "
                f"Array capacity: {context.system_capacity_kw:.2f} kW DC. "
                f"Illustrative electricity rate: ${context.electricity_rate:.3f}/kWh. "
                f"Forecast confidence: {context.forecast_confidence}. "
                "Weather currently displayed by the dashboard is synthetic."
            )
            try:
                response = asyncio.run(
                    handle_message(
                        question,
                        dashboard_context=dashboard_context,
                        session=st.session_state.agent_session,
                    )
                )
            except Exception as exc:
                fallback = answer_question(question, context, previous_user_question)
                response = (
                    f"**Live Agent Framework request failed ({type(exc).__name__}).** "
                    "The answer below is the explicitly labeled local fallback.\n\n"
                    f"{fallback}"
                )
        st.session_state.messages.append({"role": "assistant", "content": response})

    if st.button("Clear conversation"):
        st.session_state.messages = st.session_state.messages[:1]
        st.session_state.pop("agent_session", None)
        st.rerun()

    with conversation:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; max-width: 1500px;}
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(28,45,70,.75), rgba(15,111,100,.38));
        border: 1px solid rgba(112,224,189,.24);
        border-radius: 16px;
        padding: 14px;
    }
    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 20px;
        background: linear-gradient(120deg, #0b1f33, #0f6f64 68%, #efb64c);
        color: white;
        margin-bottom: 1rem;
    }
    .hero h1 {margin: 0; font-size: 2.4rem;}
    .hero p {margin: .45rem 0 0; font-size: 1.05rem; opacity: .92;}
    .plain-language {
        padding: 1rem 1.2rem;
        border-left: 5px solid #00e6a7;
        border-radius: 10px;
        background: rgba(0, 230, 167, .08);
        margin: .75rem 0 1rem;
    }
    </style>
    <div class="hero">
      <h1>Solar Advisor AI</h1>
      <p>Understand your panels, ask “what if?”, and plan energy use around the sun.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Example household")
    st.caption(
        "The app starts with a synthetic grid-connected home in ZIP 98052. "
        "Edit facts you know; unknown values stay visible as assumptions."
    )
    annual_consumption = st.number_input(
        "Electricity used in one year",
        min_value=2_000,
        max_value=30_000,
        value=10_800,
        step=100,
        help="Measured in kWh. A real user can enter 12 monthly totals instead.",
    )
    inverter_ac_kw = st.number_input(
        "Shared inverter maximum output (kW)",
        min_value=1.0,
        max_value=30.0,
        value=7.6,
        step=0.1,
        help="This limits total solar AC output. It does not describe household circuit safety.",
    )

    st.subheader("Describe the solar array")
    st.caption(
        "Use one row for each group of panels that shares wattage, direction, tilt, and shading."
    )
    default_sections = pd.DataFrame(
        [
            {
                "Panel count": 12,
                "Watts each": 400,
                "Tilt °": 30,
                "Direction °": 180,
                "Shading %": 4,
            },
            {
                "Panel count": 8,
                "Watts each": 400,
                "Tilt °": 24,
                "Direction °": 225,
                "Shading %": 7,
            },
        ]
    )
    edited_sections = st.data_editor(
        default_sections,
        hide_index=True,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "Panel count": st.column_config.NumberColumn(min_value=1, max_value=100, step=1),
            "Watts each": st.column_config.NumberColumn(min_value=100, max_value=800, step=5),
            "Tilt °": st.column_config.NumberColumn(min_value=0, max_value=90, step=1),
            "Direction °": st.column_config.NumberColumn(min_value=0, max_value=359, step=1),
            "Shading %": st.column_config.NumberColumn(min_value=0, max_value=90, step=1),
        },
    )

    with st.expander("Simple financial example"):
        electricity_rate = st.number_input(
            "Illustrative value of electricity ($/kWh)",
            min_value=0.01,
            max_value=1.00,
            value=0.14,
            step=0.01,
        )
        installed_cost = st.number_input(
            "Illustrative installed cost ($)",
            min_value=1_000,
            max_value=100_000,
            value=24_000,
            step=500,
        )

try:
    sections = tuple(
        ArraySection(
            panel_count=int(row["Panel count"]),
            panel_watts=int(row["Watts each"]),
            tilt_degrees=float(row["Tilt °"]),
            azimuth_degrees=float(row["Direction °"]),
            shading_percent=float(row["Shading %"]),
        )
        for _, row in edited_sections.dropna().iterrows()
    )
    if not sections:
        raise ValueError("At least one array section is required.")
except (TypeError, ValueError) as error:
    st.error(f"Check the solar-array rows: {error}")
    st.stop()

household = demo_household(work_from_home=True)
household = household.__class__(
    zip_code=household.zip_code,
    annual_consumption_kwh=float(annual_consumption),
    occupants=household.occupants,
    work_from_home=True,
)
system = SolarSystem(sections=sections, inverter_ac_kw=float(inverter_ac_kw))
appliances = demo_appliances(include_ev=True)

start = pd.Timestamp(datetime.now(), tz=TIMEZONE).floor("h")
weather, metadata = SyntheticForecastProvider().get_hourly(start, 48)
frame = estimate_solar_power(weather, system)
flexible_energy_kwh = sum(appliance.energy_kwh for appliance in appliances)
frame["base_load_kw"] = household_load_profile(
    frame.index,
    household,
    flexible_energy_kwh=flexible_energy_kwh,
)
scheduled_kw, recommendations = schedule_appliances(frame, appliances)
frame["optimized_load_kw"] = frame["base_load_kw"] + scheduled_kw
frame["opportunity_score"] = opportunity_score(frame)

simulated_underperformance_percent = 12
telemetry = simulate_inverter_telemetry(
    frame["solar_expected_kw"],
    simulated_underperformance_percent,
)
maintenance = diagnose_maintenance(telemetry)

optimized_flows = energy_flows(frame["solar_expected_kw"], frame["optimized_load_kw"])

forecast_energy = float(frame["solar_expected_kw"].sum())
direct_use = optimized_flows["solar_to_home"] / max(forecast_energy, 0.001)
annual_production = forecast_energy / 2 * 365
finance = simple_financial_estimate(
    annual_production,
    min(direct_use, 1),
    electricity_rate,
    installed_cost,
)
advisor_context = AdvisorContext(
    annual_consumption_kwh=household.annual_consumption_kwh,
    annual_production_kwh=float(finance["annual_production_kwh"]),
    system_capacity_kw=system.dc_capacity_kw,
    electricity_rate=electricity_rate,
    simple_payback_years=float(finance["simple_payback_years"]),
    forecast_confidence="low — demonstration only",
)

st.warning(
    "**Demo forecast:** the current weather is synthetic, not Aurora output. "
    "The interface will show the exact Aurora/ERA5 initialization time after Azure is connected."
)

st.markdown(
    f"""
    <div class="plain-language">
      <strong>What this example says:</strong> This {system.dc_capacity_kw:.1f} kW system is
      expected to make about {forecast_energy:.0f} kWh over the displayed 48 hours.
      The greenest heatmap periods are the best candidates for flexible household tasks.
      This is a grid-connected example: the grid supplies any appliance energy that solar
      does not provide.
    </div>
    """,
    unsafe_allow_html=True,
)

metric_columns = st.columns(4)
metric_columns[0].metric(
    "Your solar array",
    f"{system.dc_capacity_kw:.1f} kW",
    help=f"{system.panel_count} panels across {len(system.sections)} modeled sections.",
)
metric_columns[1].metric(
    "Solar expected in 48 hours",
    f"{forecast_energy:.1f} kWh",
    help="Energy, not instantaneous power. This uses synthetic demonstration weather.",
)
metric_columns[2].metric(
    "Solar used directly",
    f"{optimized_flows['solar_to_home']:.1f} kWh",
    help="Solar generated and consumed by household loads during the same modeled hour.",
)
metric_columns[3].metric(
    "Recommendation confidence",
    "Low — demo",
    help=(
        "Low means the recommendation demonstrates the method but the exact hour is not reliable "
        "because weather and hourly household demand are synthetic."
    ),
)

st.info(
    f"**Solar used directly** means that, out of {forecast_energy:.1f} kWh generated, "
    f"{optimized_flows['solar_to_home']:.1f} kWh occurred during the same hours as household "
    "electricity use. It was consumed in the home instead of being exported. This does not mean "
    "a particular appliance was connected directly to a panel."
)
render_advisor_chat(advisor_context)

st.subheader("1. Find the easiest hours to use solar")
st.write(
    "The heatmap summarizes the detailed forecast. **Green does not mean a circuit is safe**; "
    "it means the model expects more solar than the home's estimated non-flexible load."
)
with st.expander("How to read this heatmap"):
    st.markdown(
        """
        The display begins at midnight for readability, but only the cells from the current hour
        through the following 48 hours contain forecast data. Blank cells are outside that rolling
        forecast window.

        - **Bright green:** strong expected solar surplus; best time to consider a flexible task.
        - **Yellow:** solar may cover part of the task, but the grid may supply the remainder.
        - **Red or dark:** little solar is expected.
        - Hover over a square to see solar power, estimated non-flexible load, and the likely range.

        The score combines expected surplus with forecast uncertainty. It does not inspect
        breakers, wires, receptacles, service capacity, or appliance startup current.
        """
    )

heatmap_frame = frame.copy()
first_date = start.date()
last_date = heatmap_frame.index[-1].date()


def heatmap_date_label(timestamp: pd.Timestamp) -> str:
    day_offset = (timestamp.date() - first_date).days
    prefix = {0: "Today", 1: "Tomorrow"}.get(day_offset, "Following day")
    return f"{prefix} · {timestamp:%a %b %d}"


heatmap_frame["date"] = [heatmap_date_label(timestamp) for timestamp in heatmap_frame.index]
heatmap_frame["hour"] = [
    timestamp.strftime("%I %p").lstrip("0") for timestamp in heatmap_frame.index
]
display_days = pd.date_range(first_date, last_date, freq="D", tz=TIMEZONE)
dates = [heatmap_date_label(timestamp) for timestamp in display_days]
hours = [
    pd.Timestamp(hour=hour, year=2000, month=1, day=1).strftime("%I %p").lstrip("0")
    for hour in range(24)
]
pivot = heatmap_frame.pivot(index="date", columns="hour", values="opportunity_score")
pivot = pivot.reindex(index=dates, columns=hours)

custom = np.empty((len(dates), len(hours)), dtype=object)
for row, date in enumerate(dates):
    for column, hour in enumerate(hours):
        matches = heatmap_frame[
            (heatmap_frame["date"] == date) & (heatmap_frame["hour"] == hour)
        ]
        if matches.empty:
            custom[row, column] = (
                f"{date}, {hour}<br>Outside the rolling 48-hour forecast"
            )
            continue
        record = matches.iloc[0]
        custom[row, column] = (
            f"{date}, {hour}<br>"
            f"Expected solar: {record.solar_expected_kw:.1f} kW<br>"
            f"Likely range: {record.solar_low_kw:.1f}–{record.solar_high_kw:.1f} kW<br>"
            f"Estimated non-flexible load: {record.base_load_kw:.1f} kW"
        )

heatmap = go.Figure(
    go.Heatmap(
        z=pivot.values,
        x=hours,
        y=dates,
        customdata=custom,
        hovertemplate="%{customdata}<extra></extra>",
        colorscale=[
            [0.0, "#071526"],
            [0.25, "#bc4b3e"],
            [0.50, "#efb64c"],
            [0.75, "#72c184"],
            [1.0, "#00e6a7"],
        ],
        colorbar={"title": "Solar opportunity"},
    )
)
heatmap.update_layout(
    height=310,
    margin={"l": 20, "r": 20, "t": 10, "b": 20},
    xaxis={"title": "Local time"},
    yaxis={"title": ""},
)
st.plotly_chart(heatmap, width="stretch")

st.markdown("#### Suggested example schedule")
st.caption(
    "These are convenience recommendations, not electrical approvals. "
    "High-draw flexible examples are scheduled one at a time. Usage labels compare each "
    "appliance's running power with this household's average hourly demand."
)
recommendation_columns = st.columns(max(1, min(len(recommendations), 4)))
appliances_by_name = {appliance.name: appliance for appliance in appliances}
for column, recommendation in zip(recommendation_columns, recommendations, strict=False):
    appliance = appliances_by_name[str(recommendation["appliance"])]
    usage = classify_appliance_usage(
        appliance.power_kw,
        household.annual_consumption_kwh,
    )
    column.markdown(
        f"**{recommendation['appliance']}**  \n"
        f"{format_clock(recommendation['start'], include_day=True)}–"
        f"{format_clock(recommendation['end'])}  \n"
        f"Running power: **{appliance.power_kw:.1f} kW**  \n"
        f"Relative usage: **{usage['level']}** "
        f"({usage['relative_multiple']:.1f}× this home's average)  \n"
        f"Cycle: {recommendation['energy_kwh']:.1f} kWh  \n"
        "Recommendation confidence: **Low — demonstration only**"
    )
    column.caption(str(recommendation["safety_note"]))

with st.expander("How the recommendation was calculated"):
    st.markdown(
        f"""
        1. Each of the **{len(system.sections)} array sections** is modeled separately using its
           panel count, watts, tilt, direction, and shading.
        2. The sections are combined before applying the shared **{system.inverter_ac_kw:.1f} kW**
           inverter limit.
        3. Weather provides sunlight, air temperature, and wind.
        4. The model estimates panel temperature, DC power, losses, inverter conversion,
           and AC power.
        5. The scheduler compares modeled solar with estimated non-flexible household demand,
           then places flexible appliances in the strongest available windows.

        The annual 10,800 kWh example is converted into a 48-hour energy allowance. The model
        subtracts the flexible example cycles, then distributes the remaining energy using an
        illustrative shape: lower overnight use, a morning rise, daytime work-from-home demand,
        and a larger evening rise. It is not described as a normal or measured home.

        This is an estimate. It does not know module aging, exact horizon shading, snow coverage,
        wiring losses, inverter topology, curtailment, or actual interval household consumption.
        A utility smart-meter CSV would replace this illustrative hourly demand profile.
        """
    )

health_column, finance_column = st.columns(2)
with health_column:
    st.subheader("2. Understand system health")
    loss = maintenance["loss_percent"]
    if maintenance["severity"] == "warning":
        st.warning(f"Example issue: {loss:.1f}% below modeled expectation")
    elif maintenance["severity"] == "caution":
        st.info(f"Example issue to monitor: {loss:.1f}% below expectation")
    else:
        st.success("Production is within the modeled range")
    st.write(maintenance["message"])
    with st.expander("What does simulated inverter underperformance mean?"):
        st.markdown(
            f"""
            For the demo, the synthetic inverter reports approximately
            **{simulated_underperformance_percent}% less daylight energy** than the
            weather-adjusted model expects.

            This is not an inverter setting and does not automatically mean dirty panels.
            It demonstrates how a future real integration could compare inverter telemetry with
            weather-normalized expectations. Possible causes include weather-model error, incorrect
            panel assumptions, shading, soiling, clipping, an inverter event, or missing data.

            **Safe action:** {maintenance.get("safe_action", "Continue monitoring.")}
            """
        )

with finance_column:
    st.subheader("3. See a simple money example")
    st.metric("Annualized solar estimate", f"{finance['annual_production_kwh']:,.0f} kWh")
    st.metric("Illustrative annual energy value", f"${finance['annual_value']:,.0f}")
    st.metric("Simple payback illustration", f"{finance['simple_payback_years']:.1f} years")
    with st.expander("Show the financial assumptions and math"):
        st.markdown(
            f"""
            **Inputs**

            - Installed cost: **${installed_cost:,.0f}**
            - Illustrative electricity value: **${electricity_rate:.2f}/kWh**
            - Annualized production: **{finance["annual_production_kwh"]:,.0f} kWh**

            **Simplified math**

            `annual value = annual solar energy × illustrative electricity value`

            `simple payback = installed cost ÷ annual value`

            This deliberately excludes financing, fixed utility charges, detailed PSE rates,
            export-credit rules, incentives, taxes, degradation, maintenance, replacement costs,
            and future rate changes. Those belong in the stretch-goal tariff engine.
            """
        )

st.subheader("Confidence and assumptions")
st.write(
    "**Confidence is not the probability that a prediction will be correct.** It is a plain "
    "assessment of how much of the answer comes from measured or verified inputs versus "
    "synthetic/default assumptions."
)
confidence_table = pd.DataFrame(
    [
        {
            "Part of answer": "Solar-array model",
            "Level": "High",
            "What that means here": (
                "Panel groups, watts, direction, tilt, shading, and inverter limit are explicit."
            ),
            "What is still missing": (
                "Manufacturer curves, wiring topology, aging, and exact shade."
            ),
        },
        {
            "Part of answer": "Weather timing",
            "Level": "Low — demo",
            "What that means here": (
                "The 48-hour weather pattern is synthetic, not a live forecast."
            ),
            "What is still missing": "Validated Aurora or another live forecast with timestamps.",
        },
        {
            "Part of answer": "Hourly household demand",
            "Level": "Low — demo",
            "What that means here": (
                "Annual kWh is provided, but the hour-by-hour shape is generated from assumptions."
            ),
            "What is still missing": "Smart-meter or interval consumption data.",
        },
        {
            "Part of answer": "Suggested appliance hour",
            "Level": "Low — demo",
            "What that means here": (
                "Use it to understand the scheduling method, not as a reliable plan for this day."
            ),
            "What is still missing": "Live weather plus measured household and appliance demand.",
        },
        {
            "Part of answer": "Maintenance",
            "Level": "Simulation only",
            "What that means here": "The inverter telemetry and 12% underperformance are injected.",
            "What is still missing": "Read-only telemetry from a real inverter over time.",
        },
        {
            "Part of answer": "Financial illustration",
            "Level": "Low",
            "What that means here": "One example rate and simple payback formula are used.",
            "What is still missing": (
                "Actual tariff, export credit, incentives, financing, and fees."
            ),
        },
    ]
)
st.dataframe(confidence_table, hide_index=True, width="stretch")
st.caption(
    "**High:** required inputs are directly supplied or measured. **Medium:** key inputs are "
    "known but one important driver is modeled. **Low:** a key driver is synthetic or defaulted. "
    "Every production answer should also show missing inputs, source timestamps, and model version."
)

with st.expander("Privacy and safety boundaries"):
    st.markdown(
        """
        - No personal utility statement is used or required for the demonstration.
        - A production parser discards names, addresses, account and meter numbers, barcodes,
          and payment information before agent processing.
        - Uploaded text is data, never trusted agent instructions.
        - Solar availability does not certify appliance circuits or household electrical capacity.
        - The grid supplies shortfall in this grid-connected example.
        - No appliance is controlled automatically; the homeowner approves every action.
        - The application does not provide electrical installation, wiring, breaker, string,
          grounding, rooftop, permitting, or interconnection instructions.
        """
    )
    st.write(
        f"Weather provider: **{metadata.provider}** · Mode: **{metadata.mode}** · "
        f"Generated: **{metadata.generated_at:%Y-%m-%d %H:%M UTC}**"
    )

with st.expander("Presentation-ready stretch goals"):
    st.markdown(
        """
        1. Live Aurora initialized from compatible operational weather data.
        2. Enphase, SolarEdge, and SunSpec read-only inverter adapters.
        3. Utility smart-meter imports and learned household load profiles.
        4. Complete versioned PSE tariff, net-metering, incentive, and financing model.
        5. Proactive mobile, email, and accessibility-friendly notifications.
        6. Longer-term fault classification using real peer-array telemetry and maintenance history.
        7. Roof imagery and shading analysis without exposing a precise address to the LLM.
        8. Multilingual plain-language energy and safety education.
        9. Privacy-preserving community benchmarks and opt-in model improvement.
        10. Installer/utility handoff reports reviewed by qualified professionals.
        """
    )
