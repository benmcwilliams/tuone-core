import sys; sys.path.append("../..")
from datetime import datetime
from mongo_client import articles_collection

# builds a dictionary mapping article objectID to date

def get_article_id_to_date_map():
    articles_to_process = list(
        articles_collection.find(
            {},
            {
                "_id": 1,
                "meta.date": 1
            }
        )
        .sort("_id", -1)
    )

    id_to_date = {}

    for article in articles_to_process:
        if "meta" in article and "date" in article["meta"]:
            date_value = article["meta"]["date"]
            if isinstance(date_value, datetime):
                id_to_date[str(article["_id"])] = date_value.strftime("%Y-%m")
            else:
                print(f"⚠️ Skipping article {article['_id']} – meta.date is not a datetime (got {type(date_value).__name__})")

    return id_to_date