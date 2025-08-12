import sys; sys.path.append("..")
from dotenv import load_dotenv
load_dotenv()
from config import EXTRACTION_CONFIG

from kg_builder.src.format_prompts import read_prompt_from_file_only, load_function_schema, normalize_id, normalize_type, format_nodes_for_prompt
from kg_builder.src.process_articles import setup_logger, print_article_stats, should_skip_article, call_openai_function, has_required_nodes_for_relationship
from utils import ping_openai
from kg_builder.src.model_dictionary import model_dictionary
from kg_builder.src.inputs import nodes_by_group_prompt, characteristic_node_types, required_node_types
from mongo_client import mongo_client, articles_collection, test_mongo_connection

from datetime import datetime, timezone
from bson import json_util
#import re

# establish / test connections
test_mongo_connection()
ping_openai() 

def run_extraction(
    text: str,
    *,
    group: str,
    nodes: list[dict] | None,
    model_dictionary: dict,
    logger,
) -> list[dict]:
    
    cfg = EXTRACTION_CONFIG[group]
    logger.info(f"Extracting: {cfg}")

    # 1. load prompt & schema
    prompt = read_prompt_from_file_only(cfg["prompt"])
    schema = load_function_schema(cfg["schema"])

    # 2. build user_content
    if nodes:
        allowed = nodes_by_group_prompt.get(group)
        compact = format_nodes_for_prompt(nodes, allowed)
        user_content = f"Here is the article text:\n\n{text}\n\nKnown entities:\n{compact}"
    else:
        user_content = f"Here is the article:\n\n{text}"

    # 3. call the LLM
    model_name = model_dictionary[cfg["model_key"]]
    
    raw = call_openai_function(
        prompt=prompt,
        user_content=user_content,
        function_schema=schema,
        function_name=cfg["function_name"],
        expected_top_key=cfg["top_key"],
        model_name=model_name,
        logger=logger,
    )

    # 4. post-process
    result = post_process(raw, cfg, group, logger)
    return result

def post_process(raw: list | dict, cfg: dict, group: str, logger) -> list[dict]:
    
    logger.info("POST-PROCESSING STARTING.")
    if group == "entities":
        formatted = []
        for t, items in raw.items():

            for i, node in enumerate(items):

                formatted_node = {
                    "id": normalize_id(node.get("id", "")),
                    "type": normalize_type(node.get("type", "")),
                    "name": node.get("name", ""),
                    "location": (
                        {
                            "city": node.get("location", {}).get("city",""),
                            "country": node.get("location", {}).get("country","")
                        }
                        if node.get("location") else None
                    ),
                    "amount": node.get("amount"),
                    "status": node.get("status"),
                }
                formatted.append(formatted_node)
        return formatted

    if group in ("capacities", "investments"):
        result = raw if isinstance(raw, list) else []
        return result

    elif group in ("ownership", "technological", "financial_origin", "financial_technological"):
        formatted = []
        for i, rel in enumerate(raw):
            src = normalize_id(rel.get("source", ""))
            tgt = normalize_id(rel.get("target", ""))
            formatted_rel = {
                "id": f"{src}_{rel.get('type', '')}_{tgt}",
                "source": src,
                "target": tgt,
                "type": rel.get("type", ""),
                "group": group
            }
            formatted.append(formatted_rel)
        return formatted
    else:
        raise ValueError(f"Unknown group {group!r}")

def extract_nodes(text, group, logger):
    
    result = run_extraction(
        text,
        group=group,
        nodes=None,
        model_dictionary=model_dictionary,
        logger=logger,
    )

    return result

def extract_node_characteristics(text, group, nodes, logger):

    result = run_extraction(
        text,
        group=group,
        nodes=nodes,
        model_dictionary=model_dictionary,
        logger=logger,
    )

    return result 

def extract_relationships(text, group, nodes, logger):

    result = run_extraction(
        text,
        group=group,
        nodes=nodes,
        model_dictionary=model_dictionary,
        logger=logger,
    )

    return result 

def process_articles(articles_to_process, model_dictionary):

    print_article_stats(articles_to_process)

    run_id = model_dictionary["run_id"]
    for article in articles_to_process:
        articleID  = str(article["_id"])

        proceed, text = should_skip_article(article, run_id)
        if not proceed:
            continue

        #set up logger
        print(f"📌 Processing Article: {article['title']}")
        logger      = setup_logger(articleID)
        logger.info(f"🔍 Text length: {len(text)} characters")
        logger.info("📌 Processing Article ID: %s — %s", articleID, article["title"])

        try:
            # - - - STAGE 1: extract entities (using finetuned GPT-4o-mini)
            formatted_nodes = extract_nodes(text, "entities", logger)

            # - - - STAGE 2: enrich entities with characteristics (capacities and investments)
            for relationship_group, config in characteristic_node_types.items():
                model_name = model_dictionary[relationship_group]  # select fine-tuned model
                id_key = config["id_key"]                          
                type_match = config["type_match"]

                # only continue if there are nodes of this type in the article
                has_relevant_nodes = any(node.get("type") == type_match for node in formatted_nodes)
                if not has_relevant_nodes:
                    logger.info(f"⏭️ Skipping {relationship_group} – no nodes of type '{type_match}' found.")
                    continue

                logger.info(f"🔍 Extracting characteristics for node group: {relationship_group}")
                node_characteristics = extract_node_characteristics(text, relationship_group, formatted_nodes, logger)  

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

            # - - - STAGE 3: extract relationships between entities
            all_relationships = []
            for relationship_group,model_name in model_dictionary.items():

                if relationship_group in ["nodes", "capacities", "investments"]: # skip nodes, capacities and investments prompts which have logic elsewhere
                    continue
                
                required_types = required_node_types.get(relationship_group, [])
                if not has_required_nodes_for_relationship(formatted_nodes, required_types):
                    logger.info(f"🛑 Skipping {relationship_group}: required nodes {required_types} not present.")
                    continue

                logger.info(f"- - - Querying openai for relationships: {relationship_group}, using model: {model_name}")

                relationships = extract_relationships(text, relationship_group, formatted_nodes, logger)
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

        finally:
            # 🔒 Close all handlers to avoid too many open files
            handlers = logger.handlers[:]
            for handler in handlers:
                handler.close()
                logger.removeHandler(handler)
            print(f"🔒 Closed logger for article {articleID}. Remaining handlers: {len(logger.handlers)}")

#n_articles = 200
offset_articles = 0
categories = ["electrive", "pvmagazine"]

cutoff_date = datetime(2025, 1, 1)

articles_to_process = list(
    articles_collection.find(
        {"meta.date": {"$gt": cutoff_date},
         "meta.category": {"$in": categories}},  
        {"_id": 1, "meta": 1, "title": 1, "validation": 1, "llm_processed": 1,  "paragraphs": 1}       
    )
    .sort("_id", -1)            # sort by MongoDB ObjectId (descending)
    .skip(offset_articles)      # skip first `offset` articles
    #.limit(n_articles)          # limit the number of articles
)

process_articles(articles_to_process, model_dictionary)