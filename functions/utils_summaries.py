from openai import OpenAI
import os
import re

openAI_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openAI_api_key,
  )

def generate_summary(model, summary_prompt, company, location, country, text):

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": summary_prompt},
            {"role": "user", "content": f''' 
            Please summarise the {company} facility in {location}, {country}.
            Here are the articles: {text}
            '''
            }
        ],
        temperature=0)

    summary = completion.choices[0].message.content
    return summary

def get_full_articles_from_IDs(article_lookup, article_ids):
    """
    Given:
      - article_lookup: a dictionary keyed by articleID (strings),
        each value is an article record containing e.g. meta["date"], title, paragraphs, etc.
      - article_ids: a list of article IDs (could be int or str).
    
    Returns a list of dictionaries. Each dict has:
      {
        "article_number": <1-based index>,
        "date_of_publication": <date from meta["date"]>,
        "title": <article's title>,
        "main_text": <all paragraphs concatenated into a single string>
      }
    If an ID is not found in the lookup, we use None for its values.
    """
    results = []
    for idx, article_id in enumerate(article_ids, start=1):
        article_id_str = str(article_id)  # Convert to string for dictionary lookup
        if article_id_str in article_lookup:
            record = article_lookup[article_id_str]
            date_of_publication = record["meta"].get("date", "")
            title = record.get("title", "")
            paragraphs = record.get("paragraphs", {})
            # Combine all paragraph values into one text block
            main_text = " ".join(paragraphs.values())
            
            results.append({
                "article_number": idx,
                "date_of_publication": date_of_publication,
                "title": title,
                "main_text": main_text
            })
        else:
            # For any ID not found in our lookup
            results.append({
                "article_number": idx,
                "date_of_publication": None,
                "title": None,
                "main_text": None
            })
    return results

def write_to_txt_file(output_text, folder_path, filename):
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Define the full path to the file
    file_path = os.path.join(folder_path, filename)
    
    # Write the output text to the file
    with open(file_path, 'w') as f:
        f.write(output_text)
    
    print(f"- - - - Text written to {file_path}")

def append_sections_within_text_files(file1_path, file2_path):
    # Define section titles (with possible variations)
    sections = [
        "Technology and Operations",
        "Investment and Development",
        "Project Status and Milestones",
        "Labour",
        "Ownership Structure"
    ]
    
    # Regular expression to match section titles (numbers, ###, or bold text)
    section_pattern = re.compile(rf"(\d*\.*\s*(?:{'|'.join(re.escape(title) for title in sections)}))", re.IGNORECASE)
    
    # Function to parse a file into sections
    def parse_file(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        
        matches = list(section_pattern.finditer(content))
        sections_dict = {}
        
        for i, match in enumerate(matches):
            section_title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections_dict[section_title] = content[start:end].strip()
        
        return sections_dict
    
    # Parse both files
    file1_sections = parse_file(file1_path)
    file2_sections = parse_file(file2_path)
    
    # Combine content for each section
    combined_sections = {}
    for section in sections:
        section_key1 = next((key for key in file1_sections if re.search(section, key, re.IGNORECASE)), None)
        section_content_file1 = file1_sections.get(section_key1, "") if section_key1 else ""
        
        section_key2 = next((key for key in file2_sections if re.search(section, key, re.IGNORECASE)), None)
        section_content_file2 = file2_sections.get(section_key2, "") if section_key2 else ""
        
        combined_sections[section] = (section_content_file1 + "\n\n" + section_content_file2).strip()
    
    # Generate the combined text
    combined_text = ""
    for section, content in combined_sections.items():
        combined_text += f"### {section}\n\n{content}\n\n"
    
    return combined_text

def read_prompt_with_summaries(prompt_file_path, primary_summary):
    with open(prompt_file_path, 'r') as file:
        prompt_template = file.read()
    return prompt_template.format(first=primary_summary)

def additional_notes_on_summary(model, summary_prompt, alternative_summary):

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": summary_prompt},
            {"role": "user", "content": f'''Secondary Source: 
            {alternative_summary}
            '''
            }
        ],
        temperature=0)

    summary = completion.choices[0].message.content
    return summary