# MCP SQL Server Server

Un servidor MCP (Model Context Protocol) simple para realizar consultas de solo lectura en bases de datos SQL Server.

## Características

- ✅ **Solo lectura**: Únicamente permite consultas `SELECT`
- ✅ **Validación estricta**: Múltiples capas de seguridad
- ✅ **Connection string por parámetro**: Se pasa al iniciar el servidor
- ✅ **Tres herramientas disponibles**:
  - `execute_query`: Ejecuta consultas SQL SELECT
  - `list_tables`: Lista todas las tablas de la base de datos
  - `describe_table`: Describe la estructura de una tabla

## Seguridad Implementada

### ✅ **Permitido:**
- Consultas `SELECT` simples y complejas
- `JOIN`, `GROUP BY`, `ORDER BY`, `HAVING`
- Subconsultas y CTEs (solo con SELECT)
- Funciones agregadas (`COUNT`, `SUM`, `AVG`, etc.)

### ❌ **Bloqueado:**
- **Operaciones de escritura**: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`
- **Múltiples statements**: Consultas separadas por `;` 
- **Funciones del sistema**: `xp_cmdshell`, `sp_configure`, `OPENROWSET`, etc.
- **Comentarios**: `--` y `/* */` por seguridad
- **Variables**: `DECLARE`, `SET` para prevenir inyección
- **Procedimientos**: `EXEC`, `sp_executesql`
- **CTEs maliciosos**: Common Table Expressions con operaciones de escritura

Ver `SECURITY_TESTS.md` para ejemplos detallados.

## Instalación

```bash
cd sqlserver
npm install
npm run build
```

## Uso

```bash
node dist/index.js "Server=localhost;Database=mydb;User Id=user;Password=pass;Encrypt=true;TrustServerCertificate=true;"
```

## Tools disponibles

1. **execute_query**: Ejecuta consultas SELECT
2. **list_tables**: Lista todas las tablas de la base de datos
3. **describe_table**: Describe la estructura de una tabla específica

## Formato de Connection String

```
Server=servidor;Database=basededatos;User Id=usuario;Password=contraseña;Encrypt=true;TrustServerCertificate=true;
```

## Ejemplo de configuración en Claude Desktop

Agrega esto a tu archivo de configuración de Claude Desktop:

```json
{
  "mcpServers": {
    "sqlserver": {
      "command": "node",
      "args": [
        "/ruta/a/tu/proyecto/sqlserver/dist/index.js",
        "Server=localhost;Database=mydb;User Id=user;Password=pass;Encrypt=true;TrustServerCertificate=true;"
      ]
    }
  }
}
```