from mongo_client import articles_collection, test_mongo_connection
from kg_builder.src.process_articles import print_article_stats
from datetime import datetime, timezone

test_mongo_connection()

# filters
categories = ["electrive", "pvmagazine"]
cutoff_date = datetime(2023, 1, 1)

articles_to_process = list(
    articles_collection.find(
        {"meta.date": {"$gt": cutoff_date},
         "meta.category": {"$in": categories}},  
        {"_id": 1, "meta": 1, "title": 1, "validation": 1, "llm_processed": 1,  "paragraphs": 1}       
    )
    .sort("_id", -1)            # sort by MongoDB ObjectId (descending)
)

print_article_stats(articles_to_process)