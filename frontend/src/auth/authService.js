import { msalInstance } from "./msalInstance";
import { loginRequest } from "./msalConfig";
import {
  getCurrentSession,
  postAuthSession,
  postLogout
} from "../services/apiClient";

export async function initializeMicrosoftAuth() {
  await msalInstance.initialize();

  const response = await msalInstance.handleRedirectPromise();

  if (response?.account) {
    msalInstance.setActiveAccount(response.account);
  }

  const accounts = msalInstance.getAllAccounts();

  if (!msalInstance.getActiveAccount() && accounts.length > 0) {
    msalInstance.setActiveAccount(accounts[0]);
  }

  return msalInstance.getActiveAccount();
}

export async function loginWithMicrosoft() {
  await msalInstance.loginRedirect(loginRequest);
}

export async function logoutFromMicrosoft() {
  await postLogout().catch(() => null);

  const account = msalInstance.getActiveAccount();

  await msalInstance.logoutRedirect({
    account,
    postLogoutRedirectUri: import.meta.env.VITE_ENTRA_REDIRECT_URI
  });
}

export function getActiveAccount() {
  return msalInstance.getActiveAccount();
}

export async function acquireIdToken() {
  const account = getActiveAccount();

  if (!account) {
    throw new Error("No active Microsoft account.");
  }

  const response = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account
  });

  return response.idToken;
}

export async function restoreBackendSession() {
  try {
    return await getCurrentSession();
  } catch (error) {
    if (error.status === 401) {
      return null;
    }

    throw error;
  }
}

export async function createBackendSession() {
  const idToken = await acquireIdToken();
  return postAuthSession(idToken);
}