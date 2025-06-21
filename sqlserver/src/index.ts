#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import sql from 'mssql';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class SQLServerMCPServer {
  private server: Server;
  private pool: sql.ConnectionPool | null = null;
  private connectionString: string;
  private version: string;

  constructor() {
    // Read version from VERSION file
    try {
      this.version = readFileSync(join(__dirname, '..', 'VERSION'), 'utf-8').trim();
    } catch (error) {
      console.error("Warning: Could not read VERSION file, using default version");
      this.version = "1.0.0";
    }

    this.server = new Server(
      {
        name: "mcp-sqlserver-server",
        version: this.version,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Get connection string from parameter
    this.connectionString = process.argv[2];
    if (!this.connectionString) {
      console.error("Error: You must provide a connection string as parameter");
      console.error("Usage: node dist/index.js \"Server=localhost;Database=mydb;User Id=user;Password=pass;\"");
      process.exit(1);
    }

    this.setupToolHandlers();
  }

  private async connectToDatabase(): Promise<void> {
    if (this.pool && this.pool.connected) {
      return;
    }

    try {
      this.pool = new sql.ConnectionPool({
        ...sql.ConnectionPool.parseConnectionString(this.connectionString),
        requestTimeout: 600000,
      });
      await this.pool.connect();
      console.error("Connected to SQL Server");
    } catch (error) {
      console.error("Error connecting to database:", error);
      throw error;
    }
  }

  private setupToolHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "execute_query",
            description: "Executes a read-only SQL query (SELECT) on the SQL Server database",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "The SQL SELECT query to execute",
                },
              },
              required: ["query"],
            },
          },
          {
            name: "list_tables",
            description: "Lists all available tables in the database",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "describe_table",
            description: "Describes the structure of a specific table",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "The name of the table to describe",
                },
              },
              required: ["table_name"],
            },
          },
          {
            name: "get_version",
            description: "Gets the current version of the MCP SQL Server",
            inputSchema: {
              type: "object",
              properties: {},
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
              throw new Error("Parameter 'query' of type string is required");
            }
            return await this.executeValidatedQuery(args.query);
          case "list_tables":
            return await this.listTables();
          case "describe_table":
            if (!args || typeof args !== 'object' || !('table_name' in args) || typeof args.table_name !== 'string') {
              throw new Error("Parameter 'table_name' of type string is required");
            }
            return await this.describeTable(args.table_name);
          case "get_version":
            return await this.getVersion();
          default:
            throw new Error(`Unknown tool: ${name}`);
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
      throw new Error("No database connection available");
    }

    // Strict security validation
    this.validateReadOnlyQuery(query);
  }

  private validateReadOnlyQuery(query: string) {
    const normalizedQuery = query.trim().toLowerCase();
    
    // 1. Must start with SELECT
    if (!normalizedQuery.startsWith('select')) {
      throw new Error("Only SELECT queries are allowed for read operations");
    }

    // 2. Detect multiple statements (separated by ;)
    const statements = query.split(';').map(s => s.trim()).filter(s => s.length > 0);
    if (statements.length > 1) {
      throw new Error("Multiple SQL statements are not allowed in a single query");
    }

    // 3. List of forbidden keywords (write operations)
    const forbiddenKeywords = [
      'insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate',
      'exec', 'execute', 'sp_', 'xp_', 'merge', 'bulk', 'openrowset',
      'opendatasource', 'openquery', 'openxml', 'writetext', 'updatetext',
      'backup', 'restore', 'dbcc', 'shutdown', 'reconfigure', 'grant',
      'revoke', 'deny', 'use ', 'go ', 'declare', 'set ', 'print'
    ];

    for (const keyword of forbiddenKeywords) {
      if (normalizedQuery.includes(keyword)) {
        throw new Error(`Forbidden operation detected: '${keyword}'. Only SELECT read queries are allowed.`);
      }
    }

    // 4. Detect comments that could hide malicious code
    if (normalizedQuery.includes('/*') || normalizedQuery.includes('--')) {
      throw new Error("Comments are not allowed in queries for security reasons");
    }

    // 5. Validate that it doesn't contain CTEs with dangerous operations
    if (normalizedQuery.includes('with ') && !this.isValidCTE(normalizedQuery)) {
      throw new Error("CTE (Common Table Expression) contains forbidden operations");
    }

    // 6. Detect potentially dangerous system functions
    const dangerousFunctions = [
      'xp_cmdshell', 'sp_configure', 'openrowset', 'opendatasource',
      'fn_get_audit_file', 'bulk', 'sp_executesql'
    ];

    for (const func of dangerousFunctions) {
      if (normalizedQuery.includes(func)) {
        throw new Error(`Forbidden system function: '${func}'`);
      }
    }
  }

  private isValidCTE(query: string): boolean {
    // Validate that CTE only contains SELECT statements
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
      throw new Error("No database connection available");
    }

    try {
      const request = this.pool.request();
      const result = await request.query(query);
      
      return {
        content: [
          {
            type: "text",
            text: `Query executed successfully. Rows found: ${result.recordset.length}\n\nResults:\n${JSON.stringify(result.recordset, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Error executing query: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async listTables() {
    if (!this.pool) {
      throw new Error("No database connection available");
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
            text: `Available tables:\n${JSON.stringify(result.recordset, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Error listing tables: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async describeTable(tableName: string) {
    if (!this.pool) {
      throw new Error("No database connection available");
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
            text: `Table structure for '${tableName}':\n${JSON.stringify(result.recordset, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Error describing table: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async getVersion() {
    try {
      // Read changelog for current version info
      let changelogInfo = "";
      try {
        const changelogPath = join(__dirname, '..', 'CHANGELOG.md');
        const changelog = readFileSync(changelogPath, 'utf-8');
        
        // Extract current version section from changelog
        const versionPattern = new RegExp(`## \\[${this.version}\\].*?(?=## \\[|$)`, 's');
        const match = changelog.match(versionPattern);
        if (match) {
          changelogInfo = match[0].trim();
        }
      } catch (error) {
        changelogInfo = "Changelog information not available";
      }

      return {
        content: [
          {
            type: "text",
            text: `MCP SQL Server Version Information:

Version: ${this.version}
Server Name: mcp-sqlserver-server
Description: MCP Server for SQL Server read-only operations

${changelogInfo ? `\nChangelog for version ${this.version}:\n${changelogInfo}` : ''}`,
          },
        ],
      };
    } catch (error) {
      throw new Error(`Error getting version info: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("MCP SQL Server started");
  }
}

const server = new SQLServerMCPServer();
server.run().catch(console.error);