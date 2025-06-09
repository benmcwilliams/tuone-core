import re

def clean_text(text: str) -> str:
    """
    Minimal normalization:
      • lowercase everything
      • strip URLs
      • collapse multiple spaces / new-lines
      • keep only letters, numbers, punctuation . , : ; - and spaces
    """
    text = text.lower()
    # remove urls
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    # keep selected characters, drop the rest
    text = re.sub(r"[^a-z0-9.,:;\-\s]", " ", text)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text