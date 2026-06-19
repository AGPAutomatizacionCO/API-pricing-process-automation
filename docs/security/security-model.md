# Security Model

## Authentication

Authentication is delegated to Microsoft Entra ID through Azure App Service Easy Auth.

The backend trusts identity information provided by Easy Auth.

Authentication flow:

```text
User
 ↓
Microsoft Entra ID
 ↓
Azure Easy Auth
 ↓
Backend
```

---

## Authorization

Authorization is executed exclusively by backend services.

Frontend authorization is not trusted.

---

## Roles

Supported roles:

* ADMIN
* ANALYST
* VIEWER

Role hierarchy:

```text
ADMIN
 └─ ANALYST
     └─ VIEWER
```

---

## Audit

Every protected operation must generate audit information.

Audit events include:

* User
* Timestamp
* Operation
* Result
* Resource

---

## Database Security

Database credentials remain server-side.

Users never connect directly to SQL Server.

---

## Security Objectives

Mitigate:

* XSS privilege escalation
* Client-side role manipulation
* Direct SQL access
* Credential exposure
* Unauthorized API access
