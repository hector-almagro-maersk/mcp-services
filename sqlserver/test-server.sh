#!/bin/bash

# Test script for the MCP SQL Server
# Change the connection string to yours

CONNECTION_STRING="Server=localhost,1433;Database=master;User Id=sa;Password=YourPassword123;Encrypt=true;TrustServerCertificate=true;"

echo "Starting MCP SQL Server..."
echo "Connection String: $CONNECTION_STRING"
echo ""
echo "To test the server, use an MCP client or Claude Desktop"
echo "The server will run until you press Ctrl+C"
echo ""

node dist/index.js "$CONNECTION_STRING"