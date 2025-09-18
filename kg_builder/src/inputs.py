# which relationship types exist for each group
relationship_groups = {
    "ownership": ["forms", "owns"],
    "technological": ["at", "produced_at", "quantifies"],
    "financial_origin": ["invests", "recieves"],
    "financial_technological": ["enables", "targets", "funds"]
}

# # which prompts to use for each group
# groups_to_prompts = {
#     "ownership": "src/prompts/ownership.txt",
#     "technological": "src/prompts/technological.txt",
#     "financial_origin": "src/prompts/financial-origin.txt",
#     "financial_technological": "src/prompts/financial-technological.txt",
#     "capacities": "src/prompts/capacities.txt",
#     "investments": "src/prompts/investments.txt"
# }

# which node types are allowed for the query to return a group of relationships
nodes_by_group_prompt = {
    "ownership": ["company", "joint_venture", "factory"],
    "technological": ["factory", "capacity", "product"],
    "financial_origin": ["company", "joint_venture", "investment"],
    "financial_technological": ["investment", "capacity", "factory", "product"],
    "capacities": ["capacity"],
    "investments": ["investment"],
    "products": ["product"]
}

# at least one of the following nodes is needed for the relationship type to be processed
required_node_types = {
    "ownership": ["factory", "joint_venture"],
    "technological": ["product", "capacity"],
    "financial_origin": ["investment"],
    "financial_technological": ["investment"],
}

# keys for extracting characteristics about particular nodes
characteristic_node_types = {
    "capacities": {
        "id_key": "capacity_ID",
        "type_match": "capacity",
        "attach": {"status": "status", "phase": "phase", "additional": "additional"},
    },
    "investments": {
        "id_key": "investment_ID",
        "type_match": "investment",
        "attach": {"status": "status", "phase": "phase"},
    },
    "products": {
        "id_key": "product_ID",
        "type_match": "product",
        "attach": {"product_lv1": "product_lv1", "product_lv2": "product_lv2"},
    }
}