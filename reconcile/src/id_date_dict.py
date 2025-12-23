import sys; sys.path.append("../..")
from datetime import datetime
from mongo_client import articles_collection
import logging
from dateutil import parser  # Add this import

# Create named logger
logger = logging.getLogger("article_dates_updater")
system_logger = logging.getLogger("main")

if not logger.hasHandlers():
    logger.setLevel(logging.INFO)

    # Let messages also propagate to root (main logger)
    logger.propagate = False
    log_path = f"logs/article_dates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def safe_parse_date(date_value):
    """Safely parse date value that could be datetime, string, or other format"""
    if isinstance(date_value, datetime):
        return date_value
    
    if isinstance(date_value, str):
        try:
            # Try to parse the string as a date
            parsed_date = parser.parse(date_value)
            logger.debug(f"✅ Successfully parsed string date: {date_value} -> {parsed_date}")
            return parsed_date
        except (ValueError, TypeError) as e:
            logger.debug(f"⚠️ Failed to parse string date '{date_value}': {e}")
            return None
    
    logger.debug(f"⚠️ Unsupported date type: {type(date_value).__name__}")
    return None

def get_article_id_to_date_map():
    articles_to_process = list(
        articles_collection.find(
            {},
            {
                "_id": 1,
                "meta.date": 1
            }
        )
        .sort("_id", -1)
    )

    id_to_date = {}
    
    # DEBUG: Track dictionary creation
    dict_creation_stats = {
        'total_articles_processed': len(articles_to_process),
        'articles_with_meta': 0,
        'articles_with_date': 0,
        'articles_with_datetime': 0,
        'articles_with_string_date': 0,
        'articles_skipped': 0,
        'skipped_reasons': {}
    }

    logger.debug("🔍 DEBUGGING DICTIONARY CREATION:")
    logger.debug("=" * 50)

    for article in articles_to_process:
        article_id = str(article["_id"])
        
        if "meta" not in article:
            dict_creation_stats['articles_skipped'] += 1
            dict_creation_stats['skipped_reasons']['no_meta'] = dict_creation_stats['skipped_reasons'].get('no_meta', 0) + 1
            logger.debug(f"❌ Article failed {article_id}: NO META FIELD")
            continue
            
        dict_creation_stats['articles_with_meta'] += 1
        
        if "date" not in article["meta"]:
            dict_creation_stats['articles_skipped'] += 1
            dict_creation_stats['skipped_reasons']['no_date'] = dict_creation_stats['skipped_reasons'].get('no_date', 0) + 1
            logger.debug(f"❌ Article failed {article_id}: NO DATE FIELD IN META")
            continue
            
        dict_creation_stats['articles_with_date'] += 1
        date_value = article["meta"]["date"]
        
        # Try to parse the date safely
        parsed_date = safe_parse_date(date_value)
        
        if parsed_date:
            if isinstance(date_value, datetime):
                dict_creation_stats['articles_with_datetime'] += 1
                logger.debug(f"✅ Article {article_id}: Original datetime = {parsed_date}")
            else:
                dict_creation_stats['articles_with_string_date'] += 1
                logger.debug(f"✅ Article {article_id}: Parsed string date = {parsed_date}")
            
            formatted_date = parsed_date.strftime("%Y-%m")
            id_to_date[article_id] = formatted_date
            logger.debug(f"   → Formatted as: {formatted_date}")
        else:
            dict_creation_stats['articles_skipped'] += 1
            reason = f"unparseable_{type(date_value).__name__}"
            dict_creation_stats['skipped_reasons'][reason] = dict_creation_stats['skipped_reasons'].get(reason, 0) + 1
            logger.debug(f"❌ Article failed {article_id}: Could not parse date '{date_value}' (type: {type(date_value).__name__})")

    logger.debug("=" * 50)
    logger.debug(f"📊 DICTIONARY CREATION SUMMARY:")
    logger.debug(f"   Total articles processed: {dict_creation_stats['total_articles_processed']}")
    logger.debug(f"   Articles with meta field: {dict_creation_stats['articles_with_meta']}")
    logger.debug(f"   Articles with date field: {dict_creation_stats['articles_with_date']}")
    logger.debug(f"   Articles with datetime: {dict_creation_stats['articles_with_datetime']}")
    logger.debug(f"   Articles with string date: {dict_creation_stats['articles_with_string_date']}")
    logger.debug(f"   Articles skipped: {dict_creation_stats['articles_skipped']}")
    logger.debug(f"   Dictionary size: {len(id_to_date)}")
    logger.debug(f"   Success rate: {(dict_creation_stats['articles_with_datetime'] + dict_creation_stats['articles_with_string_date'])/dict_creation_stats['total_articles_processed']*100:.1f}%")
    
    if dict_creation_stats['skipped_reasons']:
        logger.debug(f"   Skip reasons:")
        for reason, count in dict_creation_stats['skipped_reasons'].items():
            logger.debug(f"     {reason}: {count}")

    return id_to_date