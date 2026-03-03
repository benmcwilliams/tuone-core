# Reconcile

Takes the **knowledge-graph output** from `kg_builder` (nodes and relationships per article) and turns it into **flattened, merged, normalised tables** (factories, capacities, investments, JVs) and **facility-level records** in MongoDB. Includes geo-enrichment (Geonames), capacity/investment normalisation, grouping of identical projects, event attachment, and phase summaries.

## Order of operations in `main.py`

The pipeline runs in this order. Set `update_mongo_metadata` and/or `update_main_database` to control which blocks run.

### 1. Setup
- **Setup logger** — logging for the run.

### 2. Mongo metadata (if `update_mongo_metadata=True`)
- **Normalise companies** — `clean_owner_names()`: fills in `name_canon` / `inst_canon` on owner nodes where missing.
- **Query Geonames** — `query_geonames_new_cities()`: finds `{city, country}` pairs in the DB that are not yet in the Geonames lookup, calls the Geonames API, and writes results to a MongoDB collection (and geo lookup).

*(Optional, commented out: product classification sync to Mongo.)*

### 3. Main database build (if `update_main_database=True`)

- **EV volumes** — `build_zev_og_clean_excel()`: builds/updates the ZEV OG clean Excel used downstream.

- **Flatten articles** — `run_flatten_articles()`: reads articles from MongoDB (per `ARTICLE_QUERY`), flattens nodes and relationships into two dataframes → `ALL_NODES`, `ALL_RELS` (and optionally saves to Excel).

- **Build context** — `make_context_from_frames(nodes_df, rels_df)`: builds an in-memory context used by all merge views.

- **Merge views** (in parallel conceptually; run in sequence):
  - **Factory–technology** — `run_view(FACTORY_TECH_SPEC)` → `FACTORY_TECH` (capacity-centric).
  - **Company–JV** — `run_view(COMPANY_FORMS_JV_SPEC)` → `COMPANY_JV` (JV directory).
  - **Investment–funds** — `run_view(INVESTMENT_FUNDS_SPEC)` → `INVESTMENT_FUNDS` (investment-centric).
  - **Facility registry** — `build_registry_union()` → facility directory (and optional Excel).

- **Normalise capacities** — `run_capacity_normalisation_pipeline(df_capacity)` → `FACTORY_TECH_CLEAN_CAPACITIES` (and outputs).

- **Normalise investments** (two branches):
  - On capacity table: `run_investment_normalisation_pipeline(df_clean_caps)` → `FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS`.
  - On investment table: `run_investment_normalisation_pipeline(df_investment)` → `CLEAN_INVESTMENT_FUNDS`.

- **Group projects** — For each `(input_path, output_path, output_cols)` in `GROUP_SPEC`:
  - `group_projects()`: assigns a group to rows that are considered the same project (e.g. identical `adm1`, `inst_canon`, `product_lv1`), and runs capacity normalisation inside grouping.
  - Produces: grouped capacities, grouped factories, grouped investments.

### 4. Always (after optional blocks)
- **Import facilities** — `write_facilities()`: updates MongoDB with facility records (iso2, adm1, inst_canon, product_lv1, hexspaceID, etc.).
- **Attach events** — `attach_events()`: assigns events to facilities.
- **Assign phase number** — `assign_phase_num()`: sets phase numbers on facilities/documents.
- **Phase summaries** — `compute_summaries()`: computes and stores phase summary statistics.

---

## Key scripts (used by or alongside `main.py`)

| Script | Role |
|--------|------|
| **main.py** | Orchestrator: runs the full pipeline in the order above. |
| **query_geonames.py** | Queries the Geonames API and maintains a MongoDB collection (and lookup) of `{city, country}` pairs found in the DB. |
| **normalise_owners.py** | Cleans owner names and sets canonical names (`name_canon` / `inst_canon`) on nodes. |
| **normalise_products.py** | Reads the `PRODUCT_CLASSIFICATION` Excel; maps each product to `product_lv1` and `product_lv2` and writes back to MongoDB. |
| **flatten.py** | Flattens per-article nodes and relationships into global `ALL_NODES` and `ALL_RELS` (and optional Excel in `storage/output/`). |
| **merge.py** | Runs merge views: joins nodes and relationships into tables (e.g. factory–tech, company–JV, investment–funds) per specs in `src/merge_specifications.py`. |
| **registry_union.py** | Builds the facility registry (union of facilities) from the context; can output Excel. |
| **normalise_capacity.py** | Capacity normalisation pipeline (units, time, etc.) over capacity-centric tables. |
| **normalise_investment.py** | Investment normalisation pipeline (amounts, currencies, etc.) over investment tables. |
| **group.py** | Assigns a group number to rows considered the same project (e.g. identical adm1, inst_canon, product_lv1); applies capacity normalisation within the grouping step. |
| **facilities.py** | Writes/updates facility records in MongoDB (iso2, adm1, inst_canon, product_lv1, hexspaceID). |
| **attach_events.py** | Attaches events to facilities. |
| **assign_phase.py** | Assigns phase numbers to facilities/documents. |
| **phase_summary.py** | Computes phase summaries. |
| **ev_volumes.py** | Builds the ZEV OG clean Excel used in the pipeline. |

