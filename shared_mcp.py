from mcp.server.fastmcp import FastMCP
from mcp import GetPromptResult
from mcp.types import (
    TextContent, 
    PromptMessage, 
)
from pathlib import Path
import logging
import json
from composer import build_guidelines_md
from file_helpers import (
    load_file_content,
    get_available_files,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server with better metadata
mcp = FastMCP(
    name="vscode-copilot-assistant",
    version="1.1.0",
    description="Enhanced MCP server providing development resources for VS Code Copilot"
)

# --------------------------------------------------------------------------
# Directory & URI scheme constants
# --------------------------------------------------------------------------
EXAMPLES_DIR = Path(__file__).parent / "examples"
PROMPTS_DIR = Path(__file__).parent / "prompts"
REFERENCES_DIR = Path(__file__).parent / "references"
TEMPLATES_DIR = Path(__file__).parent / "templates"

# URI schemes for different resource types
INSTRUCTION_SCHEME = "instruction://"
REFERENCE_SCHEME = "reference://"
EXAMPLE_SCHEME = "example://"
TEMPLATE_SCHEME = "template://"

# --------------------------------------------------------------------------

# Helper wrappers for resource loading

def _load_example_content(filename: str) -> str:
    return load_file_content(EXAMPLES_DIR / filename, "example")

def _load_reference_content(filename: str) -> str:
    return load_file_content(REFERENCES_DIR / filename, "reference")

# --------------------------------------------------------------------------
# PROMPTS: Prompt endpoints with categories
# --------------------------------------------------------------------------
@mcp.prompt()
def unit_testing_guidelines() -> GetPromptResult:
    """Comprehensive unit testing guidelines (pytest, unittest.mock, best practices)"""
    return GetPromptResult(
        description="Comprehensive unit testing guidelines including pytest, unittest.mock, and testing best practices",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=build_guidelines_md("unit-testing-template.md")
                ),
            )
        ],
    )

# --------------------------------------------------------------------------
# RESOURCES: Code references and examples   
# --------------------------------------------------------------------------

@mcp.resource(uri=f"{REFERENCE_SCHEME}autofixture-attributes")
def autofixture_attributes_reference() -> str:
    """AutoFixture attributes and customization options"""
    return _load_reference_content("autofixture-attributes.cs")

@mcp.resource(uri=f"{REFERENCE_SCHEME}customization-reference")
def customization_reference() -> str:
    """Customization options and best practices reference"""
    return _load_reference_content("customization-reference.cs")

@mcp.resource(uri=f"{REFERENCE_SCHEME}mocking-reference")
def mocking_reference() -> str:
    """Mocking frameworks and techniques reference"""
    return _load_reference_content("mocking-reference.cs")

@mcp.resource(uri=f"{EXAMPLE_SCHEME}testing-examples")
def testing_examples() -> str:
    """Testing examples for various scenarios"""
    return _load_example_content("testing-examples.cs")
    
@mcp.resource(uri=f"{EXAMPLE_SCHEME}autsetup-examples")
def autsetup_examples() -> str:
    """AutoSetup examples for various scenarios"""
    return _load_example_content("autsetup-examples.cs")

@mcp.resource(uri=f"{EXAMPLE_SCHEME}nullguards-examples")
def nullguards_examples() -> str:
    """NullGuard examples for various scenarios"""
    return _load_example_content("nullguards-examples.cs")

# --------------------------------------------------------------------------
# Health check and utility endpoints
# --------------------------------------------------------------------------
@mcp.resource(uri="health://status")
def health_check() -> str:
    """Health check resource for monitoring server status"""
    status = {
        "status": "healthy",
        "available_prompts": len(get_available_files(PROMPTS_DIR)),
        "available_examples": len(get_available_files(EXAMPLES_DIR)),
        "available_references": len(get_available_files(REFERENCES_DIR)),
        "available_templates": len(get_available_files(TEMPLATES_DIR))
    }
    
    return json.dumps(status, indent=2)

# --------------------------------------------------------------------------
# MAIN ENTRYPOINT with HTTP support
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # Start the MCP server over HTTP (default: 127.0.0.1:8000/mcp)
    print("Starting MCP server...")
    print("Server will be available at: http://127.0.0.1:8000/mcp")
    print("\nTo connect with MCP Inspector:")
    print("1. Run in another terminal: npx -y @modelcontextprotocol/inspector")
    print("2. Select 'Streamable HTTP' transport")
    print("3. Enter URL: http://127.0.0.1:8000/mcp")
    print("4. Click 'Connect'")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    mcp.run(transport="streamable-http")