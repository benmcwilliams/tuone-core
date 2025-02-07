import pymongo

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db_ugne = client["ugne_latest"]
db_ben = client["ben_latest"]

collection_ugne = db_ugne["projects"]
collection_ben = db_ben["projects"]

def find_differences():
    # Get all files where checked == True in ugne_latest
    ugne_files = list(collection_ugne.find({"checked": True}))

    differences = []

    for file in ugne_files:
        filename = file["_id"]  # Unique filename

        # Find the corresponding file in ben_latest
        ben_file = collection_ben.find_one({"_id": filename})

        if ben_file is None:
            # If the file doesn't exist in ben_latest, mark all fields as different
            diff_fields = {key: {"ben": None, "ugne": file[key]} for key in file if key != "_id"}
            differences.append({"filename": filename, "differences": diff_fields})
        else:
            # Compare fields
            diff_fields = {}
            for key in file:
                if key not in ["_id", "checked"]:  # Ignore _id and checked field
                    ben_value = ben_file.get(key, None)  # Get value from ben_latest (default to None)
                    ugne_value = file[key]  # Value from ugne_latest
                    if ben_value != ugne_value:
                        diff_fields[key] = {"ben": ben_value, "ugne": ugne_value}

            # If there are differences, add them
            if diff_fields:
                differences.append({"filename": filename, "differences": diff_fields})

    return differences

# Run the function
diff_results = find_differences()

# Pretty print the output
for diff in diff_results:
    print(f"\n🔍 **Filename:** {diff['filename']}")
    for field, values in diff["differences"].items():
        print(f"  - {field}:")
        print(f"    - 📁 ben_latest: {values['ben']}")
        print(f"    - 📁 ugne_latest: {values['ugne']}")