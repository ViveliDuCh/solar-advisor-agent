# Shared Microsoft Foundry + ERA5 setup

This setup must be completed by an Azure subscription owner. Never paste credentials
into chat, source control, issues, screenshots, or the recorded demonstration.

## 1. Verify Azure access

1. Sign in to the Azure portal.
2. Open **Subscriptions**, choose the active subscription, and use **Access control
   (IAM) > View my access**.
3. One teammate must be able to create resources and assign roles. The other teammate
   will receive project-scoped access rather than shared keys.

## 2. Create the resource group

Create `rg-solar-advisor-hackathon`. Select a region where Aurora-1.5 appears in the
Microsoft Foundry model catalog. Do not pick a region before confirming model
availability.

### Confirm the Aurora region before creating the Foundry project

Aurora-1.5 is a Preview custom model, so the live Foundry catalog and deployment
wizard are the source of truth. Do not rely on a generic Foundry-region table.

1. Sign in to Microsoft Foundry using the directory that contains the Azure
   subscription.
2. Open **Discover > Models**.
3. Search for `Aurora-1.5` and open the Microsoft model card.
4. Use the catalog's **Region** filter to test candidate regions.
5. Select **Use this model** or **Deploy**.
6. In the deployment wizard, inspect the eligible project/resource regions.
7. If an existing project is not eligible or the wizard reports **Region not
   supported**, cancel rather than deploying a different model.
8. Create the Foundry project in one of the regions accepted by the Aurora deployment
   wizard.
9. Open **Manage > Quota**, enable **Show all**, and check the selected region for any
   required capacity or subscription restriction.
10. Treat a successfully created Aurora deployment and healthy endpoint as final
    confirmation.

The resource group's metadata location does not prove that Aurora is available.
The Foundry resource/project region and model deployment eligibility are what matter.

### Aurora card redirects to the Foundry home page

If Aurora is visible under **All models** but selecting the card returns to the project
home page:

1. Confirm that the card does not expose **Deploy**, a deployment template, an
   accelerator, or a model ID.
2. If the portal exposes a **Switch to classic** action in its account/help menu, use
   it and check the classic **Model catalog** for a **Deploy** action. Many tenants do
   not expose this switch; do not search for or depend on it.
3. If there is no switch, or no **Deploy** action appears, use **Request a model** and
   open an Azure support request. Include the subscription offer type, Foundry resource
   region, model name, and the fact that the card redirects without a deployment wizard.
4. Do not create additional Foundry projects until model entitlement or supported
   project type is confirmed.

Visual Studio/FTE development credits can create Azure resources, but some preview
model offers can have additional subscription eligibility requirements. Available
managed-compute accelerator quota does not by itself prove access to a specific model
or deployment template.

Recommended resource names:

```text
Resource group: rg-solar-advisor-hackathon
Foundry resource: solar-advisor-foundry
Foundry project: solar-advisor-ai
Storage account: globally unique generated name
Blob container: aurora-runs
```

## 3. Create the Foundry project and share it

1. Open Microsoft Foundry and create a Foundry resource and project.
2. At the Foundry resource scope, assign the teammate **Reader**.
3. At the project scope, assign the teammate **Foundry User**.
4. Assign the project managed identity **Foundry User** if the project creation flow
   did not do so automatically.
5. Do not share API keys. Each teammate authenticates with their own Microsoft Entra
   identity.

Only the owner needs permission to assign roles. A teammate who only calls an
already-deployed endpoint can later be reduced to **Foundry Agent Consumer**.

## 4. Deploy Aurora 1.5

1. In the Foundry model catalog, search for `Aurora-1.5`.
2. Open the model card and confirm regional availability, pricing, and quota.
3. Deploy the catalog custom model.
4. Record the deployment/model name and endpoint in a password manager.
5. Put them in local `.env` values; never commit them.

Aurora and the chat model used by Agent Framework are separate deployments. The app
can run without the conversational model, but Aurora requires its own endpoint.

## 5. Create private Blob Storage

1. Create a general-purpose v2 storage account in the same region when possible.
2. Disable public blob access.
3. Create a private container named `aurora-runs`.
4. Give both developers **Storage Blob Data Contributor** only if both need to inspect
   artifacts.
5. Prefer Microsoft Entra authentication for normal management.
6. For Aurora's Foundry transfer channel, create a container-scoped SAS with only the
   read/create/write/list permissions required by the client and an expiration after
   the hackathon.
7. Store the complete SAS URL only in `.env` or a secret store.

## 6. Create Copernicus CDS access

Each developer who downloads ERA5 should:

1. Create their own Climate Data Store account.
2. Accept the terms on every ERA5 dataset used.
3. Create an API key.
4. Store the API key locally; do not share one developer's credential.

ERA5T normally trails real time by approximately five days. Therefore:

- **Fixed replay** is the reliable recorded demonstration.
- **Latest complete ERA5T** is a delayed near-real-time replay, not today's forecast.
- A future operational provider should initialize Aurora from compatible current IFS
  data.

## 7. Configure each developer workstation

```powershell
Copy-Item .env.example .env
az login
```

Populate the local `.env` without committing it:

```text
FOUNDRY_PROJECT_ENDPOINT=
FOUNDRY_MODEL=
AURORA_FOUNDRY_ENDPOINT=
AURORA_FOUNDRY_TOKEN=
AURORA_BLOB_SAS_URL=
CDS_API_URL=https://cds.climate.copernicus.eu/api
CDS_API_KEY=
```

Use `az login` and Microsoft Entra authentication for the Agent Framework chat
client. The Aurora custom endpoint currently uses the credential mechanism documented
by its model deployment.

## 8. Validate access

Both developers should independently verify:

1. They can open the Foundry project.
2. They can see the Aurora deployment.
3. They can list the private `aurora-runs` container using their own identity.
4. The owner can create and revoke the temporary SAS.
5. The `.env` file is ignored by Git.
6. `streamlit run app.py` works without any cloud credentials using simulation mode.

## 9. Data retention

- Keep global ERA5/Aurora artifacts in Blob Storage, not Git.
- Store only a compact, validated ZIP-level Parquet forecast for the demo.
- Use lifecycle rules to delete temporary global input/output blobs after the event.
- Never upload utility statements or customer telemetry to the shared demo container.
