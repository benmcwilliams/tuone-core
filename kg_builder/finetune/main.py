import os
import time
from openai import OpenAI
from dotenv import load_dotenv

type = "products"

# Load environment variables
load_dotenv()

def create_fine_tuning_job():
    # Initialize the OpenAI client
    client = OpenAI()
    
    # Upload the training file
    with open(f"training_data/{type}.jsonl", "rb") as f:
        response = client.files.create(
            file=f,
            purpose="fine-tune"
        )
        file_id = response.id
        print(f"Uploaded file with ID: {file_id}")
    
    # Create a fine-tuning job
    job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model="gpt-4o-mini-2024-07-18",
        suffix=type
    )
    
    print(f"Created fine-tuning job: {job.id}")
    print("\nMonitoring job status...")
    
    # Monitor the job status
    while True:
        job_status = client.fine_tuning.jobs.retrieve(job.id)
        print(f"Status: {job_status.status}")
        
        if job_status.status in ["succeeded", "failed"]:
            if job_status.status == "succeeded":
                print("\nFine-tuning completed successfully!")
                print(f"Fine-tuned model ID: {job_status.fine_tuned_model}")
            else:
                print("\nFine-tuning failed!")
                print(f"Error: {job_status.error}")
            break
            
        time.sleep(30)  # Check status every 30 seconds
    
    return job.id

if __name__ == "__main__":
    create_fine_tuning_job() 