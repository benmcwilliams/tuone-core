from src.inputs import EUROPEAN_COUNTRIES

FACTORY_TECH_SPEC = {
  "nodes": {
    "factory": {
      "label": "factory",
      "keep": ["name", "unique_id", "location_city", "location_country", "article_id"],
      "rename": {"unique_id": "factory_id", "name": "factory"},
      "enrich": "factory_geo"   # pluggable enricher
    },
    "capacity": {
      "label": "capacity",
      "keep": ["amount", "unique_id", "status", "phase"],
      "rename": {"unique_id": "capacity_id", "amount": "capacity"},
    },
    "product": {
      "label": "product",
      "keep": ["name", "unique_id", "product_lv1", "product_lv2"],
      "rename": {"unique_id": "product_id", "name": "product"},
    },
    "owner": {
      "label": ["company", "joint_venture"],
      "keep": ["name", "unique_id", "name_canon"],
      "rename": {"unique_id": "owner_id", "name": "institution", "name_canon": "inst_canon"},
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
  "dedupe": (["factory_id"], "first"),   # mirrors your comment about never having dup owners
  "column_order": [
    "article_id", "institution", "inst_canon", "factory",
    "city_key", "iso2", "adm1", "adm2", "bbox", "lat", "lon",
    "capacity", "product", "product_lv1", "product_lv2",
    "phase", "status"
  ]
}