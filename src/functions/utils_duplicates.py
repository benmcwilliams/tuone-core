import json
from typing import List, Dict, Any

def load_json(file_path: str) -> Any:
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
# Convert duplicate_IDs to a list
def parse_duplicate_ids(duplicate_ids: Any) -> List[str]:
    if isinstance(duplicate_ids, str):
        return [id.strip() for id in duplicate_ids.split(',')]
    elif isinstance(duplicate_ids, list):
        return duplicate_ids
    return [str(duplicate_ids)]