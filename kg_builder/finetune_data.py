import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import ping_openai, combine_paragraphs
from mongo_client import mongo_client, articles_collection
from kg_builder.format_prompts import read_prompt_from_file_only
import json
from collections import defaultdict

try:
    mongo_client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    raise

output_file = "finetune/nodes.jsonl"
PROMPT_PATH = "prompts/entities-only.txt"

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

system_prompt = read_prompt_from_file_only(PROMPT_PATH)

articles_to_process = list(
    articles_collection.find(
        {
            "validation": {
                "$exists": True,
                "$ne": False
            }
        },
        {"_id": 1, "paragraphs": 1, "nodes": 1, "validation": 1}
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
