import { useEffect, useState } from "react";

import {
  initializeMicrosoftAuth,
  getActiveAccount,
  loginWithMicrosoft,
  createBackendSession,
  restoreBackendSession,
  logoutFromMicrosoft
} from "./auth/authService";

import {
  getDbTest,
  getDatabases,
  getTables
} from "./services/apiClient";

import "./css/styles.css";

export default function App() {
  const [account, setAccount] = useState(null);
  const [session, setSession] = useState(null);
  const [dbTest, setDbTest] = useState(null);
  const [databases, setDatabases] = useState(null);
  const [tables, setTables] = useState(null);
  const [error, setError] = useState(null);

  async function loadProtectedDbTest() {
    setError(null);

    try {
      const result = await getDbTest();
      setDbTest(result);
    } catch (ex) {
      setError(ex.message);
    }
  }

  async function loadDatabases() {
    setError(null);

    try {
      const result = await getDatabases();
      setDatabases(result);
    } catch (ex) {
      setError(ex.message);
    }
  }

  async function loadTables() {
    setError(null);

    try {
      const result = await getTables(50);
      setTables(result);
    } catch (ex) {
      setError(ex.message);
    }
  }

  useEffect(() => {
    async function initialize() {
      setError(null);

      try {
        await initializeMicrosoftAuth();

        const activeAccount = getActiveAccount();
        setAccount(activeAccount);

        if (!activeAccount) return;

        const existingSession = await restoreBackendSession();

        if (existingSession) {
          setSession(existingSession);
          return;
        }

        const newSession = await createBackendSession();
        setSession(newSession);
      } catch (ex) {
        setError(ex.message);
      }
    }

    initialize();
  }, []);

  return (
    <main className="app-shell">
      <section className="app-card">
        <h1 className="app-title">Pricing Process Automation</h1>
        <p className="app-subtitle">
          Acceso corporativo protegido con Microsoft Entra ID.
        </p>

        {account && <p>Usuario: <strong>{account.username}</strong></p>}

        <div className="button-row">
          {!account && (
            <button className="primary-button" onClick={loginWithMicrosoft}>
              Login Microsoft
            </button>
          )}

          {account && (
            <>
              <button className="danger-button" onClick={logoutFromMicrosoft}>
                Logout
              </button>

              <button className="secondary-button" onClick={loadProtectedDbTest}>
                Probar API protegida
              </button>

              <button className="secondary-button" onClick={loadDatabases}>
                Listar bases
              </button>

              <button className="secondary-button" onClick={loadTables}>
                Listar tablas
              </button>
            </>
          )}
        </div>

        <div className="panel">
          <h2>Sesión backend</h2>
          <pre>{JSON.stringify(session, null, 2)}</pre>
        </div>

        <div className="panel">
          <h2>API protegida</h2>
          <pre>{JSON.stringify(dbTest, null, 2)}</pre>
        </div>

        <div className="panel">
          <h2>Bases de datos</h2>
          <pre>{JSON.stringify(databases, null, 2)}</pre>
        </div>

        <div className="panel">
          <h2>Tablas</h2>
          <pre>{JSON.stringify(tables, null, 2)}</pre>
        </div>

        {error && (
          <div className="panel">
            <h2>Error</h2>
            <pre className="error-box">{error}</pre>
          </div>
        )}
      </section>
    </main>
  );
}