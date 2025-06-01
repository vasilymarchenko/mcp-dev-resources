from mcp.server.fastmcp import FastMCP
from mcp import (
    GetPromptResult,
    ListResourcesResult,
    ListPromptsResult,
)
from mcp.types import TextContent, PromptMessage, Resource, Prompt
from pathlib import Path
import logging
from typing import List, Dict, Optional
import json

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

# Resource categories for better organization
RESOURCE_CATEGORIES = {
    "testing": ["unit-testing", "integration-testing", "e2e-testing"],
    "architecture": ["api-design", "database-design", "microservices"],
    "quality": ["code-review", "security-checklist", "performance"],
    "patterns": ["design-patterns", "error-handling", "logging"],
}

# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------
def _load_file_content(file_path: Path, resource_type: str = "file") -> str:
    """Load file content with enhanced error handling and validation."""
    if not file_path.exists():
        # Return placeholder content instead of raising error
        logger.warning(f"{resource_type.capitalize()} file not found: {file_path}")
        return f"# {resource_type.capitalize()} Content\n\nThis {resource_type} file is not yet available. Please create {file_path.name} in the {file_path.parent.name}/ directory."
    
    if not file_path.is_file():
        logger.warning(f"Path is not a file: {file_path}")
        return f"# Error\n\nPath is not a file: {file_path}"
    
    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            logger.warning(f"Empty {resource_type} file: {file_path.name}")
            return f"# Empty {resource_type.capitalize()}\n\nThis {resource_type} file exists but is empty. Please add content to {file_path.name}."
        return content
    except UnicodeDecodeError as e:
        logger.error(f"Unable to decode {resource_type} file {file_path.name}: {e}")
        return f"# Encoding Error\n\nUnable to decode {resource_type} file {file_path.name}: {e}"
    except Exception as e:
        logger.error(f"Error reading {resource_type} file {file_path.name}: {e}")
        return f"# Read Error\n\nError reading {resource_type} file {file_path.name}: {e}"

def _load_prompt_content(filename: str) -> str:
    """Load prompt content from prompts directory."""
    return _load_file_content(PROMPTS_DIR / filename, "prompt")

def _load_example_content(filename: str) -> str:
    """Load example content from examples directory."""
    return _load_file_content(EXAMPLES_DIR / filename, "example")

def _load_reference_content(filename: str) -> str:
    """Load reference content from references directory."""
    return _load_file_content(REFERENCES_DIR / filename, "reference")

def _load_template_content(filename: str) -> str:
    """Load template content from templates directory."""
    return _load_file_content(TEMPLATES_DIR / filename, "template")

def _get_available_files(directory: Path, extension: str = ".md") -> List[str]:
    """Get list of available files in a directory."""
    if not directory.exists():
        return []
    return [f.stem for f in directory.glob(f"*{extension}") if f.is_file()]

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
                    text=_load_prompt_content("unit-testing-guidelines.md")
                ),
            )
        ],
    )

@mcp.prompt()
def code_review_checklist() -> GetPromptResult:
    """Detailed code review checklist and quality standards"""
    return GetPromptResult(
        description="Comprehensive code review checklist covering style, security, performance, and maintainability",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=_load_prompt_content("code-review-checklist.md")
                ),
            )
        ],
    )

@mcp.prompt()
def api_design_principles() -> GetPromptResult:
    """REST API design principles and best practices"""
    return GetPromptResult(
        description="REST API design principles including RESTful conventions, error handling, and documentation standards",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=_load_prompt_content("api-design-principles.md")
                ),
            )
        ],
    )

@mcp.prompt()
def security_guidelines() -> GetPromptResult:
    """Security coding guidelines and vulnerability prevention"""
    return GetPromptResult(
        description="Security best practices, common vulnerability patterns, and secure coding guidelines",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=_load_prompt_content("security-guidelines.md")
                ),
            )
        ],
    )

@mcp.prompt()
def performance_optimization() -> GetPromptResult:
    """Performance optimization techniques and patterns"""
    return GetPromptResult(
        description="Performance optimization strategies, profiling techniques, and common bottleneck solutions",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=_load_prompt_content("performance-optimization.md")
                ),
            )
        ],
    )

# --------------------------------------------------------------------------
# RESOURCES: Instructions and code references
# --------------------------------------------------------------------------
@mcp.resource(uri=f"{INSTRUCTION_SCHEME}unit-testing")
def unit_testing_instruction() -> str:
    """Unit testing guidelines and best practices resource"""
    return _load_prompt_content("unit-testing-guidelines.md")

