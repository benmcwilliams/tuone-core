import sys
sys.path.append("../..")
from openai_client import openai_client
from utils import ping_openai
from datetime import datetime

# establish openai client 
ping_openai() 

response = openai_client.fine_tuning.jobs.list()

for job in response.data:
    model_name = job.fine_tuned_model
    created_at = job.created_at
    finished_at = job.finished_at
    status = job.status
    base_model = job.model
    # Convert timestamps to readable format if present
    created_str = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S') if created_at else "N/A"
    finished_str = datetime.fromtimestamp(finished_at).strftime('%Y-%m-%d %H:%M:%S') if finished_at else "N/A"
    print(f"Model: {model_name}\n  Base: {base_model}\n  Status: {status}\n  Created: {created_str}\n  Finished: {finished_str}\n")