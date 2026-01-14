import sys
import os
import json
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import combine_paragraphs
from mongo_client import mongo_client, articles_collection, test_mongo_connection
from kg_builder.src.format_prompts import read_prompt_from_file_only
from kg_builder.finetune.inputs import allowed_types_dict, groups_to_prompts

test_mongo_connection()

relationship_to_type = {
    "investments": "investment",
    "capacities": "capacity",
    "products": "product"
}

def format_nodes_for_prompt(nodes, allowed_types=None):
    """
    Format nodes into a clear ID-to-description mapping for GPT prompts.
    Falls back to `amount` for Capacity nodes if `name` is missing.
    """

    lines = ["The following is a list of known entities. You MUST ALWAYS use the ID (left value) when referring to it in a relationship:"]

    for node in nodes:
        node_id = node.get("id")
        node_type = node.get("type")

        name = node.get("name")
        if not name and node_type in {"capacity", "investment"}:
            name = node.get("amount")

        if node_id and node_type and name:
            if allowed_types is None or node_type in allowed_types:
                lines.append(f"- ID: {node_id}: Name: {name} ({node_type})")

    return "\n".join(lines)

def reconstruct_properties_format(nodes, relationship_group):
    """
    Converts validated nodes into the target assistant format for properties.
    """
    characteristics_output = []

    # Determine which key to use and what properties to extract
    if relationship_group == "capacities":
        id_key = "capacity_ID"
        node_types = {"capacity"}
        extract_fields = ["status", "phase", "is_total"]
    elif relationship_group == "investments":
        id_key = "investment_ID"
        node_types = {"investment"}
        extract_fields = ["status", "phase", "is_total"]
    elif relationship_group == "products":
        id_key = "product_ID"
        node_types = {"product"}
        extract_fields = ["product_lv1", "product_lv2"]
    else:
        raise ValueError(f"Unsupported relationship group: {relationship_group}")

    for node in nodes:
        node_type = node.get("type")
        node_id = node.get("id")
        
        # Only process nodes of the expected type
        if node_type not in node_types:
            continue
        
        # Build the output object with id_key and relevant fields
        output_item = {id_key: node_id}
        
        for field in extract_fields:
            output_item[field] = node.get(field)
        
        characteristics_output.append(output_item)

    return json.dumps({"node_characteristics": characteristics_output}, ensure_ascii=False)

articles_to_process = list(
    articles_collection.find(
        {
            "validation": {
                "$type": ["int", "long", "double"],
                # epoch seconds; adjust if you need older history
                "$gte": 946684800,   # 2000-01-01
                "$lte": 4102444800,  # 2100-01-01
            }
        },
        {"_id": 1, "title": 1, "paragraphs": 1, "nodes": 1, "validation": 1}
    )
    .sort("_id", -1)  
)

for relationship_group in ["investments", "capacities", "products"]:

    allowed_types = allowed_types_dict[relationship_group]
    print("-- Allowed node types: ", allowed_types)
    output_file = os.path.join(project_root, f"kg_builder/finetune/training_data/{relationship_group}.jsonl")

    PROMPT_PATH = os.path.join(project_root, groups_to_prompts[relationship_group])
    system_prompt = read_prompt_from_file_only(PROMPT_PATH) # the system prompt
    type_match = relationship_to_type[relationship_group]
    print(type_match)

    with open(output_file, "w", encoding="utf-8") as f_out:

        for article in articles_to_process:

            # read relevant article data
            articleID = str(article["_id"])
            text = combine_paragraphs(article)
            all_nodes = article.get("nodes", [])
            nodes = [node for node in all_nodes if node.get("type") == type_match] # only returning nodes which match the relationship group type

            # check whether article has first any nodes, and then nodes relevant to the prompt (capacity | investment)
            if not nodes:
                print(f"⚠️ Article ID: {articleID} has no nodes — skipping")
                continue

            has_relevant_nodes = any(node.get("type") == type_match for node in nodes) # a boolean, True | False
            if not has_relevant_nodes:
                print(f"⏭️ Skipping Article ID: {articleID} - no nodes of type '{type_match}' found.")
                continue

            # set compact nodes
            compact_nodes = format_nodes_for_prompt(nodes, allowed_types)

            assistant_content = reconstruct_properties_format(nodes, relationship_group) ## ERROR that this reads all nodes.

            user_content = f"""Here is the article text: {text}
            {compact_nodes}
            """

            # output as fine-tuning format
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_content
                },
                {
                    "role": "assistant",
                    "content": assistant_content
                }
            ]

            f_out.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
            print(f"✅ Wrote example for Article ID: {articleID}")

    print(f"\n🎉 Finished exporting fine-tuning examples to {output_file}")
