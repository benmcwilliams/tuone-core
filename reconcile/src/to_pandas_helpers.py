# === Flatten helper ===
def flatten_dict(d, parent_key='', sep='_'):

    """
    Recursively flattens a nested dictionary into a single-level dict with compound keys.

    Parameters:
    - d: dict
        The dictionary to flatten.
    - parent_key: str, default ''
        A prefix for key names, used internally for recursion to build compound keys.
    - sep: str, default '_'
        Separator to insert between parent and child key names.

    Returns:
    - flat_dict: dict
        A new dictionary where nested keys are joined by `sep` and values are preserved.

    Example:
    >>> flatten_dict({'a': {'b': 1}, 'c': 2})
    {'a_b': 1, 'c': 2}
    """

    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            v = None if isinstance(v, str) and v.lower() == "null" else v
            items.append((new_key, v))
    return dict(items)