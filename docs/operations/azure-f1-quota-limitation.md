# Azure F1 Quota Limitation

## Context

The project attempted to run:

* pricing-process-automation
* pricing-process-automation-api

inside the same App Service Plan.

Plan:

```text
ASP-AGPColombia-8785
SKU F1 Free
Brazil South
```

---

## Observed Behavior

The API deployment entered:

```text
QuotaExceeded
```

Subsequent operations impacted application availability.

---

## Technical Findings

The issue was not caused by:

* FastAPI
* Docker
* Azure SQL
* Azure Container Registry
* Microsoft Entra ID

All components were validated successfully.

---

## Root Cause

Azure App Service Free Plan reached operational limits.

---

## Lessons Learned

Before creating additional App Services:

* Validate plan capacity.
* Validate free plan limitations.
* Estimate required applications.

---

## Future Alternatives

### Option A

Upgrade App Service Plan.

### Option B

Deploy frontend and backend in a single container.

### Option C

Maintain backend in ACR until infrastructure approval.
