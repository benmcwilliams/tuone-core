import json
from bson import json_util
import re
from inputs import relationship_groups
import os
import logging
from functools import lru_cache 
from openai_client import openai_client

@lru_cache(maxsize=None)  # we cache each prompt so no need to re-run every time
def read_prompt_from_file_only(file_path):
    with open(file_path, 'r') as file:
        prompt = file.read()
    return prompt

@lru_cache(maxsize=None) # cache schema
def load_function_schema(path):
    with open(path, "r") as f:
        return json.load(f)

def normalize_id(id_str):
    # we need this helper as model is indifferent returning capacity-1 or capacity_1
    return id_str.replace("-", "_") if id_str else id_str

def normalize_type(type_str):
    """
    Normalize a node or entity type to lower_snake_case.
    Examples:
    - "Company" -> "company"
    - "Joint Venture" -> "joint_venture"
    - "  Joint venture  " -> "joint_venture"
    """
    if not type_str:
        return None
    return re.sub(r"\s+", "_", type_str.strip().lower())

def format_nodes_for_prompt(nodes, allowed_types=None):
    """
    Format nodes into a clear ID-to-description mapping for GPT prompts.
    Falls back to `amount` for Capacity nodes if `name` is missing.
    """
    lines = ["The following is a list of known entities. You MUST ALWAYS use the ID when referring to it in a relationship:"]

    for node in nodes:
        if not isinstance(node, dict):
            print(f"⚠️ Skipping non-dict node: {node}")
            continue

        node_id = node.get("id")
        node_type = node.get("type")

        if node_id and node_type:
            if allowed_types is None or node_type in allowed_types:
                lines.append(f"- ID: {node_id}")

    return "\n".join(lines)

def get_schema(group, schema_path="schemas/relationships.json"):
    with open(schema_path, "r") as f:
        schema = json.load(f)

    schema["parameters"]["properties"]["relationships"]["items"]["properties"]["type"]["enum"] = relationship_groups[group]
    return schema

### Logging utils

def setup_logger(article_id, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(f"article_{article_id}")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_path = os.path.join(log_dir, f"{article_id}.log")
        handler = logging.FileHandler(file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

### OpenAI Utils

def call_openai_function(
    prompt: str,
    user_content: str,
    function_schema: dict,
    function_name: str,
    expected_top_key: str,
    model_name: str,
    logger,
):
    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content}
            ],
            functions=[function_schema],
            function_call={"name": function_name},
            temperature=0
        )

        function_args = response.choices[0].message.function_call.arguments
        parsed = json.loads(function_args)

        logger.info("✅ OpenAI returned output:")
        logger.info(json.dumps(parsed, indent=2))

        if expected_top_key not in parsed:
            raise ValueError(f"❌ Expected key '{expected_top_key}' not found in OpenAI output.")

        return parsed[expected_top_key]

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return []
    except Exception as e:
        print(f"❌ OpenAI call failed: {e}")
        return []