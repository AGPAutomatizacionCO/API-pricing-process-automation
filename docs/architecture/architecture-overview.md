# Architecture Overview

## Objective

Pricing Process Automation API is the corporate backend service responsible for securely exposing business information stored in enterprise databases.

The API centralizes:

* Authentication
* Authorization
* Audit logging
* Database access
* Business validations

The frontend remains exclusively responsible for user interaction.

---

## Current Architecture

```text
User
 │
 ▼
Frontend
(App Service)
 │
 ▼
Microsoft Entra ID
(Azure Easy Auth)
 │
 ▼
FastAPI Backend
 │
 ├── Authorization
 ├── Audit
 ├── Validation
 │
 ▼
Azure SQL
```

---

## Responsibilities

### Frontend

Responsibilities:

* User interface
* User experience
* Input capture
* API consumption

Not responsible for:

* Authorization
* Role validation
* Database access

---

### Backend

Responsibilities:

* Authentication validation
* Authorization
* Role management
* Audit logging
* SQL access
* Data validation

---

### Database

Responsibilities:

* Data persistence
* Business information storage

No direct access from frontend is allowed.

---

## Design Principles

* Authentication must be delegated to Microsoft Entra ID.
* Authorization must be enforced in backend.
* SQL credentials must never be exposed to frontend.
* Audit logging must be centralized.
* Business rules must be implemented server-side.
