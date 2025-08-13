from mongo_client import articles_collection, test_mongo_connection

test_mongo_connection()

pipeline = [
    {"$match": {"llm_processed.ts": {"$type": "string"}}},

    {
        "$addFields": {
            "_ts_raw": "$llm_processed.ts",
            "_pos_plus": {"$indexOfBytes": ["$llm_processed.ts", "+", 19]},
            "_pos_minus": {"$indexOfBytes": ["$llm_processed.ts", "-", 19]},
            "_pos_z": {"$indexOfBytes": ["$llm_processed.ts", "Z", 19]},
        }
    },
    {
        "$addFields": {
            "_tz_pos": {
                "$switch": {
                    "branches": [
                        {"case": {"$gte": ["$_pos_plus", 0]}, "then": "$_pos_plus"},
                        {"case": {"$gte": ["$_pos_minus", 0]}, "then": "$_pos_minus"},
                        {"case": {"$gte": ["$_pos_z", 0]}, "then": "$_pos_z"},
                    ],
                    "default": -1,
                }
            }
        }
    },
    {
        "$addFields": {
            "_ts_clean": {
                "$concat": [
                    {"$substrBytes": ["$_ts_raw", 0, 19]},
                    {
                        "$cond": [
                            {"$gte": ["$_tz_pos", 0]},
                            {
                                "$substrBytes": [
                                    "$_ts_raw",
                                    "$_tz_pos",
                                    {"$subtract": [{"$strLenBytes": "$_ts_raw"}, "$_tz_pos"]},
                                ]
                            },
                            ""
                        ]
                    },
                ]
            }
        }
    },

    {"$addFields": {"_ts": {"$dateFromString": {"dateString": "$_ts_clean"}}}},

    {
        "$addFields": {
            "local_date": {
                "$dateToString": {
                    "date": "$_ts",
                    "timezone": "Europe/Rome",
                    "format": "%Y-%m-%d",
                }
            }
        }
    },

    {"$group": {"_id": "$local_date", "validated": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
    {"$project": {"_id": 0, "date_local": "$_id", "validated": 1}},
]

rows = list(articles_collection.aggregate(pipeline))
#print(rows)

import pandas as pd
import matplotlib.pyplot as plt

# Convert aggregation output to DataFrame
df = pd.DataFrame(rows)

# Make sure date column is datetime
df["date_local"] = pd.to_datetime(df["date_local"])

# Sort by date just in case
df = df.sort_values("date_local")

# Plot
plt.figure(figsize=(10, 5))
plt.bar(df["date_local"], df["validated"], color="steelblue")

plt.title("Articles Processed per Day")
plt.xlabel("Date")
plt.ylabel("Number of Articles")
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()