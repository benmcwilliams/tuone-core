def combine_paragraphs(article):
    paragraphs = article.get('paragraphs', [])
    # Handle missing or empty paragraphs
    if not paragraphs:
        print("⚠️ No paragraphs found in the article.")
        return ""

    combined_text = ""
    for para_obj in paragraphs:
        for key in sorted(para_obj.keys()):
            combined_text += para_obj[key].strip() + " "

    return combined_text.strip()