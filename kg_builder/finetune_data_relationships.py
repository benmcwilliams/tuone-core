import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import combine_paragraphs
from mongo_client import mongo_client, articles_collection
from kg_builder.format_prompts import read_prompt_from_file_only
from kg_builder.finetune.inputs import allowed_types_dict, groups_to_prompts

try:
    mongo_client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    raise

required_node_types = {
    "ownership": ["company", "joint_venture"],
    "technological": ["product", "capacity"],
    "financial_origin": ["investment"],
    "financial_technological": ["investment"],
}

def format_nodes_for_prompt(nodes, allowed_types=None):
    """
    Format nodes into a clear ID-to-description mapping for GPT prompts.
    Falls back to `amount` for Capacity nodes if `name` is missing.
    """
    lines = ["The following is a list of known entities. You MUST ALWAYS use the ID (left value) when referring to it in a relationship:"]
    print("Allowed types in format_nodes_for_prompt: ", allowed_types)
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

def reconstruct_original_relationship_format(relationships_mongo):
    """
    Converts MongoDB-style stored relationships back into original model output format.
    Strips article_id and ID metadata.
    """
    simplified = []
    for rel in relationships_mongo:
        simplified.append({
            "source": rel.get("source"),
            "type": rel.get("type"),
            "target": rel.get("target")
        })
    return json.dumps({"relationships": simplified}, ensure_ascii=False)

articles_to_process = list(
    articles_collection.find(
        {
            "validation": {
                "$exists": True,
                "$ne": False
            }
        },
        {"_id": 1, "title": 1, "paragraphs": 1, "nodes": 1, 
         "validation": 1, "relationships": 1}
    )
    .sort("_id", -1)  
)

for relationship_group in ["ownership", "technological", "financial_origin", "financial_technological"]:

    # set parameters
    allowed_types = allowed_types_dict[relationship_group]
    output_file = f"finetune/{relationship_group}.jsonl"

    PROMPT_PATH = groups_to_prompts[relationship_group]
    system_prompt = read_prompt_from_file_only(PROMPT_PATH)

    with open(output_file, "w", encoding="utf-8") as f_out:
        for article in articles_to_process:

            articleID = str(article["_id"])
            text = combine_paragraphs(article)
            nodes = article.get("nodes")

            # check whether article has any nodes
            if not nodes:
                print(f"⚠️ Article ID: {articleID} has no nodes — skipping")
                continue

            # ✅ Correct node presence check
            required_types = required_node_types[relationship_group]
            has_required_nodes = any(node.get("type") in required_types for node in nodes)
            if not has_required_nodes:
                print(f"⏭️ Skipping Article ID: {articleID} - no required node types {required_types} found for relationship group '{relationship_group}'.")
                continue

            compact_nodes = format_nodes_for_prompt(nodes, allowed_types)

            all_relationships = article.get("relationships")
            
            filter_relations = [entry for entry in all_relationships if entry.get('group') == relationship_group]
            print(f"{relationship_group} relations: ", filter_relations)

            user_content = f"""Here is the article text: {text}
            {compact_nodes}
            Please extract only the specified relationship types."""

            assistant_content = reconstruct_original_relationship_format(filter_relations)

            # Create fine-tuning format
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
