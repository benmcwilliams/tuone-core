import sys; sys.path.append("..")
from kg_builder.functions import read_prompt_from_file_only, load_function_schema, normalize_id, normalize_type, format_nodes_for_prompt, get_schema, setup_logger
from utils import ping_openai, combine_paragraphs
from kg_builder.functions import call_openai_function
from kg_builder.model_dictionary import model_dictionary
from kg_builder.inputs import relationship_groups, groups_to_prompts, nodes_by_group_prompt, characteristic_node_types, required_node_types
from openai_client import openai_client
from mongo_client import mongo_client, articles_collection
from datetime import datetime, timezone

from dotenv import load_dotenv
from bson import json_util
import re
from datetime import datetime, timezone
load_dotenv()

try:
    mongo_client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    raise

# establish openai client 
ping_openai(openai_client) 

def extract_nodes(text, model_name, logger):

    PROMPT_PATH = "prompts/entities-only.txt"
    FUNCTION_SCHEMA_PATH = "schemas/entities.json"

    function_schema = load_function_schema(FUNCTION_SCHEMA_PATH)
    prompt = read_prompt_from_file_only(PROMPT_PATH)

    user_content = f"Here is the article: {text}"

    nodes_by_category = call_openai_function(
        prompt=prompt,
        user_content=user_content,
        function_schema=function_schema,
        function_name="extract_clean_tech_entities",
        expected_top_key="nodes",
        model_name=model_name,
        logger=logger
    )

    # Flatten nodes while retaining their type
    formatted_nodes = []
    for node_type, node_categories in nodes_by_category.items():
        for node in node_categories:
            formatted_node = {
                #"article_id": article_id,
                "id": normalize_id(node.get("id")),
                "type": normalize_type(node.get("type")),
                "name": node.get("name"),
                "location": {
                    "city": node.get("location", {}).get("city", ""),
                    "country": node.get("location", {}).get("country", "")
                } if node.get("location") else None,
                "amount": node.get("amount"), #possibly to drop
                "status": node.get("status"),
            }
            formatted_nodes.append(formatted_node)

    return formatted_nodes

def extract_node_characteristics(text, nodes, relationship_group, model_name, logger):

    PROMPT_PATH = groups_to_prompts[relationship_group]
    FUNCTION_SCHEMA_PATH = f"schemas/{relationship_group}.json"

    prompt = read_prompt_from_file_only(PROMPT_PATH)
    function_schema = load_function_schema(FUNCTION_SCHEMA_PATH)

    allowed_types = nodes_by_group_prompt[relationship_group]
    compact_nodes = format_nodes_for_prompt(nodes, allowed_types)
    
    user_content = f"""Here is the article text: {text}
    Here is the list of known entities:
    {compact_nodes}
    """

    return call_openai_function(
        prompt=prompt,
        user_content=user_content,
        function_schema=function_schema,
        function_name="extract_characteristics",
        expected_top_key="node_characteristics",
        model_name=model_name,
        logger=logger
    )

def extract_relationships(text, nodes, relationship_group, model_name, logger, allowed_types=None):

    PROMPT_PATH = groups_to_prompts[relationship_group]
    FUNCTION_SCHEMA_PATH = f"schemas/{relationship_group}.json"

    prompt = read_prompt_from_file_only(PROMPT_PATH)
    function_schema = load_function_schema(FUNCTION_SCHEMA_PATH)

    allowed_types = nodes_by_group_prompt[relationship_group]
    compact_nodes = format_nodes_for_prompt(nodes, allowed_types)

    user_content = f"""Here is the article text: {text}
    Here is the list of known entities:
    {compact_nodes}
    Please extract only the specified relationship types.
    """

    # Use shared OpenAI wrapper
    raw_relationships = call_openai_function(
        prompt=prompt,
        user_content=user_content,
        function_schema=function_schema,
        function_name="extract_clean_tech_relationships",
        expected_top_key="relationships",
        model_name=model_name,
        logger=logger
    )

    # Format output
    formatted_relationships = []
    for rel in raw_relationships:
        raw_source = rel.get("source")
        raw_target = rel.get("target")
        norm_source = normalize_id(raw_source)
        norm_target = normalize_id(raw_target)

        formatted_relationships.append({
            #"article_id": article_id,
            "id": f"{norm_source}_{rel.get('type')}_{norm_target}",
            "source": norm_source,
            "target": norm_target,
            "type": rel.get("type"),
            "group": relationship_group
        })

    return formatted_relationships

def should_skip_article(article, logger, run_id):
    """Returns (proceed, text). If should skip, returns (False, None)."""

    # skip if article has been validated
    val = article.get("validation")
    if val is True:
        print("⏭️  Skipping – article is validated")
        logger.info("⏭️  Skipping – article is validated")
        return False, None

    if isinstance(val, (int, float)):
        processed_on = datetime.fromtimestamp(val, tz=timezone.utc)\
                               .strftime("%Y-%m-%d %H:%M UTC")
        print(f"⏭️  Skipping – article was validated on {processed_on}")
        logger.info("⏭️  Skipping – article was validated on %s", processed_on)
        return False, None
    
    # skip if this model architecture has already processed article
    previous_run = article.get("llm_processed", {}).get("run_id")
    if previous_run == run_id:
        print(f"⏭️  Skipping – article already processed with run_id: {run_id}")
        logger.info(f"⏭️  Skipping – article already processed with run_id: {run_id}")
        return False, None

    # skip if there is no text
    text = combine_paragraphs(article)
    if not text:
        logger.warning("⚠️ No valid text found; skipping.")
        return False, None

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

