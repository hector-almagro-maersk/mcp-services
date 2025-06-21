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
  private connectionString: string = '';
  private version: string;
  private editMode: boolean = false;

  constructor() {
    // Read version from VERSION file
    try {
      this.version = readFileSync(join(__dirname, '..', 'VERSION'), 'utf-8').trim();
    } catch (error) {
      console.error("Warning: Could not read VERSION file, using default version");
      this.version = "1.0.0";
    }

    // Parse command line arguments
    this.parseArguments();

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

    this.setupToolHandlers();
  }

  private parseArguments(): void {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
      this.showUsage();
      process.exit(1);
    }

    // Check for edit mode flag
    const editModeIndex = args.findIndex(arg => arg === '--edit-mode' || arg === '-e');
    if (editModeIndex !== -1) {
      this.editMode = true;
      args.splice(editModeIndex, 1); // Remove the flag from args
      console.error("⚠️  EDIT MODE ENABLED - Write operations are allowed");
    }

    // First remaining argument should be the connection string
    this.connectionString = args[0];
    if (!this.connectionString) {
      console.error("Error: You must provide a connection string as parameter");
      this.showUsage();
      process.exit(1);
    }
  }

  private showUsage(): void {
    console.error("Usage: node dist/index.js [--edit-mode] \"connection_string\"");
    console.error("");
    console.error("Options:");
    console.error("  --edit-mode, -e    Enable write operations (INSERT, UPDATE, DELETE, DDL)");
    console.error("");
    console.error("Examples:");
    console.error("  # Read-only mode (default):");
    console.error("  node dist/index.js \"Server=localhost;Database=mydb;User Id=user;Password=pass;\"");
    console.error("");
    console.error("  # Edit mode enabled:");
    console.error("  node dist/index.js --edit-mode \"Server=localhost;Database=mydb;User Id=user;Password=pass;\"");
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
      const tools = [
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
      ];

      // Add write operation tools only if edit mode is enabled
      if (this.editMode) {
        tools.push(
          {
            name: "execute_write_query",
            description: "Executes a write SQL query (INSERT, UPDATE, DELETE, DDL) - Only available in edit mode",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "The SQL write query to execute",
                },
              },
              required: ["query"],
            },
          },
          {
            name: "create_table",
            description: "Creates a new table with specified columns - Only available in edit mode",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "The name of the table to create",
                },
                columns: {
                  type: "array",
                  description: "Array of column definitions",
                  items: {
                    type: "object",
                    properties: {
                      name: { type: "string", description: "Column name" },
                      type: { type: "string", description: "Column data type (e.g., VARCHAR(50), INT, DATETIME)" },
                      nullable: { type: "boolean", description: "Whether column can be NULL" },
                      primaryKey: { type: "boolean", description: "Whether column is primary key" }
                    },
                    required: ["name", "type"]
                  }
                },
              },
              required: ["table_name", "columns"],
            } as any,
          },
          {
            name: "drop_table",
            description: "Drops an existing table - Only available in edit mode",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "The name of the table to drop",
                },
              },
              required: ["table_name"],
            },
          },
          {
            name: "insert_data",
            description: "Inserts new records into a table - Only available in edit mode",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "The name of the table to insert data into",
                },
                data: {
                  type: "object",
                  description: "Key-value pairs representing column names and values",
                },
              },
              required: ["table_name", "data"],
            } as any,
          },
          {
            name: "update_data",
            description: "Updates existing records in a table - Only available in edit mode",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "The name of the table to update",
                },
                data: {
                  type: "object",
                  description: "Key-value pairs representing column names and new values",
                },
                where_clause: {
                  type: "string",
                  description: "WHERE clause to specify which records to update (without WHERE keyword)",
                },
              },
              required: ["table_name", "data", "where_clause"],
            } as any,
          },
          {
            name: "delete_data",
            description: "Deletes records from a table - Only available in edit mode",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "The name of the table to delete from",
                },
                where_clause: {
                  type: "string",
                  description: "WHERE clause to specify which records to delete (without WHERE keyword)",
                },
              },
              required: ["table_name", "where_clause"],
            } as any,
          }
        );
      }

      return { tools };
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
            return await this.executeQuery(args.query);
          case "execute_write_query":
            if (!this.editMode) {
              throw new Error("Write operations are not allowed. Start the server with --edit-mode flag to enable write operations.");
            }
            if (!args || typeof args !== 'object' || !('query' in args) || typeof args.query !== 'string') {
              throw new Error("Parameter 'query' of type string is required");
            }
            return await this.executeWriteQuery(args.query);
          case "create_table":
            if (!this.editMode) {
              throw new Error("Table creation is not allowed. Start the server with --edit-mode flag to enable write operations.");
            }
            if (!args || typeof args !== 'object' || !('table_name' in args) || typeof args.table_name !== 'string' || !('columns' in args) || !Array.isArray(args.columns)) {
              throw new Error("Parameters 'table_name' (string) and 'columns' (array) are required");
            }
            return await this.createTable(args.table_name, args.columns);
          case "drop_table":
            if (!this.editMode) {
              throw new Error("Table deletion is not allowed. Start the server with --edit-mode flag to enable write operations.");
            }
            if (!args || typeof args !== 'object' || !('table_name' in args) || typeof args.table_name !== 'string') {
              throw new Error("Parameter 'table_name' of type string is required");
            }
            return await this.dropTable(args.table_name);
          case "insert_data":
            if (!this.editMode) {
              throw new Error("Data insertion is not allowed. Start the server with --edit-mode flag to enable write operations.");
            }
            if (!args || typeof args !== 'object' || !('table_name' in args) || typeof args.table_name !== 'string' || !('data' in args) || typeof args.data !== 'object') {
              throw new Error("Parameters 'table_name' (string) and 'data' (object) are required");
            }
            return await this.insertData(args.table_name, args.data);
          case "update_data":
            if (!this.editMode) {
              throw new Error("Data updates are not allowed. Start the server with --edit-mode flag to enable write operations.");
            }
            if (!args || typeof args !== 'object' || !('table_name' in args) || typeof args.table_name !== 'string' || !('data' in args) || typeof args.data !== 'object' || !('where_clause' in args) || typeof args.where_clause !== 'string') {
              throw new Error("Parameters 'table_name' (string), 'data' (object), and 'where_clause' (string) are required");
            }
            return await this.updateData(args.table_name, args.data, args.where_clause);
          case "delete_data":
            if (!this.editMode) {
              throw new Error("Data deletion is not allowed. Start the server with --edit-mode flag to enable write operations.");
            }
            if (!args || typeof args !== 'object' || !('table_name' in args) || typeof args.table_name !== 'string' || !('where_clause' in args) || typeof args.where_clause !== 'string') {
              throw new Error("Parameters 'table_name' (string) and 'where_clause' (string) are required");
            }
            return await this.deleteData(args.table_name, args.where_clause);
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

  private async executeWriteQuery(query: string) {
    if (!this.pool) {
      throw new Error("No database connection available");
    }

    // Validate write query
    this.validateWriteQuery(query);
    
    const transaction = this.pool.transaction();
    
    try {
      await transaction.begin();
      const request = transaction.request();
      const result = await request.query(query);
      await transaction.commit();
      
      return {
        content: [
          {
            type: "text",
            text: `Write query executed successfully. Rows affected: ${result.rowsAffected[0] || 0}\n\nQuery: ${query}`,
          },
        ],
      };
    } catch (error) {
      await transaction.rollback();
      throw new Error(`Error executing write query: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private validateWriteQuery(query: string) {
    const normalizedQuery = query.trim().toLowerCase();
    
    // Allow write operations
    const allowedOperations = ['insert', 'update', 'delete', 'create', 'alter', 'drop', 'truncate'];
    const hasAllowedOperation = allowedOperations.some(op => normalizedQuery.startsWith(op));
    
    if (!hasAllowedOperation) {
      throw new Error("Query must be a valid write operation (INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, TRUNCATE)");
    }

    // Detect multiple statements (separated by ;)
    const statements = query.split(';').map(s => s.trim()).filter(s => s.length > 0);
    if (statements.length > 1) {
      throw new Error("Multiple SQL statements are not allowed in a single query");
    }

    // Still block dangerous system functions
    const dangerousFunctions = [
      'xp_cmdshell', 'sp_configure', 'openrowset', 'opendatasource',
      'fn_get_audit_file', 'bulk', 'sp_executesql'
    ];

    for (const func of dangerousFunctions) {
      if (normalizedQuery.includes(func)) {
        throw new Error(`Forbidden system function: '${func}'`);
      }
    }

    // Block comments for security
    if (normalizedQuery.includes('/*') || normalizedQuery.includes('--')) {
      throw new Error("Comments are not allowed in queries for security reasons");
    }
  }

  private async createTable(tableName: string, columns: any[]) {
    if (!this.pool) {
      throw new Error("No database connection available");
    }

    // Validate table name (allow schema.table format)
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$/.test(tableName)) {
      throw new Error("Invalid table name. Use format 'table' or 'schema.table' with letters, numbers, and underscores.");
    }

    // Build CREATE TABLE statement
    const columnDefinitions = columns.map(col => {
      if (!col.name || !col.type) {
        throw new Error("Each column must have 'name' and 'type' properties");
      }
      
      let definition = `[${col.name}] ${col.type}`;
      if (col.nullable === false) {
        definition += ' NOT NULL';
      }
      if (col.primaryKey === true) {
        definition += ' PRIMARY KEY';
      }
      return definition;
    });

    // Handle schema.table format
    const formattedTableName = tableName.includes('.') 
      ? tableName.split('.').map(part => `[${part}]`).join('.')
      : `[${tableName}]`;

    const createTableQuery = `CREATE TABLE ${formattedTableName} (${columnDefinitions.join(', ')})`;
    
    const transaction = this.pool.transaction();
    
    try {
      await transaction.begin();
      const request = transaction.request();
      await request.query(createTableQuery);
      await transaction.commit();
      
      return {
        content: [
          {
            type: "text",
            text: `Table '${tableName}' created successfully with ${columns.length} columns.\n\nSQL: ${createTableQuery}`,
          },
        ],
      };
    } catch (error) {
      await transaction.rollback();
      throw new Error(`Error creating table: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async dropTable(tableName: string) {
    if (!this.pool) {
      throw new Error("No database connection available");
    }

    // Validate table name (allow schema.table format)
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$/.test(tableName)) {
      throw new Error("Invalid table name. Use format 'table' or 'schema.table' with letters, numbers, and underscores.");
    }

    // Handle schema.table format
    const formattedTableName = tableName.includes('.') 
      ? tableName.split('.').map(part => `[${part}]`).join('.')
      : `[${tableName}]`;

    const dropTableQuery = `DROP TABLE ${formattedTableName}`;
    
    const transaction = this.pool.transaction();
    
    try {
      await transaction.begin();
      const request = transaction.request();
      await request.query(dropTableQuery);
      await transaction.commit();
      
      return {
        content: [
          {
            type: "text",
            text: `Table '${tableName}' dropped successfully.\n\nSQL: ${dropTableQuery}`,
          },
        ],
      };
    } catch (error) {
      await transaction.rollback();
      throw new Error(`Error dropping table: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async insertData(tableName: string, data: any) {
    if (!this.pool) {
      throw new Error("No database connection available");
    }

    // Validate table name (allow schema.table format)
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$/.test(tableName)) {
      throw new Error("Invalid table name. Use format 'table' or 'schema.table' with letters, numbers, and underscores.");
    }

    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
      throw new Error("Data object must contain at least one key-value pair");
    }

    const columns = Object.keys(data);
    const values = Object.values(data);
    
    // Build parameterized INSERT statement with proper schema handling
    const columnNames = columns.map(col => `[${col}]`).join(', ');
    const parameterNames = columns.map((_, i) => `@param${i}`).join(', ');
    
    // Handle schema.table format
    const formattedTableName = tableName.includes('.') 
      ? tableName.split('.').map(part => `[${part}]`).join('.')
      : `[${tableName}]`;
    
    const insertQuery = `INSERT INTO ${formattedTableName} (${columnNames}) VALUES (${parameterNames})`;
    
    const transaction = this.pool.transaction();
    
    try {
      await transaction.begin();
      const request = transaction.request();
      
      // Add parameters
      values.forEach((value, i) => {
        request.input(`param${i}`, value);
      });
      
      const result = await request.query(insertQuery);
      await transaction.commit();
      
      return {
        content: [
          {
            type: "text",
            text: `Data inserted successfully into '${tableName}'. Rows affected: ${result.rowsAffected[0] || 0}\n\nData: ${JSON.stringify(data, null, 2)}`,
          },
        ],
      };
    } catch (error) {
      await transaction.rollback();
      throw new Error(`Error inserting data: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async updateData(tableName: string, data: any, whereClause: string) {
    if (!this.pool) {
      throw new Error("No database connection available");
    }

    // Validate table name (allow schema.table format)
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$/.test(tableName)) {
      throw new Error("Invalid table name. Use format 'table' or 'schema.table' with letters, numbers, and underscores.");
    }

    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
      throw new Error("Data object must contain at least one key-value pair");
    }

    if (!whereClause.trim()) {
      throw new Error("WHERE clause is required for UPDATE operations");
    }

    const columns = Object.keys(data);
    const values = Object.values(data);
    
    // Build parameterized UPDATE statement with proper schema handling
    const setClause = columns.map((col, i) => `[${col}] = @param${i}`).join(', ');
    
    // Handle schema.table format
    const formattedTableName = tableName.includes('.') 
      ? tableName.split('.').map(part => `[${part}]`).join('.')
      : `[${tableName}]`;
    
    const updateQuery = `UPDATE ${formattedTableName} SET ${setClause} WHERE ${whereClause}`;
    
    const transaction = this.pool.transaction();
    
    try {
      await transaction.begin();
      const request = transaction.request();
      
      // Add parameters
      values.forEach((value, i) => {
        request.input(`param${i}`, value);
      });
      
      const result = await request.query(updateQuery);
      await transaction.commit();
      
      return {
        content: [
          {
            type: "text",
            text: `Data updated successfully in '${tableName}'. Rows affected: ${result.rowsAffected[0] || 0}\n\nData: ${JSON.stringify(data, null, 2)}\nWHERE: ${whereClause}`,
          },
        ],
      };
    } catch (error) {
      await transaction.rollback();
      throw new Error(`Error updating data: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async deleteData(tableName: string, whereClause: string) {
    if (!this.pool) {
      throw new Error("No database connection available");
    }

    // Validate table name (allow schema.table format)
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$/.test(tableName)) {
      throw new Error("Invalid table name. Use format 'table' or 'schema.table' with letters, numbers, and underscores.");
    }

    if (!whereClause.trim()) {
      throw new Error("WHERE clause is required for DELETE operations");
    }

    // Handle schema.table format
    const formattedTableName = tableName.includes('.') 
      ? tableName.split('.').map(part => `[${part}]`).join('.')
      : `[${tableName}]`;

    const deleteQuery = `DELETE FROM ${formattedTableName} WHERE ${whereClause}`;
    
    const transaction = this.pool.transaction();
    
    try {
      await transaction.begin();
      const request = transaction.request();
      const result = await request.query(deleteQuery);
      await transaction.commit();
      
      return {
        content: [
          {
            type: "text",
            text: `Data deleted successfully from '${tableName}'. Rows affected: ${result.rowsAffected[0] || 0}\n\nWHERE: ${whereClause}`,
          },
        ],
      };
    } catch (error) {
      await transaction.rollback();
      throw new Error(`Error deleting data: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error(`MCP SQL Server started - Mode: ${this.editMode ? 'EDIT (Write operations enabled)' : 'READ-ONLY'}`);
  }
}

const server = new SQLServerMCPServer();
server.run().catch(console.error);