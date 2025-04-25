# Step 1. MongoDB to Panda Dataframes
## Step 1.1 Retrieve metadata from MongoDB
## Step 1.2 Retrieve data from MongoDB

This script connects to a MongoDB collection to extract and process entity and relationship data from articles for network analysis.

It queries up to 800 articles where:

- Entities (nodes_ben) and full text (combined_text) exist.

- The article ID (meta.ID) starts with "27".

The script flattens nested entity and relationship data into two structured pandas DataFrames:

- df_all_nodes: contains nodes (entities) with unique identifiers.

-  df_all_rels: contains relationships between nodes, with source/target mapped to these unique IDs.

Relationship types include ownership, technological, financial origin, and financial links. The script ensures that all relationship endpoints are properly connected by building lookup dictionaries for node IDs and labels.

# Step 2. Rule based node matching

# Step 2.1 Schema

Keeps only nodes that meet the schema requirements. 

+ add the schema here 

# Step 2.2 Joint venture

This script manages the grouping of joint venture names by detecting similar or duplicate entries using fuzzy matching (based on name similarity). It allows users to iteratively refine groupings directly through an Excel file (joint_venture_groups.xlsx), supporting manual edits and automatic updates.

Names are grouped together if:

- They are exactly the same (case-insensitive i.e. case sensitive means that uppercase and lowercase letters are treated as different characters).

- Their similarity score (using fuzz.ratio, partial_ratio, or token_set_ratio from fuzzywuzzy) is 90% or higher.

- Already grouped names (in input_1) are considered canonical — new matches are added to these groups unless they form a new cluster. i.e. The first name in each row of input_1 is considered the "canonical" name for that group. This name is fixed unless you manually move or edit it.



Excel Structure:

- input_1: Main editable sheet where joint venture groups are listed (one group per row, names in columns).

- input_0: Backup copy of input_1 (previous state before each run).

- output_1: Snapshot of the updated input_1 after processing.


Action: 
1.	Prepare or edit groups in input_1.
2.	Run the script to detect and update groups.
3.	Review highlighted new entries.
4.	Adjust manually if needed and re-run.
5.	Use output_1 as a stable snapshot of results.

## Step 2.4 Factory
This script groups factory locations by city name and geographic proximity (within 30 km) and allows manual override and iteration via an Excel file (factory_groups.xlsx). It combines automatic geo-clustering with user-defined city groups, ensuring flexibility and control over the grouping process.

Factory are grouped together if:

- Factories with latitude/longitude within 30 km of each other are clustered automatically.

- Geolocation is obtained via the city and country if coordinates are missing.

- Automatic clustering respects your manual groupings first. Only unassigned factories are clustered automatically.

# Step 3. Humain validation

## Step3.x Factory

A. 
This script performs entity matching and deduplication (reconciliation) for:

- Companies

- Joint Ventures (JVs)

- Products

It uses predefined groups from Excel files (e.g., company_groups.xlsx) to merge duplicate entities into canonical names and generate consistent IDs. The script also prepares a factory merge preview, grouping factories owned by the same entity within the same location group, allowing manual review before applying final merges.

Excel structure (factory_merge_preview.xlsx):
- input_0 / input_0_jv	Snapshot of the suggested groupings (read-only).
- input_1 / input_1_jv	Editable: Review and manually adjust factory groups. Group by entity and city by listing factory unique IDs together.

B. 
This part of the script applies the factory groupings defined in the preview file (factory_merge_preview.xlsx). After manual review and editing of the preview, this block finalizes the merges by:

- Updating factory IDs.

- Deduplicating factory entries.

- Remapping relationships.

- Saving the fully reconciled output.

