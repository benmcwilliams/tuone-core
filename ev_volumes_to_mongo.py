from mongo_client import facilities_collection

# read list of facilities from facilities_develop 
# filter product_lv1 == vehicle; product_lv2 contains "electric"
# for identifiers, use
    # inst_canon (company name)
    # iso2
    # admin_group_key


# inside the events array, each event has a products array. 
# Flatten this absolutely & return list of products at facility. 
    # (VW ID2, VW ID3)


# read in the EV Volumes 

# { jan-17: {VW ID2: 100, VWID3: 10}, feb-17: {VW ID2: 110, VWID3: 20} 
# 
#   }


# (fuzzy) match

# match on iso2 and inst_canon
    # if only one match, simply write
    # if multiple matches, explore using product/model names

