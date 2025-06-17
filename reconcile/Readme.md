# to_pand.py explainer

## Overview
 This script extracts and processes data from a MongoDB collection where each article includes nodes (e.g., companies, factories, investments) 
 and relationships (e.g., owns, funds, produced_at). Each node is given a unique ID by combining its article ID and internal ID to ensure global uniqueness.
 Relationships reference node IDs, so these are translated to the new unique node IDs. Each source and target in a relationship is also enriched
 with the type of node it refers to (e.g., company, factory), using the original node metadata. This makes it easier to group and interpret relationships later.
 
 The pipeline focuses on factories: it identifies which companies or joint ventures own them, which investments fund them, 
 what products are made there, and what capacities are installed. This is done by grouping relationship data by factory ID and enriching it 
 using metadata from the original nodes (such as name, phase, amount, status).
 
 The result is a set of clean Excel files where each factory has its ecosystem (direct links) of owners, products, investments, and capacities clearly organised
 into summary and pivoted views for easy exploration.

## Mermaid
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'fontSize': '14px' }}}%%
flowchart TD

%% Section 1: Mongo query and document loop
Start([1️⃣ Start: MongoDB query]) --> QueryMongo["1.1 Query articles with: nodes & relationships exist"]
QueryMongo -->|Projection: _id, nodes, relationships| IterateDocs["1.2 For each document"]
IterateDocs --> FlattenNodes["1.3 Flatten 'nodes' → flat rows with article_id, label"]
IterateDocs --> FlattenRels["1.4 Flatten 'relationships' → flat rows with source, target, type"]
FlattenNodes --> DFNodes["1.5 Create df_all_nodes"]
FlattenRels --> DFRels["1.6 Create df_all_rels"]
DFNodes --> UniqueID["1.7 Add unique_id = article_id + node id"]
DFNodes --> IDToLabel["1.8 Build lookup dictionaries:\nid_to_unique & id_to_label"]
DFNodes --> Role1["1.9 Used for filtering entity types:\nfactories, companies, etc."]
DFNodes --> Role2["1.10 Used to enrich metadata:\nname, status, amount, etc."]
DFNodes --> Role3["1.11 Used for lookup during relationship mapping"]
DFNodes --> Role4["1.12 Used to build enrichment dictionaries:\ninv_lookup & cap_lookup"]
DFRels --> MapSourceTarget["1.13 Use lookup to map:\nsource & target → unique_id and label"]
MapSourceTarget --> SaveRawExcel["1.14 Save df_all_nodes & df_all_rels to Excel"]

%% Section 2: Begin enrichment function
SaveRawExcel --> StartEnrich([2️⃣ run_factory_centric_enrichment])
StartEnrich --> Deduplicate["2.1 Drop duplicate rows"]
Deduplicate --> SubsetNodes["2.2 Filter df_all_nodes by label → factories, products, etc."]
Deduplicate --> SubsetRels["2.3 Filter df_all_rels by type → owns, funds, at, produced_at"]

%% Section 3: Grouping via relationships
SubsetRels --> GroupOwns["3.1 Group COMPANY → FACTORY (owns)"]
SubsetRels --> GroupOwnsJV["3.2 Group JOINT_VENTURE → FACTORY (owns)"]
SubsetRels --> GroupFunds["3.3 Group INVESTMENT → FACTORY (funds)"]
SubsetRels --> GroupProducts["3.4 Group PRODUCT → FACTORY (produced_at)"]
SubsetRels --> GroupCapacities["3.5 Group CAPACITY → FACTORY (at)"]
GroupOwns --> MergeGroups
GroupOwnsJV --> MergeGroups
GroupFunds --> MergeGroups
GroupProducts --> MergeGroups
GroupCapacities --> MergeGroups
SubsetNodes --> FactoryMeta["3.6 Extract FACTORY metadata:\nname, city, country"]
MergeGroups --> MergeFactory["3.7 Merge grouped tables on factory_unique_id"]
MergeFactory --> MergeMeta["3.8 Join with factory metadata"]

%% New arrow from factory metadata to merge step
FactoryMeta --> MergeMeta

%% Section 4: Enrichment using dictionaries
MergeMeta --> BuildLookups["4.1 Create inv_lookup & cap_lookup from df_all_nodes"]
BuildLookups --> EnrichInvest["4.2 Enrich investment fields:\nname, amount, phase, status"]
BuildLookups --> EnrichCap["4.3 Enrich capacity fields:\nname, amount, phase, status"]

%% Section 5: Excel export
EnrichInvest --> SelectCols["5.1 Select final output columns"]
EnrichCap --> SelectCols
SelectCols --> PivotViews["5.2 Explode columns for pivot views"]
PivotViews --> SaveExcel["5.3 Save multiple sheets to reconciliation_outputs_factory.xlsx"]
SaveExcel --> End([✅ 5.4 Done])
```
