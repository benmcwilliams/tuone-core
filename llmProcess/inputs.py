# which relationship types exist for each group
relationship_groups = {
    "ownership": ["forms", "owns"],
    "technological": ["at", "produced_at", "quantifies"],
    "financial_origin": ["invests", "recieves"],
    "financial_technological": ["enables", "targets", "funds"]
}

# which prompts to use for each group
groups_to_prompts = {
    "ownership": "prompts/ownership.txt",
    "technological": "prompts/technological.txt",
    "financial_origin": "prompts/financial-origin.txt",
    "financial_technological": "prompts/financial-technological.txt"
}

# which node types are allowed for the query to return a group of relationships
nodes_by_group_prompt = {
    "ownership": ["company", "joint_venture", "factory"],
    "technological": ["factory", "capacity", "product"],
    "financial_origin": ["company", "joint_venture"],
    "financial_technological": ["investment", "capacity", "factory", "product"]
}
