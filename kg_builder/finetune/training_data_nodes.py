import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import ping_openai, combine_paragraphs
from mongo_client import mongo_client, articles_collection, test_mongo_connection
from kg_builder.src.format_prompts import read_prompt_from_file_only
import json
from collections import defaultdict

test_mongo_connection()

output_file = os.path.join(project_root, "kg_builder/finetune/training_data/nodes.jsonl")
PROMPT_PATH = os.path.join(project_root, "kg_builder/src/prompts/entities-only.txt")
system_prompt = read_prompt_from_file_only(PROMPT_PATH)

def reconstruct_function_call_arguments(validated_nodes):
    grouped_nodes = defaultdict(list)

    for node in validated_nodes:
        node_type = node["type"]
        reconstructed_node = {
            "id": node.get("id"),
            "type": node_type,
            "name": node.get("name"),
        }

        # Include optional fields if present
        if node.get("location"):
            reconstructed_node["location"] = {
                "city": node["location"].get("city", ""),
                "country": node["location"].get("country", "")
            }

        if node.get("amount") is not None:
            reconstructed_node["amount"] = node["amount"]
        if node.get("status") is not None:
            reconstructed_node["status"] = node["status"]

        grouped_nodes[node_type].append(reconstructed_node)

    return json.dumps({"nodes": grouped_nodes}, ensure_ascii=False) 

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

with open(output_file, "w", encoding="utf-8") as f_out:
    for article in articles_to_process:
        articleID = str(article["_id"])

        text = combine_paragraphs(article)
        user_content = f"Here is the article: {text}"

        nodes = article.get("nodes")
        if not nodes:
            print(f"⚠️ Article ID: {articleID} has no nodes — skipping")
            continue

        assistant_content = reconstruct_function_call_arguments(nodes)

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
