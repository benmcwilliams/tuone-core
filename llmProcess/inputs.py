relationship_groups = {
    "ownership": ["forms", "owns"],
    "technological": ["at", "produced_at", "quantifies"],
    "financial_origin": ["invests", "recieves"],
    "financial_technological": ["enables", "targets", "funds"]
}

groups_to_prompts = {
    "ownership": "prompts/ownership.txt",
    "technological": "prompts/technological.txt",
    "financial_origin": "prompts/financial_origin.txt",
    "financial_technological": "prompts/financial_technological.txt"
}

### define a dictionary to map relationship groups to the node_types that are allowed when they are queried
