import sys; sys.path.append("..")
from dotenv import load_dotenv
load_dotenv()
from config import EXTRACTION_CONFIG

from kg_builder.src.format_prompts import read_prompt_from_file_only, load_function_schema, normalize_id, normalize_type, format_nodes_for_prompt
from kg_builder.src.process_articles import setup_logger, print_article_stats, should_skip_article, call_openai_function, has_required_nodes_for_relationship
from kg_builder.src.check_subsidy import main as check_subsidy_main
from utils import ping_openai
from kg_builder.src.model_dictionary import model_dictionary
from kg_builder.src.inputs import nodes_by_group_prompt, characteristic_node_types, required_node_types
from mongo_client import mongo_client, articles_collection, test_mongo_connection

from datetime import datetime, timezone
from bson import json_util

# establish / test connections
test_mongo_connection()
ping_openai()

# update subsidy flags from user-added articles before processing
check_subsidy_main(dry_run=False) 

def should_process_subsidy(article: dict) -> bool:
    return bool(article.get("meta", {}).get("subsidy") is True)

def run_extraction(
    text: str,
    *,
    group: str,
    nodes: list[dict] | None,
    model_dictionary: dict,
    logger) -> list[dict]:

    """
    Run a single LLM extraction step for a given extraction group.

    Loads the group-specific prompt and function schema, builds the user
    message (optionally conditioning on known nodes), calls the configured
    OpenAI model via function calling, and post-processes the raw output into
    normalized entities or relationships.
    """
    
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
    
    """
    Normalize and format raw LLM outputs into a consistent structure.

    Applies group-specific post-processing rules to convert raw function-call
    outputs into cleaned entity or relationship dictionaries, including ID/type
    normalization and construction of stable relationship identifiers,
    turning openAI output into KG-ready. 
    Use of get means we can over-specify characteristics which only apply if present. 
    """

    logger.info("POST-PROCESSING STARTING.")
    ENTITY_GROUPS = {"entities", "subsidy_entities"}
    if group in ENTITY_GROUPS:
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

    if group in ("capacities", "investments", "products"):
        result = raw if isinstance(raw, list) else []
        return result

    elif group in ("ownership", "technological", "financial_origin", "financial_technological", "grantor_aid"):
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

def attach_characteristics_to_nodes(
    *,
    formatted_nodes: list[dict],
    node_characteristics: list[dict],
    id_key: str,
    type_match: str,
    attach_map: dict[str, str],
    logger):
    # Quick index for O(1) lookup by (id, type)
    node_index = {(n.get("id"), n.get("type")): n for n in formatted_nodes}

    for char in node_characteristics:
        node_id = char.get(id_key)
        node = node_index.get((node_id, type_match))
        if not node:
            logger.info(f"⚠️ No match found for {id_key} '{node_id}' in {type_match} nodes")
            continue

        logger.info(f"✅ Match found for {id_key} '{node_id}' in {type_match} nodes")
        for src_key, dst_key in (attach_map or {}).items():
            if src_key not in char:
                continue
            value = char[src_key]
            if value in (None, "", [], {}):
                continue

            node[dst_key] = value
            logger.info(f"  ➕ Set field '{dst_key}': {value}")

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

            # ------ 1b extract subsidy entities ------
            if should_process_subsidy(article):
                logger.info("💰 Subsidy article detected — extracting subsidy entities")
                subsidy_nodes = extract_nodes(text, "subsidy_entities", logger)
                formatted_nodes.extend(subsidy_nodes or [])

            # - - - STAGE 2: enrich entities with characteristics (capacities, investments and products)
            for relationship_group, config in characteristic_node_types.items():
                model_name = model_dictionary[relationship_group]  # select fine-tuned model
                id_key = config["id_key"]                          
                type_match = config["type_match"]
                attach_map  = config.get("attach", {})

                # only continue if there are nodes of this type in the article
                has_relevant_nodes = any(node.get("type") == type_match for node in formatted_nodes)
                if not has_relevant_nodes:
                    logger.info(f"⏭️ Skipping {relationship_group} – no nodes of type '{type_match}' found.")
                    continue

                logger.info(f"🔍 Extracting characteristics for node group: {relationship_group}")
                node_characteristics = extract_node_characteristics(text, relationship_group, formatted_nodes, logger)  

                # attach the characteristics returned by LLM inference to our JSON objects/documents
                attach_characteristics_to_nodes(
                    formatted_nodes=formatted_nodes,
                    node_characteristics=node_characteristics,
                    id_key=id_key,
                    type_match=type_match,
                    attach_map=attach_map,
                    logger=logger,
                )

            # - - - STAGE 3: extract relationships between entities
            all_relationships = []

            RELATIONSHIP_GROUPS = [
                "ownership",
                "technological",
                "financial_origin",
                "financial_technological"
            ]

            # conditionally add subsidy relationships
            if article.get("meta", {}).get("subsidy") is True:
                RELATIONSHIP_GROUPS.append("grantor_aid")

            for relationship_group in RELATIONSHIP_GROUPS:

                required_types = required_node_types.get(relationship_group, [])
                if not has_required_nodes_for_relationship(formatted_nodes, required_types):
                    logger.info(f"🛑 Skipping {relationship_group}: required nodes {required_types} not present.")
                    continue

                logger.info(f"- - - Querying openai for relationships: {relationship_group}")

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

offset_articles = 0
#categories = ["user", "electrive", "justauto", "pvmagazine", "pvtech", "renewsBiz", "offshorewind"]
#categories = ["user", "electrive", "pvmagazine", "pvtech", "transformers-magazine", ]
categories = ["electrive"]

cutoff_date = datetime(2021, 1, 1)

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