import sys; sys.path.append("..")
from mongo_client import articles_collection, test_mongo_connection
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Test MongoDB connection ---
test_mongo_connection()

# --- 2. Define queries ---
numeric_query = {"validation": {"$type": ["int", "long", "double"]}}   # validated with timestamp
true_query    = {"validation": True}                                   # explicitly True
false_query   = {"validation": False}                                  # explicitly False

# --- 3. Count each category ---
count_numeric = articles_collection.count_documents(numeric_query)
count_true    = articles_collection.count_documents(true_query)
count_false   = articles_collection.count_documents(false_query)

# --- 4. Display summary ---
print("🧾 Validation status summary:")
print(f"• With timestamp (numeric): {count_numeric}")
print(f"• Boolean True:             {count_true}")
print(f"• Boolean False:            {count_false}")
print(f"• Total with validation field: {count_numeric + count_true + count_false}")

# --- 5. If timestamped validations exist, plot them by month ---
if count_numeric > 0:
    # Fetch timestamps
    projection = {"validation": 1, "_id": 0}
    vals = [
        doc["validation"]
        for doc in articles_collection.find(numeric_query, projection)
        if isinstance(doc.get("validation"), (int, float))
    ]

    # Convert to Brussels time and aggregate by month
    dt_index = pd.to_datetime(vals, unit="s", utc=True).tz_convert("Europe/Brussels")
    monthly_counts = (
        pd.Series(1, index=dt_index)
        .sort_index()
        .resample("MS")  # Month Start
        .sum()
        .astype(int)
    )
    monthly_counts.index = monthly_counts.index.strftime("%Y-%m")

    # Plot monthly counts
    plt.figure(figsize=(10, 4))
    monthly_counts.plot(kind="bar")
    plt.title("Validated Articles per Month (Europe/Brussels)")
    plt.xlabel("Month")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()

    print("\n📊 Monthly validation counts:")
    print(monthly_counts.to_string())

    # --- 6. Category split for timestamp-validated articles ---
    pipeline = [
        { "$match": numeric_query },
        { "$project": { "cat": { "$ifNull": ["$meta.category", "Unknown"] } } },
        { "$group": { "_id": "$cat", "count": { "$sum": 1 } } },
        { "$sort": { "count": -1, "_id": 1 } },
    ]
    cat_rows = list(articles_collection.aggregate(pipeline))

    if cat_rows:
        # Build a Series indexed by category
        cat_series = pd.Series(
            { row["_id"]: row["count"] for row in cat_rows }
        )

        # Plot category split
        plt.figure(figsize=(10, 4))
        cat_series.plot(kind="bar")
        plt.title("Validated Articles by Category (meta.category)")
        plt.xlabel("Category")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.show()

        print("\n📚 Category split for timestamp-validated articles:")
        print(cat_series.to_string())
    else:
        print("\nNo categories found among timestamp-validated articles.")
else:
    print("\nNo timestamped validations found.")