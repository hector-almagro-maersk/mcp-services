#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import sql from 'mssql';

class SQLServerMCPServer {
  private server: Server;
  private pool: sql.ConnectionPool | null = null;
  private connectionString: string;

  constructor() {
    this.server = new Server(
      {
        name: "mcp-sqlserver-server",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Obtener connection string del parámetro
    this.connectionString = process.argv[2];
    if (!this.connectionString) {
      console.error("Error: Debes proporcionar una connection string como parámetro");
      console.error("Uso: node dist/index.js \"Server=localhost;Database=mydb;User Id=user;Password=pass;\"");
      process.exit(1);
    }

    this.setupToolHandlers();
  }

  private async connectToDatabase(): Promise<void> {
    if (this.pool && this.pool.connected) {
      return;
    }

    try {
      this.pool = new sql.ConnectionPool(this.connectionString);
      await this.pool.connect();
      console.error("Conectado a SQL Server");
    } catch (error) {
      console.error("Error conectando a la base de datos:", error);
      throw error;
    }
  }

  private setupToolHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "execute_query",
            description: "Ejecuta una consulta SQL de solo lectura (SELECT) en la base de datos SQL Server",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "La consulta SQL SELECT a ejecutar",
                },
              },
              required: ["query"],
            },
          },
          {
            name: "list_tables",
            description: "Lista todas las tablas disponibles en la base de datos",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "describe_table",
            description: "Describe la estructura de una tabla específica",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "El nombre de la tabla a describir",
                },
              },
              required: ["table_name"],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        await this.connectToDatabase();

        switch (name) {
          case "execute_query":
            if (!args || typeof args !== 'object' || !('query' in args) || typeof args.query !== 'string') {
              throw new Error("Se requiere el parámetro 'query' de tipo string");
            }
            return await this.executeValidatedQuery(args.query);
          case "list_tables":
            return await this.listTables();
          case "describe_table":
            if (!args || typeof args !== 'object' || !('table_name' in args) || typeof args.table_name !== 'string') {
              throw new Error("Se requiere el parámetro 'table_name' de tipo string");
            }
            return await this.describeTable(args.table_name);
          default:
            throw new Error(`Tool desconocido: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  private async executeQuery(query: string) {
    if (!this.pool) {
      throw new Error("No hay conexión a la base de datos");
    }

    // Validación estricta de seguridad
    this.validateReadOnlyQuery(query);
  }

  private validateReadOnlyQuery(query: string) {
    const normalizedQuery = query.trim().toLowerCase();
    
    // 1. Debe empezar con SELECT
    if (!normalizedQuery.startsWith('select')) {
      throw new Error("Solo se permiten consultas SELECT para lectura");
    }

    // 2. Detectar múltiples statements (separados por ;)
    const statements = query.split(';').map(s => s.trim()).filter(s => s.length > 0);
    if (statements.length > 1) {
      throw new Error("No se permiten múltiples statements SQL en una sola consulta");
    }

    // 3. Lista de palabras clave prohibidas (operaciones de escritura)
    const forbiddenKeywords = [
      'insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate',
      'exec', 'execute', 'sp_', 'xp_', 'merge', 'bulk', 'openrowset',
      'opendatasource', 'openquery', 'openxml', 'writetext', 'updatetext',
      'backup', 'restore', 'dbcc', 'shutdown', 'reconfigure', 'grant',
      'revoke', 'deny', 'use ', 'go ', 'declare', 'set ', 'print'
    ];

    for (const keyword of forbiddenKeywords) {
      if (normalizedQuery.includes(keyword)) {
        throw new Error(`Operación prohibida detectada: '${keyword}'. Solo se permiten consultas SELECT de lectura.`);
      }
    }

    // 4. Detectar comentarios que podrían ocultar código malicioso
    if (normalizedQuery.includes('/*') || normalizedQuery.includes('--')) {
      throw new Error("No se permiten comentarios en las consultas por seguridad");
    }

    // 5. Validar que no contenga CTEs con operaciones peligrosas
    if (normalizedQuery.includes('with ') && !this.isValidCTE(normalizedQuery)) {
      throw new Error("CTE (Common Table Expression) contiene operaciones no permitidas");
    }

    // 6. Detectar funciones del sistema potencialmente peligrosas
    const dangerousFunctions = [
      'xp_cmdshell', 'sp_configure', 'openrowset', 'opendatasource',
      'fn_get_audit_file', 'bulk', 'sp_executesql'
    ];

    for (const func of dangerousFunctions) {
      if (normalizedQuery.includes(func)) {
        throw new Error(`Función del sistema prohibida: '${func}'`);
      }
    }
  }

  private isValidCTE(query: string): boolean {
    // Validar que el CTE solo contenga SELECT statements
    const ctePattern = /with\s+.*?\s+as\s*\((.*?)\)/gi;
    const matches = ctePattern.exec(query);
    
    if (matches) {
      const cteContent = matches[1].toLowerCase().trim();
      return cteContent.startsWith('select') && !cteContent.includes('insert') && 
             !cteContent.includes('update') && !cteContent.includes('delete');
    }
    
    return true;
  }

  private async executeValidatedQuery(query: string) {
    if (!this.pool) {
      throw new Error("No hay conexión a la base de datos");
    }

    try {
      const request = this.pool.request();
      const result = await request.query(query);
      
      return {
        content: [
          {
            type: "text",
            text: `Consulta ejecutada exitosamente. Filas encontradas: ${result.recordset.length}\n\nResultados:\n${JSON.stringify(result.recordset, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Error ejecutando la consulta: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async listTables() {
    if (!this.pool) {
      throw new Error("No hay conexión a la base de datos");
    }

    try {
      const request = this.pool.request();
      const result = await request.query(`
        SELECT 
          TABLE_SCHEMA,
          TABLE_NAME,
          TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
      `);

      return {
        content: [
          {
            type: "text",
            text: `Tablas disponibles:\n${JSON.stringify(result.recordset, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Error listando tablas: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async describeTable(tableName: string) {
    if (!this.pool) {
      throw new Error("No hay conexión a la base de datos");
    }

    try {
      const request = this.pool.request();
      request.input('tableName', sql.VarChar, tableName);
      
      const result = await request.query(`
        SELECT 
          COLUMN_NAME,
          DATA_TYPE,
          IS_NULLABLE,
          COLUMN_DEFAULT,
          CHARACTER_MAXIMUM_LENGTH,
          NUMERIC_PRECISION,
          NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = @tableName
        ORDER BY ORDINAL_POSITION
      `);

      return {
        content: [
          {
            type: "text",
            text: `Estructura de la tabla '${tableName}':\n${JSON.stringify(result.recordset, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Error describiendo tabla: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Servidor MCP SQL Server iniciado");
  }
}

const server = new SQLServerMCPServer();
server.run().catch(console.error);