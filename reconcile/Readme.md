*query_geonames.py*
Queries the geonames API and creates a monogdb collection with all {city, country} pairs in the database.

*normalise_products.py*
Reads PRODUCT_CLASSIFICATION dictionary. This is an excel file where we manually assign product_lv1 and
product_lv2. Each product is mapped to its respective lv1 and lv2 and this is stored directly in mongodb.

*flatten.py* 
Outputs flattened set of nodes and relationships. 
- ALL_NODES
- ALL_RELS

*merge.py*
Merges *nodes* and *relationships* to form connected segments of the knowledge graph. Currently used to output a table of unique factories, their owners, capacities and products present at the facility. 

*group.py*
Applies a group number to all rows of *FACTORY_TECH* which are considered identical. Grouping is for cases that have identical adm1, inst_canon and product_lvl1. 
- Applies capacity normalisation pipeline from *normalise_capacity.py*