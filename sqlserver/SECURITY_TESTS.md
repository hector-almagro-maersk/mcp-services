# Pruebas de Validación de Seguridad

## ✅ Consultas PERMITIDAS

```sql
-- Consultas SELECT básicas
SELECT * FROM users;
SELECT name, email FROM customers WHERE active = 1;
SELECT COUNT(*) FROM orders;

-- JOIN operations
SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id;

-- Funciones agregadas
SELECT department, AVG(salary) FROM employees GROUP BY department;

-- Subconsultas
SELECT * FROM products WHERE category_id IN (SELECT id FROM categories WHERE active = 1);

-- CTEs válidos (solo SELECT)
WITH recent_orders AS (
  SELECT * FROM orders WHERE created_date > '2024-01-01'
)
SELECT * FROM recent_orders;
```

## ❌ Consultas BLOQUEADAS

### Operaciones de Escritura
```sql
INSERT INTO users (name) VALUES ('test');           -- ❌ BLOQUEADA
UPDATE users SET name = 'new' WHERE id = 1;         -- ❌ BLOQUEADA  
DELETE FROM users WHERE id = 1;                     -- ❌ BLOQUEADA
DROP TABLE users;                                    -- ❌ BLOQUEADA
CREATE TABLE test (id int);                          -- ❌ BLOQUEADA
ALTER TABLE users ADD COLUMN test VARCHAR(50);      -- ❌ BLOQUEADA
TRUNCATE TABLE users;                                -- ❌ BLOQUEADA
```

### Múltiples Statements
```sql
SELECT * FROM users; DROP TABLE users;              -- ❌ BLOQUEADA
SELECT * FROM users; INSERT INTO logs VALUES (1);   -- ❌ BLOQUEADA
```

### Funciones del Sistema Peligrosas
```sql
SELECT * FROM OPENROWSET(...);                      -- ❌ BLOQUEADA
EXEC xp_cmdshell 'dir';                             -- ❌ BLOQUEADA
EXEC sp_configure;                                   -- ❌ BLOQUEADA
```

### Comentarios (por seguridad)
```sql
SELECT * FROM users; -- DROP TABLE users;           -- ❌ BLOQUEADA
SELECT * FROM users /* hidden code */;              -- ❌ BLOQUEADA
```

### Variables y Procedimientos
```sql
DECLARE @var INT; SELECT @var = 1;                   -- ❌ BLOQUEADA
SET @variable = 'value';                             -- ❌ BLOQUEADA
EXEC sp_executesql @sql;                            -- ❌ BLOQUEADA
```

### CTEs Maliciosos
```sql
WITH malicious AS (
  INSERT INTO logs VALUES (1)  -- ❌ BLOQUEADA
)
SELECT * FROM users;
```

## Validaciones Implementadas

1. **Inicio obligatorio con SELECT**: La consulta debe empezar con `SELECT`
2. **Un solo statement**: No se permiten múltiples consultas separadas por `;`
3. **Lista negra de palabras clave**: Bloquea INSERT, UPDATE, DELETE, DROP, etc.
4. **Sin comentarios**: Previene ocultación de código malicioso
5. **Validación de CTEs**: Los Common Table Expressions deben contener solo SELECT
6. **Funciones del sistema**: Bloquea funciones peligrosas como `xp_cmdshell`
7. **Sin variables**: Previene declaración y uso de variables