@mcp.resource(uri=f"{REFERENCE_SCHEME}error-handling")
def error_handling_reference() -> str:
    """Error handling patterns and implementation examples"""
    return _load_reference_content("error-handling-patterns.md")

@mcp.resource(uri=f"{EXAMPLE_SCHEME}pytest-fixtures")
def pytest_fixtures_example() -> str:
    """Pytest fixtures and test organization examples"""
    return _load_example_content("pytest-fixtures-examples.py")

@mcp.resource(uri=f"{TEMPLATE_SCHEME}fastapi-endpoint")
def fastapi_endpoint_template() -> str:
    """FastAPI endpoint template with validation and error handling"""
    return _load_template_content("fastapi-endpoint-template.py")

@mcp.resource(uri=f"{REFERENCE_SCHEME}logging-configuration")
def logging_configuration_reference() -> str:
    """Logging configuration patterns and best practices"""
    return _load_reference_content("logging-configuration.md")

@mcp.resource(uri=f"{EXAMPLE_SCHEME}database-patterns")
def database_patterns_example() -> str:
    """Database access patterns and ORM examples"""
    return _load_example_content("database-patterns.py")

# --------------------------------------------------------------------------
# Dynamic resource discovery
# --------------------------------------------------------------------------
def list_available_resources() -> ListResourcesResult:
    """Dynamically list all available resources"""
    resources = []
    
    # Add instruction resources
    for file in _get_available_files(PROMPTS_DIR):
        resources.append(Resource(
            uri=f"{INSTRUCTION_SCHEME}{file}",
            name=f"instruction:{file}",
            description=f"Development instruction: {file.replace('-', ' ').title()}",
            mimeType="text/markdown"
        ))
    
    # Add reference resources
    for file in _get_available_files(REFERENCES_DIR):
        resources.append(Resource(
            uri=f"{REFERENCE_SCHEME}{file}",
            name=f"reference:{file}",
            description=f"Code reference: {file.replace('-', ' ').title()}",
            mimeType="text/markdown"
        ))
    
    # Add example resources
    for file in _get_available_files(EXAMPLES_DIR, ".py"):
        resources.append(Resource(
            uri=f"{EXAMPLE_SCHEME}{file}",
            name=f"example:{file}",
            description=f"Code example: {file.replace('-', ' ').title()}",
            mimeType="text/python"
        ))
    
    # Add template resources
    for file in _get_available_files(TEMPLATES_DIR, ".py"):
        resources.append(Resource(
            uri=f"{TEMPLATE_SCHEME}{file}",
            name=f"template:{file}",
            description=f"Code template: {file.replace('-', ' ').title()}",
            mimeType="text/python"
        ))
    
    return ListResourcesResult(resources=resources)

def list_available_prompts() -> ListPromptsResult:
    """List all available prompts with enhanced descriptions"""
    prompts = []
    
    # Define prompts with categories
    prompt_definitions = {
        "unit_testing_guidelines": {
            "description": "Comprehensive unit testing guidelines (pytest, mocking, CI/CD)",
            "category": "testing"
        },
        "code_review_checklist": {
            "description": "Code review checklist (quality, security, performance)",
            "category": "quality"
        },
        "api_design_principles": {
            "description": "REST API design principles and best practices",
            "category": "architecture"
        },
        "security_guidelines": {
            "description": "Security coding guidelines and vulnerability prevention",
            "category": "quality"
        },
        "performance_optimization": {
            "description": "Performance optimization techniques and patterns",
            "category": "quality"
        }
    }
    
    for name, info in prompt_definitions.items():
        prompts.append(Prompt(
            name=name,
            description=f"[{info['category'].upper()}] {info['description']}"
        ))
    
    return ListPromptsResult(prompts=prompts)

# Register the list functions with the MCP server
mcp.list_resources_handler = list_available_resources
mcp.list_prompts_handler = list_available_prompts

# --------------------------------------------------------------------------
# Health check and utility endpoints
# --------------------------------------------------------------------------
@mcp.resource(uri="health://status")
def health_check() -> str:
    """Health check resource for monitoring server status"""
    status = {
        "status": "healthy",
        "available_prompts": len(_get_available_files(PROMPTS_DIR)),
        "available_examples": len(_get_available_files(EXAMPLES_DIR, ".py")),
        "available_references": len(_get_available_files(REFERENCES_DIR)),
        "available_templates": len(_get_available_files(TEMPLATES_DIR, ".py")),
        "categories": list(RESOURCE_CATEGORIES.keys())
    }
    
    return json.dumps(status, indent=2)

# --------------------------------------------------------------------------
# MAIN ENTRYPOINT
# --------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("Starting MCP server for VS Code Copilot assistance...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise