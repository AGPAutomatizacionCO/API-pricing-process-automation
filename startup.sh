#!/bin/bash
# Startup script para Azure App Service
# Instala ODBC Driver 17 si no está instalado
if ! command -v odbcinst &> /dev/null; then
    echo "Instalando ODBC Driver 17..."
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
    apt-get update -y
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev
fi

# Arrancar la API
cd /home/site/wwwroot
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
