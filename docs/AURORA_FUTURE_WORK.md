# Aurora future integration work

Aurora remains an explicit stretch goal. The application must not describe synthetic
or third-party weather as Aurora output.

## Why the current computer is not the Aurora host

The development computer has 32 GB of system RAM and an Intel Arc 140V integrated GPU.
System RAM is not equivalent to dedicated GPU memory. Aurora 1.5 operates on a global
0.25-degree atmospheric grid and is designed for accelerator-backed PyTorch inference.
The complete workload is not a practical local target on this Intel integrated GPU:

- the documented full-model path expects substantially more accelerator memory;
- the common inference path uses NVIDIA CUDA-capable hardware;
- CPU execution of global hourly rollouts would be too slow and memory-constrained for
  a reliable interactive demonstration.

The correct architecture is remote inference through Microsoft Foundry or a dedicated
cloud GPU, followed by a compact location-level forecast cached for the household app.

## Phase 1: obtain model deployment access

1. Receive approval for Aurora-1.5 in the Foundry model catalog.
2. Use an approved internal development/BAMI subscription.
3. Assign the deployment operator **Cognitive Services Contributor** or an equivalent
   Foundry owner role at the Foundry resource scope.
4. Confirm the model card exposes **Deploy**, a compatible deployment template, and an
   accelerator.
5. Deploy one instance and wait for provisioning state `Succeeded`.
6. Record the model name, endpoint, region, accelerator, version, and deployment state.
7. Store endpoint credentials only in a local secret store or Key Vault.

## Phase 2: create secure transfer storage

1. Create a private Blob Storage container named `aurora-runs`.
2. Disable public blob access.
3. Give developers individual Entra-based access rather than shared account keys.
4. Generate a short-lived container SAS with the exact read/write rights required by
   the Aurora client.
5. Add lifecycle rules that delete global intermediate artifacts after the agreed
   retention period.
6. Keep household bills and inverter telemetry out of this container.

## Phase 3: prepare a fixed ERA5 replay

Start with the official-style 1 January 2023 replay because it is reproducible.

Download ERA5 single-level inputs at 00:00 and 06:00:

```text
2m temperature
10m u/v wind
mean sea-level pressure
2m dewpoint
total-column water vapour
total cloud cover
100m u/v wind
surface pressure
low/medium/high cloud cover
skin temperature
soil temperature level 1
volumetric soil water layer 1
sea-ice cover
snow depth
```

Download ERA5 pressure-level inputs:

```text
temperature
u wind
v wind
specific humidity
geopotential
```

At pressure levels:

```text
50, 100, 150, 200, 250, 300, 400,
500, 600, 700, 850, 925, 1000 hPa
```

Download Aurora 1.5's 36 static variables from the Microsoft Aurora model package.
Calculate insolation for both history timestamps.

## Phase 4: validate and construct the Aurora batch

Before submission, validate:

- all required variables and pressure levels exist;
- input history contains the two expected six-hour states;
- units and canonical Aurora variable names match;
- latitude is ordered north to south;
- longitude is in `[0, 360)`;
- global dimensions match;
- missing values are investigated rather than silently replaced;
- model/checkpoint and static-variable versions match.

Create an `aurora.Batch` with:

```text
surface variables: batch x history x latitude x longitude
atmospheric variables: batch x history x pressure x latitude x longitude
static variables: latitude x longitude
metadata: latitude, longitude, initialization time, pressure levels
```

Persist an input manifest containing checksums, source datasets, model version, and
timestamps so every forecast is reproducible.

## Phase 5: submit to Foundry

1. Create `FoundryClient` from the secret endpoint and token.
2. Create `BlobStorageChannel` from the short-lived SAS container URL.
3. Submit with model `aurora-0.25-v1.5`.
4. Request eight six-hour main steps for a 48-hour horizon.
5. Request fine lead times 1 through 6 for hourly output.
6. Save only weather variables required by the household PV pipeline.
7. Treat timeout, incomplete output, missing fields, and stale initialization as
   explicit failure states.

## Phase 6: convert global output to household weather

1. Convert ZIP 98052 to a non-sensitive representative centroid.
2. Locate the four surrounding Aurora grid cells.
3. Bilinearly interpolate each requested variable.
4. Keep UTC internally and create Pacific-time presentation columns.
5. Convert Aurora radiation output to the irradiance representation required by
   `pvlib`.
6. Pass radiation, temperature, and wind into the existing array-section PV model.
7. Export a compact Parquet artifact with:

```text
timestamp
irradiance
cloud information
temperature
wind
forecast low/expected/high values
model name and version
initialization source and timestamp
prediction creation timestamp
```

## Phase 7: integrate with the application

Complete `AuroraPipeline.run` and load the resulting artifact through
`CachedAuroraForecastProvider`.

The UI must show:

- Aurora model/version;
- ERA5 initialization timestamp;
- prediction creation timestamp;
- fixed replay versus delayed/latest mode;
- age/staleness;
- uncertainty method;
- fallback provider, if used.

Never catch an Aurora failure and silently present another provider as Aurora.

## Phase 8: validate scientific and software behavior

- Compare a fixed Aurora replay against observed ERA5 hours not used as input.
- Compare PV output against PVWatts or a known inverter dataset.
- Test zero/nighttime radiation.
- Test timezone and daylight-saving transitions.
- Test missing variables, incomplete files, stale forecasts, Blob failures, and
  endpoint failures.
- Verify energy conservation through solar, home, grid, and battery flows.
- Confirm secrets and global artifacts are absent from Git.

## Phase 9: operational-current forecast

ERA5 and ERA5T are delayed reanalysis products. A production live forecast requires a
current initialization source compatible with the deployed Aurora checkpoint, such as
the required IFS/HRES fields under appropriate access terms.

This phase must verify:

- availability of every required Aurora input;
- licensing and redistribution rights;
- run cadence and latency;
- incomplete-cycle behavior;
- forecast quality for rooftop-scale decisions;
- operational cost and endpoint scaling.
