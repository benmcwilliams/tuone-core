import sys; sys.path.append("../..")
from dotenv import load_dotenv
from openai import OpenAI
import json
from openai_client import openai_client
from utils import ping_openai

load_dotenv()

ping_openai() 
    
def check_moderation(text):
    try:
        response = openai_client.moderations.create(input=text)
        result = response.results[0]
        print(result.flagged)
        print(result.category_scores)
        return result.flagged, result.category_scores
    except Exception as e:
        return True, {"error": str(e)}

file_path = "nodes.jsonl"

with open(file_path, "r") as f:
    for i, line in enumerate(f):
        print(i)
        data = json.loads(line)
        for msg in data.get("messages", []):
            flagged, scores = check_moderation(msg["content"])
            high_scores = {
                k: round(v, 3) for k, v in dict(scores).items() if v is not None and v > 0.01
            }

            if flagged or high_scores:
                print(f"\n🔎 Example {i}, role={msg['role']}")
                print(f"Text: {msg['content'][:100]}...")
                print(f"Flagged: {flagged}")
                print(f"High-scoring categories: {high_scores}")