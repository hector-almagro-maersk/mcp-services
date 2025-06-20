# Security Validation Tests

## ✅ ALLOWED Queries

```sql
-- Basic SELECT queries
SELECT * FROM users;
SELECT name, email FROM customers WHERE active = 1;
SELECT COUNT(*) FROM orders;

-- JOIN operations
SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id;

-- Aggregate functions
SELECT department, AVG(salary) FROM employees GROUP BY department;

-- Subqueries
SELECT * FROM products WHERE category_id IN (SELECT id FROM categories WHERE active = 1);

-- Valid CTEs (SELECT only)
WITH recent_orders AS (
  SELECT * FROM orders WHERE created_date > '2024-01-01'
)
SELECT * FROM recent_orders;
```

## ❌ BLOCKED Queries

### Write Operations
```sql
INSERT INTO users (name) VALUES ('test');           -- ❌ BLOCKED
UPDATE users SET name = 'new' WHERE id = 1;         -- ❌ BLOCKED  
DELETE FROM users WHERE id = 1;                     -- ❌ BLOCKED
DROP TABLE users;                                    -- ❌ BLOCKED
CREATE TABLE test (id int);                          -- ❌ BLOCKED
ALTER TABLE users ADD COLUMN test VARCHAR(50);      -- ❌ BLOCKED
TRUNCATE TABLE users;                                -- ❌ BLOCKED
```

### Multiple Statements
```sql
SELECT * FROM users; DROP TABLE users;              -- ❌ BLOCKED
SELECT * FROM users; INSERT INTO logs VALUES (1);   -- ❌ BLOCKED
```

### Dangerous System Functions
```sql
SELECT * FROM OPENROWSET(...);                      -- ❌ BLOCKED
EXEC xp_cmdshell 'dir';                             -- ❌ BLOCKED
EXEC sp_configure;                                   -- ❌ BLOCKED
```

### Comments (for security)
```sql
SELECT * FROM users; -- DROP TABLE users;           -- ❌ BLOCKED
SELECT * FROM users /* hidden code */;              -- ❌ BLOCKED
```

### Variables and Procedures
```sql
DECLARE @var INT; SELECT @var = 1;                   -- ❌ BLOCKED
SET @variable = 'value';                             -- ❌ BLOCKED
EXEC sp_executesql @sql;                            -- ❌ BLOCKED
```

### Malicious CTEs
```sql
WITH malicious AS (
  INSERT INTO logs VALUES (1)  -- ❌ BLOCKED
)
SELECT * FROM users;
```

## Implemented Validations

1. **Mandatory SELECT start**: Query must start with `SELECT`
2. **Single statement**: Multiple queries separated by `;` are not allowed
3. **Keyword blacklist**: Blocks INSERT, UPDATE, DELETE, DROP, etc.
4. **No comments**: Prevents hiding malicious code
5. **CTE validation**: Common Table Expressions must contain only SELECT
6. **System functions**: Blocks dangerous functions like `xp_cmdshell`
7. **No variables**: Prevents declaration and use of variables