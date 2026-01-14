# which node types are allowed for the query to return a group of relationships
allowed_types_dict = {
    "ownership": ["company", "joint_venture", "factory"],
    "technological": ["factory", "capacity", "product"],
    "financial_origin": ["company", "joint_venture", "investment"],
    "financial_technological": ["investment", "capacity", "factory", "product"],
    "capacities": ["capacity"],
    "investments": ["investment"],
    "products": ["product"],
}

# which prompts to use for each group
groups_to_prompts = {
    "ownership": "kg_builder/src/prompts/ownership.txt",
    "technological": "kg_builder/src/prompts/technological.txt",
    "financial_origin": "kg_builder/src/prompts/financial_origin.txt",
    "financial_technological": "kg_builder/src/prompts/financial_technological.txt",
    "capacities": "kg_builder/src/prompts/capacities.txt",
    "investments": "kg_builder/src/prompts/investments.txt",
    "products": "kg_builder/src/prompts/products.txt"
}