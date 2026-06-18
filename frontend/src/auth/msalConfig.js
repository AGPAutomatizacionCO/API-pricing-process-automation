const requiredEnv = (key) => {
  const value = import.meta.env[key];

  if (!value) {
    console.warn(`Missing environment variable: ${key}`);
  }

  return value || "";
};

export const msalConfig = {
  auth: {
    clientId: requiredEnv("VITE_ENTRA_CLIENT_ID"),
    authority: requiredEnv("VITE_ENTRA_AUTHORITY"),
    redirectUri: requiredEnv("VITE_ENTRA_REDIRECT_URI"),
    postLogoutRedirectUri: requiredEnv("VITE_ENTRA_REDIRECT_URI")
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false
  }
};

export const loginRequest = {
  scopes: ["openid", "profile", "email"]
};