/*
  ROLLBACK de 001_pricing_schema.sql. DESTRUCTIVO: borra las 4 tablas y TODOS sus datos.
  Solo ejecutar a mano, con autorizacion, y tras respaldar. No lo ejecuta ningun workflow.
*/
DROP TABLE IF EXISTS dbo.App_Finanzas_Pricing_CotizacionPieza;
DROP TABLE IF EXISTS dbo.App_Finanzas_Pricing_Cotizacion;
DROP TABLE IF EXISTS dbo.App_Finanzas_Pricing_Formula;
DROP TABLE IF EXISTS dbo.App_Finanzas_Pricing_Auditoria;
