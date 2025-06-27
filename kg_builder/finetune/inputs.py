# which node types are allowed for the query to return a group of relationships
allowed_types_dict = {
    "ownership": ["company", "joint_venture", "factory"],
    "technological": ["factory", "capacity", "product"],
    "financial_origin": ["company", "joint_venture", "investment"],
    "financial_technological": ["investment", "capacity", "factory", "product"],
    "capacities": ["capacity"],
    "investments": ["investment"]
}

# which prompts to use for each group
groups_to_prompts = {
    "ownership": "prompts/ownership.txt",
    "technological": "prompts/technological.txt",
    "financial_origin": "prompts/financial-origin.txt",
    "financial_technological": "prompts/financial-technological.txt",
    "capacities": "prompts/capacities.txt",
    "investments": "prompts/investments.txt"
}