def process_articles(articles_to_process, model_dictionary):

    print_article_stats(articles_to_process)

    run_id = model_dictionary["run_id"]
    for article in articles_to_process:
        articleID  = str(article["_id"])
        logger      = setup_logger(articleID)

        print(f"📌 Processing Article: {article['title']}")
        logger.info("📌 Processing Article ID: %s — %s", articleID, article["title"])

        proceed, text = should_skip_article(article, logger, run_id)
        if not proceed:
            continue

        try:
            # extract entities
            formatted_nodes = extract_nodes(text, model_dictionary["nodes"], logger)
            logger.info(f"Formatted nodes used for all prompts hereafter: {formatted_nodes}")

            # attach characteristics to entities (capacities and investments)
            for relationship_group, config in characteristic_node_types.items():
                model_name = model_dictionary[relationship_group] # select fine-tuned model
                id_key = config["id_key"]
                type_match = config["type_match"]

                # only continue if there are nodes of this type in the article
                has_relevant_nodes = any(node.get("type") == type_match for node in formatted_nodes)
                if not has_relevant_nodes:
                    logger.info(f"⏭️ Skipping {relationship_group} – no nodes of type '{type_match}' found.")
                    continue

                logger.info(f"🔍 Extracting characteristics for node group: {relationship_group}")
                node_characteristics = extract_node_characteristics(text, formatted_nodes, relationship_group, model_name, logger)  

                # attach 'status' and 'type' to matching capacity nodes (flat list structure)
                for char in node_characteristics:
                    node_id = char.get(id_key)
                    logger.info(f"Node ID is {node_id}")
                    found_match = False

                    for node in formatted_nodes:
                        if node.get("id") == node_id and node.get("type") == type_match:
                            logger.info(f"✅ Match found for {id_key} '{node_id}' in {type_match} nodes")
                            if "status" in char:
                                node["status"] = char["status"]
                                logger.info(f"  ➕ Set status: {char['status']}")
                            if "phase" in char:
                                node["phase"] = char["phase"]
                                logger.info(f"  ➕ Set phase: {char['phase']}")
                            found_match = True

                    if not found_match:
                        logger.info(f"⚠️ No match found for {id_key} '{node_id}' in formatted_nodes")

            # extract relationships between entities
            all_relationships = []
            for relationship_group,model_name in model_dictionary.items():
                if relationship_group in ["nodes", "capacities", "investments"]: #skip nodes, capacities and investments which have logic elsewhere
                    continue

                def has_required_nodes(formatted_nodes, required_types):
                    existing_types = {node['type'] for node in formatted_nodes}
                    return any(req_type in existing_types for req_type in required_types)
                
                required_types = required_node_types.get(relationship_group, [])
                if not has_required_nodes(formatted_nodes, required_types):
                    logger.info(f"🛑 Skipping {relationship_group}: required nodes {required_types} not present.")
                    continue

                logger.info(f"- - - Querying openai for relationships: {relationship_group}, using model: {model_name}")

                allowed_types = relationship_groups[relationship_group]
                logger.info(f"Node types included in the query: {allowed_types}")

                relationships = extract_relationships(text, formatted_nodes, relationship_group, model_name, logger, allowed_types)
                all_relationships.extend(relationships)

            # update entries in mongodb with clean entities and relationships
            update_result = articles_collection.update_one(
                {"_id": article["_id"]},  #match by mongodb article id
                {"$set": {
                    "nodes": formatted_nodes or [],
                    "relationships": all_relationships or [],
                    "llm_processed.run_id": model_dictionary["run_id"],
                    "llm_processed.ts": datetime.now(timezone.utc).isoformat()
                    }})

            if update_result.modified_count > 0:
                logger.info(f"✅ Updated Article ID: {articleID} with {len(formatted_nodes)} nodes and combined text.")
            else:
                logger.info(f"⚠️ No updates made for Article ID: {articleID}.")

        except Exception as e:
            print(f"❌ Error processing Article ID {articleID}: {e}")  

n_articles = 10000
offset_articles = 0

cutoff_date = datetime(2025, 1, 1)

articles_to_process = list(
    articles_collection.find(
        {"meta.date": {"$gt": cutoff_date}},  
        {"_id": 1, "meta": 1, "title": 1, "validation": 1, "llm_processed": 1,  "paragraphs": 1}       
    )
    .sort("_id", -1)            # sort by MongoDB ObjectId (descending)
    .skip(offset_articles)      # skip first `offset` articles
    .limit(n_articles)          # limit the number of articles
)

process_articles(articles_to_process, model_dictionary)