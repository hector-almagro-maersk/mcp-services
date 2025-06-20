# MCP Services Collection

Esta colección contiene múltiples servidores MCP (Model Context Protocol) para diferentes servicios.

## Servicios Disponibles

### 🗃️ SQL Server (`sqlserver/`)
Servidor MCP para realizar consultas de solo lectura en bases de datos SQL Server.

- **Características**: Solo lectura, validación estricta de seguridad
- **Herramientas**: `execute_query`, `list_tables`, `describe_table`
- **Documentación**: [sqlserver/README.md](sqlserver/README.md)

## Estructura del Repositorio

```
mcp-services/
├── README.md                 # Este archivo
├── sqlserver/               # Servidor MCP para SQL Server
│   ├── README.md
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   └── index.ts
│   ├── SECURITY_TESTS.md
│   ├── test-server.sh
│   └── mcp-config-example.json
└── [otros-servicios]/       # Futuros servicios MCP
```

## Agregar Nuevos Servicios

Para agregar un nuevo servicio MCP:

1. Crea una nueva carpeta con el nombre del servicio
2. Incluye todos los archivos necesarios del servicio
3. Agrega documentación específica del servicio
4. Actualiza este README con la nueva información

## Configuración General

Cada servicio incluye:
- `README.md` - Documentación específica del servicio
- `package.json` - Dependencias y scripts
- `src/` - Código fuente del servidor MCP
- `mcp-config-example.json` - Ejemplo de configuración para Claude Desktop

## Contribuir

Para contribuir con nuevos servicios o mejoras:

1. Fork este repositorio
2. Crea una rama para tu servicio/mejora
3. Agrega tu servicio en una carpeta separada
4. Actualiza la documentación
5. Envía un Pull Request