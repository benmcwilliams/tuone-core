import re
import yaml

def clean_markdown_yaml(file_path):
    """
    Cleans and normalizes the YAML frontmatter of a Markdown file, handling malformed fields
    and preserving the desired key order.

    Args:
        file_path (str): Path to the Markdown file to clean.
    """
    # Define the desired order of keys
    desired_order = [
        "country",
        "location",
        "company",
        "tech",
        "component",
        "phase",
        "investment_value",
        "capacity",
        "status",
        "dt_announce",
        "dt_actual",
        "dt_operational",
        "dt_cancel",
        "jobs",
        "checked",
        "reject-phase",
        "finetune",
        "share-investment",
    ]

    with open(file_path, 'r') as f:
        content = f.read()

    # Extract YAML frontmatter using regex
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        print(f"No YAML frontmatter found in {file_path}.")
        return

    yaml_content = yaml_match.group(1)

    # Normalize problematic values in the raw YAML string
    normalized_yaml_content = re.sub(r':\s*-$', ': null', yaml_content, flags=re.MULTILINE)
    normalized_yaml_content = re.sub(r':\s*NA$', ': null', normalized_yaml_content, flags=re.MULTILINE)

    # Parse YAML after normalization
    try:
        yaml_data = yaml.safe_load(normalized_yaml_content)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in {file_path}: {e}")
        return

    # Reorder keys based on the desired order
    ordered_yaml_data = {key: yaml_data.get(key) for key in desired_order if key in yaml_data}

    # Reconstruct cleaned YAML frontmatter
    cleaned_yaml = yaml.dump(ordered_yaml_data, default_flow_style=False).strip()

    # Replace old YAML frontmatter with the cleaned version
    cleaned_content = content.replace(yaml_match.group(0), f"---\n{cleaned_yaml}\n---")

    # Write cleaned content back to the file
    with open(file_path, 'w') as f:
        f.write(cleaned_content)

    print(f"Cleaned YAML frontmatter in {file_path}.")