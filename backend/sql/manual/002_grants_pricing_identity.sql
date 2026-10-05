/*
  002_grants_pricing_identity.sql  — EJECUCION MANUAL por TI / admin de la base (NO lo ejecuta ningun workflow).
  Crea el usuario de la base para la Managed Identity de la web app y le da el MINIMO necesario sobre las 4 tablas de Pricing.
  Base: agpc-productivity (servidor agpcol). Requiere ejecutarse conectado como administrador Entra del servidor.

  1) Reemplazar <IDENTIDAD> por el NOMBRE de la identidad administrada asignada a la web app
     (la de la app es "ua-id-b4fa", clientId f213fbe2-1a27-4fc0-bdfc-0b49bd821218; si TI prefiere una identidad
      exclusiva para pricing, crear otra y poner aqui su nombre).
  2) En la web app: SQL_AUTH_MODE=msi y SQL_MSI_CLIENT_ID=<clientId de esa identidad>  (sin SQL_USERNAME/SQL_PASSWORD).

  Principio: nada de db_datareader/db_datawriter (darian acceso a las 700+ tablas de la base). Solo estas 4 tablas.
*/

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'<IDENTIDAD>')
    CREATE USER [<IDENTIDAD>] FROM EXTERNAL PROVIDER;
GO

-- Cotizaciones y formulas: leer, crear y editar (el borrado es logico: no necesita DELETE).
GRANT SELECT, INSERT, UPDATE ON dbo.App_Finanzas_Pricing_Cotizacion TO [<IDENTIDAD>];
GRANT SELECT, INSERT, UPDATE ON dbo.App_Finanzas_Pricing_Formula    TO [<IDENTIDAD>];

-- Piezas: la API reemplaza las piezas de una cotizacion al editarla (DELETE + INSERT).
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.App_Finanzas_Pricing_CotizacionPieza TO [<IDENTIDAD>];

-- Auditoria: solo insertar (la API no la lee ni la modifica; nadie debe poder alterar el historial desde la app).
GRANT INSERT ON dbo.App_Finanzas_Pricing_Auditoria TO [<IDENTIDAD>];
GO

/* Verificacion (debe listar exactamente estos permisos y ninguno mas sobre otras tablas):
SELECT OBJECT_NAME(major_id) AS tabla, permission_name
FROM sys.database_permissions
WHERE grantee_principal_id = USER_ID(N'<IDENTIDAD>') AND class = 1
ORDER BY tabla, permission_name;
*/

/* Revertir:
REVOKE SELECT, INSERT, UPDATE, DELETE ON dbo.App_Finanzas_Pricing_Cotizacion        FROM [<IDENTIDAD>];
REVOKE SELECT, INSERT, UPDATE, DELETE ON dbo.App_Finanzas_Pricing_Formula           FROM [<IDENTIDAD>];
REVOKE SELECT, INSERT, UPDATE, DELETE ON dbo.App_Finanzas_Pricing_CotizacionPieza   FROM [<IDENTIDAD>];
REVOKE INSERT                         ON dbo.App_Finanzas_Pricing_Auditoria         FROM [<IDENTIDAD>];
DROP USER [<IDENTIDAD>];
*/
