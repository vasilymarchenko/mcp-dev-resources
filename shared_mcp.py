from mcp.server.fastmcp import FastMCP
from mcp import (
    GetPromptResult,
    ListResourcesResult,
    ListPromptsResult,
)
from mcp.types import (
    TextContent, 
    PromptMessage, 
    Resource, 
    Prompt
)
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
    """Comprehensive unit testing guidelines """
    
    # Load all the related content directly
    main_content = _load_prompt_content("unit-testing-guidelines.md")
    autofixture_content = _load_reference_content("autofixture-attributes.cs")
    customization_content = _load_reference_content("customization-reference.cs")
    mocking_content = _load_reference_content("mocking-reference.cs")
    testing_examples_content = _load_example_content("testing-examples.cs")
    autsetup_examples_content = _load_example_content("autsetup-examples.cs")
    nullguards_examples_content = _load_example_content("nullguards-examples.cs")
    
    # Combine all content into a comprehensive prompt
    combined_content = f"""# Unit Testing Guidelines

{main_content}

## AutoFixture Attributes Reference

{autofixture_content}

## Customization Reference

{customization_content}

## Mocking Reference

{mocking_content}

## Testing Examples

{testing_examples_content}

## AutoSetup Examples

{autsetup_examples_content}

## NullGuards Examples

{nullguards_examples_content}
"""
    
    return GetPromptResult(
        description="Comprehensive unit testing guidelines including Autofixture, and testing best practices",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=combined_content
                )
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
    for file in _get_available_files(EXAMPLES_DIR, ".cs"):
        resources.append(Resource(
            uri=f"{EXAMPLE_SCHEME}{file}",
            name=f"example:{file}",
            description=f"Code example: {file.replace('-', ' ').title()}",
            mimeType="text/csharp"
        ))
    
    # Add template resources
    for file in _get_available_files(TEMPLATES_DIR, ".cs"):
        resources.append(Resource(
            uri=f"{TEMPLATE_SCHEME}{file}",
            name=f"template:{file}",
            description=f"Code template: {file.replace('-', ' ').title()}",
            mimeType="text/csharp"
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
        "available_templates": len(_get_available_files(TEMPLATES_DIR, ".py"))
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