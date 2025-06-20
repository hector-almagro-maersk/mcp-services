# 🛠️ Workflow Preferences

Este archivo define las preferencias de trabajo para el repositorio `mcp-services`.

## 🔧 **Herramientas Preferidas**
- ✅ **MCP GitHub Tools**: Usar exclusivamente herramientas MCP para operaciones de GitHub
- ✅ **No comandos git locales**: Evitar `git checkout`, `git pull`, etc. en terminal
- ✅ **Operaciones remotas**: Todas las operaciones deben hacerse a través de la API de GitHub

## 📋 **Flujo de Trabajo**
### 1. **Gestión de Issues**
- Siempre revisar issues abiertos al inicio
- Trabajar un issue a la vez
- Asignar issues antes de comenzar

### 2. **Gestión de Ramas**
- **Naming Convention**: 
  - `fix/descripcion-corta` para bug fixes
  - `feature/descripcion-corta` para nuevas funcionalidades
  - `docs/descripcion-corta` para cambios de documentación
- **Creación**: Siempre crear rama desde `main`
- **Nunca trabajar directamente en `main`**

### 3. **Pull Requests**
- **Título**: Usar emojis descriptivos (🔧, ✨, 📝, etc.)
- **Descripción obligatoria**:
  - 📝 Description
  - 🎯 Changes Made (con checkboxes ✅)
  - 📋 Acceptance Criteria Fulfilled (con checkboxes)
  - 🔗 Related Issue (con "Fixes #N")
  - 📊 Impact
- **Auto-cerrar issues**: Usar "Fixes #N" en el PR body

### 4. **Merge Strategy**
- **Método preferido**: `squash` merge
- **Commit message**: Descriptivo con emoji
- **Cleanup**: Eliminar rama después del merge

## 📝 **Estilo de Documentación**
- **Markdown**: Formato principal
- **Emojis**: Usar para categorizar y hacer más visual
- **Checkboxes**: Para listas de tareas y criterios
- **Estructura consistente**: Mantener formato similar en PRs e issues

## 🎯 **Criterios de Calidad**
- **Tests**: Verificar que no se rompan funcionalidades existentes
- **Documentación**: Actualizar README si es necesario
- **Enlaces**: Verificar que no queden enlaces rotos
- **Formato**: Mantener consistencia en markdown

## 📞 **Comunicación**
- **Issues**: Usar para trackear trabajo y bugs
- **PR Reviews**: Comentarios constructivos
- **Commit messages**: Claros y descriptivos
- **Referencias**: Siempre linkear issues relacionados

## 🚀 **Automatización**
- **Issue auto-close**: Los PRs deben cerrar issues automáticamente
- **Branch cleanup**: Eliminar ramas después del merge
- **Status checks**: Verificar que pasen antes del merge

---

📅 **Última actualización**: 20 de junio de 2025
👤 **Mantenido por**: hector-almagro-maersk