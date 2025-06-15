# which node types are allowed for the query to return a group of relationships
allowed_types_dict = {
    "ownership": ["company", "joint_venture", "factory"],
    "technological": ["factory", "capacity", "product"],
    "financial_origin": ["company", "joint_venture"],
    "financial_technological": ["investment", "capacity", "factory", "product"],
    "capacities": ["capacity"],
    "investments": ["investment"]
}

# which prompts to use for each group
groups_to_prompts = {
    "ownership": "/Users/ben/Documents/bruegel/data_new/WORKING/INDUSTRY/tuone_v6/llmProcess/prompts/ownership.txt",
    "technological": "/Users/ben/Documents/bruegel/data_new/WORKING/INDUSTRY/tuone_v6/llmProcess/prompts/technological.txt",
    "financial_origin": "/Users/ben/Documents/bruegel/data_new/WORKING/INDUSTRY/tuone_v6/llmProcess/prompts/financial-origin.txt",
    "financial_technological": "/Users/ben/Documents/bruegel/data_new/WORKING/INDUSTRY/tuone_v6/llmProcess/prompts/financial-technological.txt",
    "capacities": "/Users/ben/Documents/bruegel/data_new/WORKING/INDUSTRY/tuone_v6/llmProcess/prompts/capacities.txt",
    "investments": "/Users/ben/Documents/bruegel/data_new/WORKING/INDUSTRY/tuone_v6/llmProcess/prompts/investments.txt"
}