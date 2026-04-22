# Tuone

This repository is a pipeline for turning unstructured reporting on clean technology manufacturing and industrial investment into structured data.

At a high level, it:

- collects and stores article text
- extracts entities and relationships with language models
- normalizes products, capacities, investments, owners, and locations
- reconciles multiple article-level signals into project-level facility records
- writes structured outputs to MongoDB for downstream analysis

## What This Repository Does

The aim is to identify and connect entities such as:

- companies
- factories and project sites
- products
- capacities
- investments

It then builds relationships between them, for example:

- who owns or operates a site
- what product is produced at a facility
- what capacity or investment is associated with a project
- what stage a project appears to be in

## Repository Structure

- `scrape/` and `crawl/`: scripts for collecting and updating article data
- `kg_builder/`: article-level extraction and node / relationship building
- `reconcile/`: normalization, grouping, and project-level facility writing
- `database-operations/`: one-off maintenance and migration scripts
- `mongo_client.py`: shared MongoDB connection setup
- `openai_client.py`: shared OpenAI client setup

## Pipeline Overview

The broad flow is:

1. Ingest article text into MongoDB.
2. Extract nodes and relationships from each article.
3. Normalize key attributes such as product types, ownership, capacities, amounts, and geography.
4. Group records that refer to the same underlying project.
5. Write facility-level documents and attach project events, phase summaries, and derived fields.

## Setup

The code expects local environment variables in a root `.env` file.

Common variables include:

- `MONGO_URI`
- `MONGO_DB_NAME`
- `MONGO_COLLECTION_NAME`
- `OPENAI_API_KEY`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running

The main entry points live inside the module directories. In practice, the two most important ones are:

- `python kg_builder/main.py`
- `python reconcile/main.py`

Some subdirectories also contain their own README files with more task-specific detail.

## Notes

- This is operational research / pipeline code rather than a polished package.
- MongoDB is the main working store throughout the pipeline.
- Some scripts are intended for one-off maintenance, backfills, or debugging rather than routine runs.
