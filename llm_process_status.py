from mongo_client import mongo_client, articles_collection
from kg_builder.src.process_articles import print_article_stats
from datetime import datetime, timezone

try:
    mongo_client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    raise

# filters
category = "electrive"
cutoff_date = datetime(2021, 1, 1)

articles_to_process = list(
    articles_collection.find(
        {"meta.date": {"$gt": cutoff_date},
         "meta.category": category},  
        {"_id": 1, "meta": 1, "title": 1, "validation": 1, "llm_processed": 1,  "paragraphs": 1}       
    )
    .sort("_id", -1)            # sort by MongoDB ObjectId (descending)
)

print_article_stats(articles_to_process)