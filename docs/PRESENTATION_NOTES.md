# Presentation notes

## MVP claim

Solar Advisor AI helps a non-engineer homeowner understand an existing solar system,
identify likely solar-rich hours, explore household changes through conversation, and
see the assumptions and confidence behind every estimate.

## Safety claim

The application recommends convenience windows, not electrical capacity. In the
grid-connected demo, the grid supplies any shortfall between solar and appliance load.
Circuit safety depends on the installed wiring, breaker, receptacle, appliance
nameplate, and simultaneous loads. High-draw demo appliances are scheduled
sequentially, but the application never certifies a circuit.

## Assumption claim

The demo uses:

- a synthetic household in ZIP 98052;
- two solar-array sections totaling 8.0 kW DC;
- 10,800 kWh annual household consumption;
- synthetic hourly consumption;
- synthetic weather until Aurora is connected;
- synthetic inverter telemetry with a 12% injected loss;
- one illustrative electricity value rather than a complete PSE tariff.

## Stretch goals for judges

1. Live Aurora initialized from compatible operational weather data.
2. Read-only vendor inverter integrations with customer OAuth.
3. Smart-meter data imports and learned household load profiles.
4. Complete versioned tariff, net-metering, incentive, and financing calculations.
5. Mobile/email notifications with consent, quiet hours, and delivery auditing.
6. Longer-term maintenance classification using real weather and peer-array telemetry.
7. Roof imagery and shading analysis without sending precise addresses to the LLM.
8. Multilingual explanations and accessibility testing.
9. Privacy-preserving opt-in community benchmarks.
10. Professional installer and utility handoff reports.
