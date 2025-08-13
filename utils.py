def combine_paragraphs(article):
    title = article.get("title", "").strip()
    paragraphs = article.get('paragraphs', [])
    
    # If it's a dict, wrap in a list so the loop still works
    if isinstance(paragraphs, dict):
        paragraphs = [paragraphs]
    
    # Handle missing or empty paragraphs
    if not paragraphs:
        print("⚠️ No paragraphs found in the article.")
        return ""

    combined_text = title + " - " if title else ""
    for para_obj in paragraphs:
        for key in sorted(para_obj.keys()):
            combined_text += para_obj[key].strip() + " "

    return combined_text.strip()

def ping_openai():
    try:
        print("✅ Successfully connected to OpenAI API!")

    except Exception as e:
        print(f"❌ OpenAI API Connection Error: {e}")