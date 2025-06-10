# Enhanced MCP Server for VS Code Copilot Development
This repository provides a FastMCP-based server that exposes development resources—including instructions, references, examples, and templates—to enhance productivity and code quality within VS Code Copilot. It offers dynamic resource discovery, categorized prompts, and comprehensive content loading for various development tasks.

## Activate venv

```bash
venv\Scripts\activate
```

## Run locally

### Option 1: run via STDIO

Run the MCP server together with MCP Inspector

```bash
mcp dev shared_mcp.py
```

### Option 2: run via HTTP (preferable)

1. Run MCP server: `python shared_mcp.py`. It will be available at: http://127.0.0.1:8000/mcp
2. Run MCP Inspector in another terminal: `npx -y @modelcontextprotocol/inspector`. It will be available at http://127.0.0.1:6274
3. Set up connection:
    - Select 'Streamable HTTP' transport
    - Enter URL: http://127.0.0.1:8000/mcp
    - Click 'Connect'

## Connect to VS Code

### Option 1

`Ctrl-Shift-P` -> `MCP: List servers` -> `Add server` -> `HTTP` -> http://127.0.0.1:8000/mcp/

### Option 2 - add config manually

Add config `.vscode\mcp.json`:
```json
{
    "servers": {
        "shared-instructions-mcp": {
            "url": "http://127.0.0.1:8000/mcp/"
        }
    }
}
```
