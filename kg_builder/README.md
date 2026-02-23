# kg_builder

Builds a **knowledge graph** from article text: extracts **entities** (nodes) and **relationships** via LLM function calling, enriches nodes with **characteristics** (capacities, investments, products), and optionally computes **node mentions** in the text. All outputs are written back to the article documents in MongoDB.

## What it does

- **Input:** Articles in MongoDB with `paragraphs` (and `meta.category`, `meta.date`, etc.).
- **Output:** Each article document is updated with:
  - `nodes` — entities (company, factory, capacity, investment, product, joint_venture, and for subsidy articles: grantor, aid)
  - `relationships` — typed links between nodes (ownership, technological, financial_origin, financial_technological, and for subsidy articles: grantor_aid)
  - `llm_processed.run_id`, `llm_processed.ts` — processing version and timestamp
  - Optionally `mentions` and `mentions_ts` (from `run_mentions.py`)

Pipeline skips articles that are validated, already processed with the same `run_id`, or processed with a “stronger” model (e.g. won’t overwrite gpt-4o with gpt-4o-mini).

## Structure

| Path | Role |
|------|------|
| `main.py` | Entry point: loads articles from MongoDB, runs the full extraction pipeline per article, writes `nodes` and `relationships` back. |
| `run_mentions.py` | Standalone script: computes **mentions** (which node appears in which paragraph) via rule-based matching; updates `mentions` and `mentions_ts`. |
| `config.py` | Loads `EXTRACTION_CONFIG` from `extraction_config.yaml`. |
| `extraction_config.yaml` | Maps each extraction group (entities, capacities, ownership, …) to prompt file, schema file, function name, and model key. |
| `src/` | Core logic and prompts/schemas. |
| `src/process_articles.py` | Skip logic, logger setup, `call_openai_function`, `has_required_nodes_for_relationship`. |
| `src/format_prompts.py` | Prompt/schema loading, ID/type normalization, `format_nodes_for_prompt`. |
| `src/inputs.py` | `nodes_by_group_prompt`, `required_node_types`, `characteristic_node_types` (which node types feed into which relationship/characteristic groups). |
| `src/model_dictionary.py` | Model names per group and `run_id` (fine-tuned or base OpenAI models). |
| `src/check_subsidy.py` | Sets `meta.subsidy` from keyword matching (run before main pipeline in `main.py`). |
| `src/mentions.py` | Rule-based mention extraction (by name, amount, city, etc.) for use by `run_mentions.py`. |
| `src/prompts/` | Per-group prompt text (e.g. `entities-only.txt`, `ownership.txt`). |
| `src/schemas/` | JSON function schemas for OpenAI (entities, relationships, characteristics). |
| `logs/` | Per-article logs (and `logs/mentions/` for mentions). |

## Pipeline (main.py)

1. **Pre-step:** `check_subsidy_main()` — updates `meta.subsidy` for articles in configured categories using keyword match.
2. **Query:** Articles with `meta.date` > cutoff, `meta.category` in a configured list; optionally skip/limit.
3. **Per article:**
   - **Stage 1 — Entities:** Extract nodes (entities). If `meta.subsidy` is true, also extract subsidy entities (grantor, aid).
   - **Stage 2 — Characteristics:** For each characteristic group (capacities, investments, products), if the article has the right node types, call the LLM and attach results to the corresponding nodes (e.g. status, phase, product_lv1/lv2).
   - **Stage 3 — Relationships:** For each relationship group (ownership, technological, financial_origin, financial_technological; plus grantor_aid for subsidy articles), if required node types exist, extract relationships. All relationships are merged and stored.
4. **Write:** `articles_collection.update_one` sets `nodes`, `relationships`, `llm_processed.run_id`, `llm_processed.ts`.

Run and model behaviour are controlled by `model_dictionary` in `src/model_dictionary.py` (e.g. `run_id` "v2.0", fine-tuned vs base models).

## Mentions (run_mentions.py)

- **Input:** Articles that have both `nodes` and `paragraphs`.
- **Logic:** For each node, build search strings (by name, amount, city, etc. depending on node type) and find spans in the combined paragraph text; produce a list of mention objects.
- **Output:** `mentions` and `mentions_ts` on the article.
- **Run from project root:** `python kg_builder/run_mentions.py`  
  Config (dry_run, limit, article_id, categories, cutoff_date, offset) is set at the top of the file.

## Setup and run

1. **Environment:** Project root `.env` (or equivalent) with MongoDB and OpenAI credentials. `main.py` expects to be run from **project root** (it does `sys.path.append("..")` and uses `config`, `mongo_client`, `openai_client`, `utils`).
2. **Dependencies:** As per project (e.g. `pymongo`, `openai`, `python-dotenv`, `PyYAML`).
3. **Main pipeline:** From **project root**:  
   `python kg_builder/main.py`  
   Tune in `main.py`: `categories`, `cutoff_date`, `offset_articles`, and optional `.limit(n_articles)` on the find cursor.
4. **Mentions:** From **project root**:  
   `python kg_builder/run_mentions.py`  
   Edit config at top of `run_mentions.py` (categories, cutoff, limit, etc.).

## Extraction groups (summary)

| Group | Purpose |
|-------|--------|
| `entities` | Core nodes (company, factory, capacity, investment, product, joint_venture). |
| `subsidy_entities` | Grantor, aid (only when `meta.subsidy` is true). |
| `capacities`, `investments`, `products` | Characteristics attached to capacity/investment/product nodes. |
| `ownership`, `technological`, `financial_origin`, `financial_technological` | Relationships between nodes. |
| `grantor_aid` | Relationships for subsidy articles (grantor ↔ aid, etc.). |

Prompts and schemas are in `src/prompts/` and `src/schemas/`; the mapping is in `extraction_config.yaml`.
