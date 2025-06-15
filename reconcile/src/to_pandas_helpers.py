# === Flatten helper ===
def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            v = None if isinstance(v, str) and v.lower() == "null" else v
            items.append((new_key, v))
    return dict(items)