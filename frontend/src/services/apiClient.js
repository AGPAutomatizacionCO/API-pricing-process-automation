const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      payload && typeof payload === "object"
        ? payload.detail || payload.message || JSON.stringify(payload)
        : payload;

    const error = new Error(detail || `HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return payload;
}

export function getHealth() {
  return request("/health", { method: "GET" });
}

export function postAuthSession(idToken) {
  return request("/auth/session", {
    method: "POST",
    body: JSON.stringify({ id_token: idToken })
  });
}

export function getCurrentSession() {
  return request("/auth/me", { method: "GET" });
}

export function postLogout() {
  return request("/auth/logout", { method: "POST" });
}

export function getDbTest() {
  return request("/api/db/test", { method: "GET" });
}

export function getDatabases() {
  return request("/api/db/databases", { method: "GET" });
}

export function getTables(limit = 50) {
  return request(`/api/db/tables?limit=${limit}`, { method: "GET" });
}