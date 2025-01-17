import pandas as pd

def get_unique_elements(list_a, list_b):
    """Returns a list of elements that are in list_a but not in list_b."""
    return [item for item in list_a if item not in list_b]

def save_urls_to_csv(urls, file_path):
    """Saves the URLs to a CSV file."""
    df = pd.DataFrame(list(set(urls)), columns=['URL'])
    df.sort_values('URL').to_csv(file_path, index=False)
    print(f'Saved {len(urls)} URLs to {file_path}') 