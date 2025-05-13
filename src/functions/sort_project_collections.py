import json
import datetime

def load_article_dates(jsonl_path):
    """
    Load articleID -> date mappings from a JSONL file.
    Returns a dictionary mapping articleID (string) to a datetime object.
    """
    article_to_date = {}
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line.strip())
            article_id = record["ID"]
            # Parse the date in DD-MM-YYYY format
            dt = datetime.datetime.strptime(record["date"], "%d-%m-%Y")
            article_to_date[article_id] = dt
    return article_to_date


def sort_articles_by_date(project_dict, article_date_map):
    """
    Given:
      - project_dict: { projectID: [articleID1, articleID2, ...], ... }
      - article_date_map: { 'articleID': datetime_object, ... }

    Sorts each project's articles by their date in ascending chronological order.
    Returns a new dictionary with the same structure but sorted article lists.
    """
    sorted_dict = {}
    for project_id, article_ids in project_dict.items():
        # Sort by looking up the date from article_date_map
        # If an article ID is not found in article_date_map, sort it to the front
        # by assigning the minimal datetime.
        sorted_articles = sorted(
            article_ids,
            key=lambda aid: article_date_map.get(str(aid), datetime.datetime.min)
        )
        sorted_dict[project_id] = sorted_articles
    return sorted_dict


def return_sorted_project_collection(project_json_path, article_dates_jsonl_path):
    """
    Read the project->articles JSON, load article->date JSONL mappings,
    and return a new dictionary where each project's article list
    is sorted in ascending chronological order by date.
    """
    # 1. Load the project-to-articles JSON
    with open(project_json_path, 'r', encoding='utf-8') as f:
        project_data = json.load(f)
    
    # 2. Load articleID -> date mappings from JSONL
    article_date_map = load_article_dates(article_dates_jsonl_path)

    # 3. Sort the articles in each project by the associated date
    sorted_project_data = sort_articles_by_date(project_data, article_date_map)

    return sorted_project_data