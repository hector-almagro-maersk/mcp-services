#!/bin/bash

# Script de prueba para el servidor MCP SQL Server
# Cambia la connection string por la tuya

CONNECTION_STRING="Server=localhost,1433;Database=master;User Id=sa;Password=YourPassword123;Encrypt=true;TrustServerCertificate=true;"

echo "Iniciando servidor MCP SQL Server..."
echo "Connection String: $CONNECTION_STRING"
echo ""
echo "Para probar el servidor, usa un cliente MCP o Claude Desktop"
echo "El servidor estará corriendo hasta que presiones Ctrl+C"
echo ""

node dist/index.js "$CONNECTION_STRING"