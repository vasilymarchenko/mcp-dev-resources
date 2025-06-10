from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from file_helpers import load_file_content

EXAMPLES_DIR = Path(__file__).parent / "examples"
PROMPTS_DIR = Path(__file__).parent / "prompts"
REFERENCES_DIR = Path(__file__).parent / "references"
TEMPLATES_DIR = Path(__file__).parent / "templates"

# env - central context/config for Jinja2 templates
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),  # So {% include %} works
    autoescape=False
)

def build_guidelines_md(template_filename: str):
    tmpl_str = load_file_content(TEMPLATES_DIR / template_filename, "template")

    # Create a template object from the string
    tmpl = env.from_string(tmpl_str)

    rendered = tmpl.render(
        reference_content=lambda fname: load_file_content(REFERENCES_DIR / fname, "reference"),
        example_content=lambda fname: load_file_content(EXAMPLES_DIR / fname, "example")
    )
    return rendered

def save_guidelines_md(template_filename: str, output_filename: str):
    """
    Build the guidelines md from a template and save the result to a file.
    """
    try:
        rendered = build_guidelines_md(template_filename)
    except FileNotFoundError as e:
        print(f"Input file not found: {e}")
        return
    except Exception as e:
        print(f"Failed to build guidelines: {e}")
        return
    output_path = Path(output_filename)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Saved: {output_path.resolve()}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Render a Jinja2-based Markdown template with injected file content.")
    parser.add_argument("template", help="Template filename, e.g. dummy-template.md")
    parser.add_argument("output", help="Output filename for rendered Markdown, e.g. out.md")
    args = parser.parse_args()

    save_guidelines_md(args.template, args.output)

if __name__ == "__main__":
    main()