## Config and storage

- **src/config.py** — Article query, projection, and paths for all output Excel/JSON files (`storage/output/`, `storage/input/`), and `GROUP_SPEC` (input/output/columns for each grouped table).
- **src/merge_specifications.py** — Specs for factory–tech, company–JV, and investment–funds views.
- **storage/input/** — Inputs (e.g. `zev_og_clean.xlsx`, `product_classification.xlsx`).
- **storage/output/** — Flattened nodes/rels, merge views, cleaned capacities/investments, grouped tables, facilities, etc.

## Running

From **project root**, with Python path including the repo:

```bash
python reconcile/main.py
```

In `main()` at the bottom of `main.py`, set:
- `update_mongo_metadata=True/False` — run company normalisation and Geonames.
- `update_main_database=True/False` — run flatten → merge → normalise → group.
- `debug_article_id="..."` — optional MongoDB article ObjectId for per-article debug (see below).

Verbose flags at the top of `main.py` control extra logging for flatten, grouping, capacity, investment split, Geonames, and attach_events.

## Per-article debug (`debug_article_id`)

When `debug_article_id` is set to a MongoDB article ObjectId, the pipeline writes **all** debug diagnostics for that article to a **single log file** only (no extra lines in the main console). The main run prints one line with the path to that file.

- **Log file location**: `reconcile/logs/articleID/{article_id}.log` (overwritten each run). When running from the `reconcile/` directory, the path is `logs/articleID/{article_id}.log`.
- **Contents**: Flatten summary (node/relationship counts by type), merge join-chain checkpoints and drop reasons, registry-union per-view counts, grouping step-by-step row counts, and an end-of-run **Diagnosis summary** with bullet points explaining why rows were dropped (if any).

### Interpreting the log

- **Flatten**: Confirms nodes and relationships for the article and whether any relation endpoints failed to resolve (missing source/target label).
- **Merge (join_chain)**: Each view (e.g. `FACTORY_REGISTRY_DIRECT`) logs row counts after each join. If the count goes to zero at an **inner** join, the log explains that the article had no matching path (e.g. no ownership edge for that factory).
- **EU filter**: If rows exist before the filter but disappear after, the log states that they were removed because `iso2` is not in `EUROPEAN_COUNTRIES` (e.g. facility only in Turkey or outside EU).
- **Registry union**: Shows how many rows the article contributed from the direct, capacity-inferred, and investment-inferred views; if the total is zero, a drop reason explains typical causes (no ownership for EU factories, or only non-EU countries).
- **Grouping**: For each grouped table (capacities, factories, investments), logs row count after EU filter and after each required-field drop; if the article ends with zero rows, it notes whether the input was already empty or rows were dropped for missing `inst_canon`, `city_key`, `admin_group_key`, or `product_lv1`.

### Common drop reasons

| Message / reason | Meaning |
|------------------|--------|
| All rows dropped at inner join | The view requires a relationship path (e.g. `owns` + `produced_at`). The article has no such path for the relevant nodes (e.g. no ownership edge for an EU factory). |
| EU filter removed all article rows | Facilities in the article resolve to non-EU countries (`iso2` not in `EUROPEAN_COUNTRIES`). |
| No rows from any view for this article (registry) | Direct, capacity-inferred, and investment-inferred views all contributed 0 rows (join chain or EU filter removed them). |
| No rows in the input table (grouping) | The table fed into grouping already had 0 rows for this article; see merge/registry steps above. |
| All article rows dropped due to missing required field | A required column (`inst_canon`, `city_key`, `admin_group_key`, `product_lv1`) was null for every row of this article. |
