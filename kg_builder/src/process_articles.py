import sys; sys.path.append("..")
import json
from bson import json_util
import re
from .inputs import relationship_groups
import os
import logging
from functools import lru_cache 
from openai_client import openai_client
from utils import combine_paragraphs
from datetime import datetime, timezone

def should_skip_article(article, run_id):
    """Returns (proceed, text). If should skip, returns (False, None)."""

    # skip if article has been validated
    val = article.get("validation")
    if val is True:
        print("⏭️  Skipping – article is validated")
        return False, None

    if isinstance(val, (int, float)):
        processed_on = datetime.fromtimestamp(val, tz=timezone.utc)\
                               .strftime("%Y-%m-%d %H:%M UTC")
        print(f"⏭️  Skipping – article was validated on {processed_on}")
        return False, None
    
    # skip if this model architecture has already processed article
    previous_run = article.get("llm_processed", {}).get("run_id")
    if previous_run == run_id:
        print(f"⏭️  Skipping – article already processed with run_id: {run_id}")
        return False, None

    # skip if there is no text
    text = combine_paragraphs(article)
    if not text:
        return False, None
    
    # if we reach here, we are going to process it
    if previous_run is None:
        print(f"✅ Processing – no previous run_id found")
    else:
        print(f"✅ Overwiting run_id: {previous_run}. Processing article with run_id: {run_id}")

    return True, text

def print_article_stats(articles):
    """
    Print basic descriptive statistics for a list of article documents.
    """
    n_total = len(articles)
    n_validated = sum(1 for a in articles if "validation" in a and a["validation"] is not None)
    n_llm_processed = sum(1 for a in articles if "llm_processed" in a and a["llm_processed"] is not None)

    print("\n📊 Descriptive Stats (from articles_to_process)")
    print(f"🧾 Total articles loaded: {n_total}")
    print(f"✅ Validated: {n_validated}")
    print(f"❌ Not validated: {n_total - n_validated}")
    print(f"🤖 LLM processed: {n_llm_processed}")
    print(f"🕳️ Not LLM processed: {n_total - n_llm_processed}")

### Logging utils

def setup_logger(article_id, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(f"article_{article_id}")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_path = os.path.join(log_dir, f"{article_id}.log")
        handler = logging.FileHandler(file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

### OpenAI Utils

def call_openai_function(
    prompt: str,
    user_content: str,
    function_schema: dict,
    function_name: str,
    expected_top_key: str,
    model_name: str,
    logger,
):
    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content}
            ],
            functions=[function_schema],
            function_call={"name": function_name},
            temperature=0
        )

        function_args = response.choices[0].message.function_call.arguments
        parsed = json.loads(function_args)

        logger.info("✅ OpenAI returned output:")
        logger.info(json.dumps(parsed, indent=2))

        if expected_top_key not in parsed:
            raise ValueError(f"❌ Expected key '{expected_top_key}' not found in OpenAI output.")

        return parsed[expected_top_key]

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return []
    except Exception as e:
        print(f"❌ OpenAI call failed: {e}")
        return []