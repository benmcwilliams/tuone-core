from pymongo import MongoClient

def get_all_factory_products():
    # Connect to MongoDB (modify connection string as needed)
    client = MongoClient("mongodb://localhost:27017/")
    db = client.clean_tech_db
    collection = db.article_entities
    
    # Extract products from all factory nodes
    products = set()
    for article in collection.find():
        if "nodes" in article:
            for node in article["nodes"]:
                if node["type"] == "factory" and "products" in node:
                    products.update(node["products"])
    
    client.close()
    return list(products)

# Example usage
products = get_all_factory_products()
print("Products mentioned in all factory nodes:", products)