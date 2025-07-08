# GitHub Actions Workflows

This directory contains automated workflow for building and managing MCP (Model Context Protocol) services.

## Available Workflow

### 🎯 Build MCP Server (`build-mcp.yml`)

**Purpose:** Build a specific MCP service with manual selection.

**Trigger:** Manual dispatch (workflow_dispatch)

**Features:**
- 📋 **Dropdown selection** of available MCP services
- 🔄 **Version detection** from VERSION file or package.json
- 🏗️ **Automated build process** with support for Python and TypeScript projects
- 🧪 **Optional testing** if test scripts are available
- 📦 **Artifact generation** with naming format: `{service}-v{version}`
- ♻️ **Artifact overwriting** for same versions
- 📊 **Detailed build summary** in GitHub Actions UI

**Usage:**
1. Go to the **Actions** tab in GitHub
2. Select "Build MCP Server"
3. Click "Run workflow"
4. Choose the MCP service from the dropdown
5. Click "Run workflow" to start the build

**Artifact Contents:**

For **Python MCP services:**
- `server.py` - Python MCP server implementation
- `requirements.txt` - Python dependencies
- `test_server.py` - Unit tests (if available)
- `README.md` - Documentation
- `VERSION` - Version information
- `CHANGELOG.md` - Version history

For **TypeScript MCP services:**
- `dist/` - Compiled JavaScript code
- `package.json` - Package configuration
- `README.md` - Documentation (if available)
- `CHANGELOG.md` - Version history (if available)
- `VERSION` - Version file (if available)
- `BUILD_INFO.txt` - Build metadata
- Configuration and script files

## Artifact Management

### Naming Convention
Artifacts are named using the pattern: `{service-name}-v{version}`

Examples:
- `sqlserver-v1.0.0`
- `filesystem-v2.1.3`
- `database-v1.5.0`

### Version Handling
- **Same version:** Artifacts are overwritten (using `overwrite: true`)
- **New version:** Creates a new artifact with the new version number
- **Retention:** Artifacts are kept for 90 days

### Download Process
1. Go to the **Actions** tab in your repository
2. Click on the completed workflow run
3. Scroll down to the **Artifacts** section
4. Download the desired MCP service artifact
5. Extract the ZIP file to use the compiled MCP server

## Adding New MCP Services

To add a new MCP service to the automated build process:

### For Python MCP Services

1. **Create the service directory** with the required structure:
   ```
   your-mcp-service/
   ├── server.py          # Required - Main MCP server
   ├── requirements.txt   # Required - Python dependencies
   ├── VERSION           # Required - Version information
   ├── README.md         # Optional but recommended
   ├── CHANGELOG.md      # Optional
   └── test_server.py    # Optional - Unit tests
   ```

2. **Update the dropdown** in `build-mcp.yml`:
   ```yaml
   options:
     - sqlserver
     - your-mcp-service  # Add your service here
   ```

### For TypeScript MCP Services

1. **Create the service directory** with the required structure:
   ```
   your-mcp-service/
   ├── package.json      # Required
   ├── tsconfig.json     # Required
   ├── src/
   │   └── index.ts
   ├── VERSION           # Optional but recommended
   ├── README.md         # Optional
   └── CHANGELOG.md      # Optional
   ```

2. **Update the dropdown** in `build-mcp.yml`:
   ```yaml
   options:
     - sqlserver
     - your-mcp-service  # Add your service here
   ```

3. **Ensure build script** exists in package.json:
   ```json
   {
     "scripts": {
       "build": "tsc"
     }
   }
   ```

## Troubleshooting

### Build Failures
1. Check the **Actions** tab for detailed error logs
2. **For Python projects**: Verify that `requirements.txt` and `server.py` exist
3. **For TypeScript projects**: Verify that `package.json` and `tsconfig.json` exist
4. Ensure all dependencies are properly declared
5. **For TypeScript projects**: Check that the `build` script is defined in package.json

### Missing Artifacts
1. Verify the build completed successfully
2. **For TypeScript projects**: Check that the `dist/` directory was created during build
3. **For Python projects**: Ensure `server.py` and `requirements.txt` exist
4. Ensure retention period hasn't expired (90 days)

### Version Detection Issues
The workflow uses this priority order for version detection:
1. `VERSION` file content
2. `package.json` version field
3. Default: "1.0.0"

Make sure at least one of these sources contains a valid version.

## Security Notes

- Workflows run in a sandboxed environment
- No sensitive data is stored in artifacts
- All builds use clean Ubuntu containers
- Dependencies are cached for faster builds

## Support

For issues with the workflow:
1. Check the Actions logs for detailed error messages
2. Verify your MCP service follows the expected structure
3. Test builds locally before pushing changes
4. Create an issue if problems persist
