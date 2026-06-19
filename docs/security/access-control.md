# Access Control

## Current Model

Access control is currently configuration-based.

Environment variables:

```text
ADMIN_USERS
ANALYST_USERS
VIEWER_USERS
```

Example:

```text
ADMIN_USERS=user1@agpglass.com,user2@agpglass.com

ANALYST_USERS=user3@agpglass.com

VIEWER_USERS=user4@agpglass.com
```

---

## Authorization Logic

When a user is authenticated:

1. Backend reads the user identity.
2. Backend evaluates configured user lists.
3. Backend assigns the highest available role.
4. Backend validates endpoint permissions.

---

## Temporary Solution

This implementation is intended for MVP and validation stages.

---

## Future Evolution

Future versions should replace static lists with:

* Corporate directory integration
* Database-driven role management
* Centralized authorization service
