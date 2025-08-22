from src.inputs import EUROPEAN_COUNTRIES

FACTORY_REGISTRY_SPEC = {
  "nodes": {
    "factory": {
      "label": "factory",
      "keep": ["name", "unique_id", "location_city", "location_country", "status", "article_id"],
      "rename": {"unique_id": "factory_id", "name": "factory", "status": "factory_status"},
      "enrich": "factory_geo"   # enriches with adm1, adm2, bbox, lat, lon etc
    },
    "owner": {
      "label": ["company", "joint_venture"],
      "keep": ["unique_id", "name_canon", "label"],
      "rename": {"unique_id": "owner_id", "name_canon": "inst_canon", "label": "inst_type"},
    },
    "product": {
      "label": "product",
      "keep": ["name", "unique_id", "product_lv1", "product_lv2"],
      "rename": {"unique_id": "product_id", "name": "product"},
    },
  },
  "edges": [
    {
      "alias": "owns",
      "type": "owns",
      "source_label": ["company", "joint_venture"],
      "target_label": "factory",
      "rename": {"source": "owner_id", "target": "factory_id"}
    },
    {
      "alias": "produced_at",
      "type": "produced_at",
      "source_label": "product",
      "target_label": "factory",
      "rename": {"source": "product_id", "target": "factory_id"}
    },
  ],
  # Join: (left_alias, key_left, right_alias, key_right, how)
  # FIRST returns the OWNS relationship, joins product IDs using the *PRODUCED_AT* relationship
  # SECOND decorate owners
  # THIRD decorate factories
  # FOURTH decorate products
  "join_chain": [
    ("owns", "factory_id", "produced_at", "factory_id", "inner"),                    
    ("owns", "owner_id", "owner", "owner_id", "inner"),         
    ("owns", "factory_id", "factory", "factory_id", "inner"),             
    ("owns", "product_id", "product", "product_id", "inner"),             
  ],
  "filters": [
    lambda df: df[df["iso2"].isin(EUROPEAN_COUNTRIES)]
  ],
  "column_order": 
    [
    "factory", "inst_canon", "inst_type", "city_key", "iso2", "adm1", "adm2", "adm3", "adm4", "lat", "lon",
    "factory_status", "product_lv1", "product_lv2", "article_id"
    # output product_id | owner_id | factory_id to identify them globally
  ]
}

FACTORY_TECH_SPEC = {
  "nodes": {
    "factory": {
      "label": "factory",
      "keep": ["name", "unique_id", "location_city", "location_country", "status", "article_id"],
      "rename": {"unique_id": "factory_id", "name": "factory", "status": "factory_status"},
      "enrich": "factory_geo"   # pluggable enricher
    },
    "capacity": {
      "label": "capacity",
      "keep": ["amount", "unique_id", "status", "phase", "additional"],
      "rename": {"unique_id": "capacity_id", "amount": "capacity"},
    },
    "product": {
      "label": "product",
      "keep": ["name", "unique_id", "product_lv1", "product_lv2"],
      "rename": {"unique_id": "product_id", "name": "product"},
    },
    "owner": {
      "label": ["company", "joint_venture"],
      "keep": ["name", "unique_id", "name_canon", "label"],
      "rename": {"unique_id": "owner_id", "name": "institution", "name_canon": "inst_canon", "label": "inst_type"},
    },
  },
  "edges": [
    {
      "alias": "quant",
      "type": "quantifies",
      "source_label": "capacity",
      "target_label": "product",
      "rename": {"source": "capacity_id", "target": "product_id"}
    },
    {
      "alias": "at",
      "type": "at",
      "source_label": "capacity",
      "target_label": "factory",
      "rename": {"source": "capacity_id", "target": "factory_id"}
    },
    {
      "alias": "owns",
      "type": "owns",
      "source_label": ["company", "joint_venture"],
      "target_label": "factory",
      "rename": {"source": "owner_id", "target": "factory_id"}
    }
  ],
  # Join: (left_alias, key_left, right_alias, key_right, how)
  # FIRST returns the QUANTIFY relationship, and merges with the AT relationship (we keep quant as the df name)
  # SECOND returns the above and merges with the OWNS relationship
  # THIRD decorates the factory node
  # FOURTH decorates the capacity node
  # FIFTH decorates the product node
  # SIXTH decorates the owner node
  "join_chain": [
    ("quant", "capacity_id", "at", "capacity_id", "inner"),         # capacity→product ∩ capacity→factory
    ("quant", "factory_id", "owns", "factory_id", "inner"),         # add owner
    ("quant", "factory_id", "factory", "factory_id", "inner"),      # enrich factory
    ("quant", "capacity_id", "capacity", "capacity_id", "inner"),   # enrich capacity
    ("quant", "product_id", "product", "product_id", "inner"),      # enrich product
    ("quant", "owner_id", "owner", "owner_id", "inner"),            # enrich owner
  ],
  "filters": [
    lambda df: df[df["iso2"].isin(EUROPEAN_COUNTRIES)]
  ],
  "column_order": [
    "article_id", "institution", "inst_canon", "inst_type", "factory",
    "city_key", "iso2", "adm1", "adm2", "adm3", "adm4", "bbox", "lat", "lon",
    "capacity", "product", "product_lv1", "product_lv2",
    "phase", "status", "additional", "factory_status"
  ]
}

### JOINT VENTURES REGISTRY

COMPANY_FORMS_JV_SPEC = {
  "nodes": {
    "company": {
      "label": "company",
      "keep": ["unique_id", "name_canon"],
      "rename": {"unique_id": "company_id", "name": "company", "name_canon": "company_canon"}
    },
    "joint_venture": {
      "label": "joint_venture",
      "keep": ["unique_id", "name_canon"],
      "rename": {"unique_id": "jv_id", "name": "jv_name", "name_canon": "jv_canon"}
    }
  },
  "edges": [
    {
      "alias": "forms",
      "type": "forms",
      "source_label": "company",
      "target_label": "joint_venture",
      "rename": {"source": "company_id", "target": "jv_id"}
    }
  ],
  # join chain returns a relationship (whatever you put first)
  # FIRST. Return the *FORMS* relationship. (we keep forms as the df name)
  # SECOND. Decorate the companies with their (names) and name_canon. 
  # THIRD. Decorate the joint ventures with their (names) and name_canon.
  "join_chain": [
    ("forms", "company_id", "company", "company_id", "inner"),
    ("forms", "jv_id", "joint_venture", "jv_id", "inner"),
  ],
  # "filters":        NOT USED
  # "column_order":   NOT USED
}

