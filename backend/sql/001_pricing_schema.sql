/*
  001_pricing_schema.sql
  Tablas de Pricing Process (Azure SQL). Nomenclatura: App_<Area>_<Desarrollo>_<Tabla> = App_Finanzas_Pricing_*, en dbo (patron de agpc-productivity).
  Reemplaza el almacenamiento en localStorage del frontend:
    - agp_cotizaciones_v1  -> dbo.App_Finanzas_Pricing_Cotizacion + dbo.App_Finanzas_Pricing_CotizacionPieza
    - formula_library.json -> dbo.App_Finanzas_Pricing_Formula
  Idempotente: se puede ejecutar varias veces. Base destino: agpc-productivity (servidor agpcol). Revisar con TI antes de aplicar.
  Las cargas de referencia (Budget, homologacion, BD Pricing) quedan para una fase posterior.
*/

/* ---------- Cotizacion (cabecera + snapshot completo de las pestañas) ---------- */
IF OBJECT_ID('dbo.App_Finanzas_Pricing_Cotizacion', 'U') IS NULL
CREATE TABLE dbo.App_Finanzas_Pricing_Cotizacion (
    IdCotizacion        INT            IDENTITY(1,1) CONSTRAINT PK_App_Finanzas_Pricing_Cotizacion PRIMARY KEY,
    Codigo              NVARCHAR(40)   NOT NULL,            -- p.ej. COT-1727800000000 (compatible con el HTML actual)
    Fecha               DATE           NOT NULL,
    UnidadComercial     NVARCHAR(200)  NULL,
    Cliente             NVARCHAR(200)  NULL,
    Pm                  NVARCHAR(200)  NULL,
    Programa            NVARCHAR(200)  NULL,
    Estado              NVARCHAR(20)   NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_Cotizacion_Estado DEFAULT 'abierta',
    PrecioMinAprobado   DECIMAL(18,4)  NULL,
    PrecioTarget        DECIMAL(18,4)  NULL,
    SnapshotJson        NVARCHAR(MAX) NOT NULL,             -- brief, tiempos, costos, pricing, adicionales
    CreadoPor           NVARCHAR(256)  NOT NULL,
    CreadoEnUtc         DATETIME2(0)   NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_Cotizacion_Creado DEFAULT SYSUTCDATETIME(),
    ModificadoPor       NVARCHAR(256)  NULL,
    ModificadoEnUtc     DATETIME2(0)   NULL,
    Eliminada           BIT            NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_Cotizacion_Elim DEFAULT 0,
    RowVer              ROWVERSION     NOT NULL,            -- concurrencia optimista (ETag)
    CONSTRAINT CK_App_Finanzas_Pricing_Cotizacion_Estado CHECK (Estado IN ('abierta', 'archivada')),
    CONSTRAINT CK_App_Finanzas_Pricing_Cotizacion_Json   CHECK (ISJSON(SnapshotJson) = 1)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_App_Finanzas_Pricing_Cotizacion_Codigo')
    CREATE UNIQUE INDEX UX_App_Finanzas_Pricing_Cotizacion_Codigo ON dbo.App_Finanzas_Pricing_Cotizacion (Codigo);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_App_Finanzas_Pricing_Cotizacion_Listado')
    CREATE INDEX IX_App_Finanzas_Pricing_Cotizacion_Listado ON dbo.App_Finanzas_Pricing_Cotizacion (Eliminada, Estado, Fecha DESC)
        INCLUDE (Codigo, Cliente, UnidadComercial, Pm);
GO

/* ---------- Piezas del Brief (consultables sin parsear el JSON) ---------- */
IF OBJECT_ID('dbo.App_Finanzas_Pricing_CotizacionPieza', 'U') IS NULL
CREATE TABLE dbo.App_Finanzas_Pricing_CotizacionPieza (
    IdPieza       INT           IDENTITY(1,1) CONSTRAINT PK_App_Finanzas_Pricing_CotizacionPieza PRIMARY KEY,
    IdCotizacion  INT           NOT NULL
        CONSTRAINT FK_App_Finanzas_Pricing_CotizacionPieza_Cotizacion REFERENCES dbo.App_Finanzas_Pricing_Cotizacion (IdCotizacion) ON DELETE CASCADE,
    Linea         INT           NOT NULL,
    PartNo        NVARCHAR(100) NULL,
    Descripcion   NVARCHAR(300) NULL,
    Superficie    NVARCHAR(50)  NULL,
    AnchoMm       DECIMAL(12,2) NULL,
    AltoMm        DECIMAL(12,2) NULL,
    Piezas        INT           NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_CotPieza_Pcs  DEFAULT 1,
    Sets          INT           NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_CotPieza_Sets DEFAULT 1,
    FormulaCode   NVARCHAR(50)  NULL,
    Color         NVARCHAR(100) NULL,
    Bb            NVARCHAR(100) NULL,
    Feat          NVARCHAR(300) NULL,
    CONSTRAINT UX_App_Finanzas_Pricing_CotizacionPieza_Linea UNIQUE (IdCotizacion, Linea)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_App_Finanzas_Pricing_CotizacionPieza_Formula')
    CREATE INDEX IX_App_Finanzas_Pricing_CotizacionPieza_Formula ON dbo.App_Finanzas_Pricing_CotizacionPieza (FormulaCode);
GO

/* ---------- Biblioteca de formulas (antes formula_library.json) ---------- */
IF OBJECT_ID('dbo.App_Finanzas_Pricing_Formula', 'U') IS NULL
CREATE TABLE dbo.App_Finanzas_Pricing_Formula (
    IdFormula       INT            IDENTITY(1,1) CONSTRAINT PK_App_Finanzas_Pricing_Formula PRIMARY KEY,
    Code            NVARCHAR(50)   NOT NULL,
    Nombre          NVARCHAR(300)  NULL,
    Nivel           NVARCHAR(10)   NULL,
    Geo             NVARCHAR(50)   NULL,
    TipoProd        NVARCHAR(100)  NULL,
    Area            DECIMAL(12,4)  NULL,
    EspesorMm       DECIMAL(10,2)  NULL,
    RechPct         DECIMAL(9,6)   NULL,
    EmpqM2          DECIMAL(12,4)  NULL,
    PintM2          DECIMAL(12,4)  NULL,
    TecoM2          DECIMAL(12,4)  NULL,
    CostoTotal      DECIMAL(18,4)  NULL,
    DetalleJson     NVARCHAR(MAX) NOT NULL,                 -- rows (materiales), bh/bi, sizes, etc.
    CreadoPor       NVARCHAR(256)  NOT NULL,
    CreadoEnUtc     DATETIME2(0)   NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_Formula_Creado DEFAULT SYSUTCDATETIME(),
    ModificadoPor   NVARCHAR(256)  NULL,
    ModificadoEnUtc DATETIME2(0)   NULL,
    Eliminada       BIT            NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_Formula_Elim DEFAULT 0,
    RowVer          ROWVERSION     NOT NULL,
    CONSTRAINT CK_App_Finanzas_Pricing_Formula_Json CHECK (ISJSON(DetalleJson) = 1)
);
GO

-- Code unico solo entre formulas no eliminadas
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_App_Finanzas_Pricing_Formula_Code_Activa')
    CREATE UNIQUE INDEX UX_App_Finanzas_Pricing_Formula_Code_Activa ON dbo.App_Finanzas_Pricing_Formula (Code) WHERE Eliminada = 0;
GO

/* ---------- Auditoria (solo inserciones) ---------- */
IF OBJECT_ID('dbo.App_Finanzas_Pricing_Auditoria', 'U') IS NULL
CREATE TABLE dbo.App_Finanzas_Pricing_Auditoria (
    IdAuditoria   BIGINT         IDENTITY(1,1) CONSTRAINT PK_App_Finanzas_Pricing_Auditoria PRIMARY KEY,
    FechaUtc      DATETIME2(3)   NOT NULL CONSTRAINT DF_App_Finanzas_Pricing_Auditoria_Fecha DEFAULT SYSUTCDATETIME(),
    UsuarioEmail  NVARCHAR(256)  NOT NULL,
    Rol           NVARCHAR(20)   NULL,
    Evento        NVARCHAR(60)   NOT NULL,                  -- COTIZACION_CREADA, FORMULA_ELIMINADA, ...
    Entidad       NVARCHAR(40)   NOT NULL,
    EntidadId     NVARCHAR(60)   NULL,
    Resultado     NVARCHAR(20)   NOT NULL,
    Ip            NVARCHAR(64)   NULL,
    DetalleJson   NVARCHAR(MAX)  NULL,
    CONSTRAINT CK_App_Finanzas_Pricing_Auditoria_Json CHECK (DetalleJson IS NULL OR ISJSON(DetalleJson) = 1)
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_App_Finanzas_Pricing_Auditoria_Entidad')
    CREATE INDEX IX_App_Finanzas_Pricing_Auditoria_Entidad ON dbo.App_Finanzas_Pricing_Auditoria (Entidad, EntidadId, FechaUtc DESC);
GO
