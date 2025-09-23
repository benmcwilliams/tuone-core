from src.inputs import EUROPEAN_COUNTRIES

# 1. first factory registry
FACTORY_REGISTRY_DIRECT = {
    "nodes": {
        "factory": {
            "label": "factory",
            "keep": [
                "name",
                "unique_id",
                "location_city",
                "location_country",
                "status",
                "article_id",
            ],
            "rename": {
                "unique_id": "factory_id",
                "name": "factory",
                "status": "factory_status",
            },
            "enrich": "factory_geo",  # enriches with adm1, adm2, bbox, lat, lon etc
        },
        "owner": {
            "label": ["company", "joint_venture"],
            "keep": ["unique_id", "name_canon", "label"],
            "rename": {
                "unique_id": "owner_id",
                "name_canon": "inst_canon",
                "label": "inst_type",
            },
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
            "rename": {"source": "owner_id", "target": "factory_id"},
        },
        {
            "alias": "produced_at",
            "type": "produced_at",
            "source_label": "product",
            "target_label": "factory",
            "rename": {"source": "product_id", "target": "factory_id"},
        },
    ],
    # Join: (left_alias, key_left, right_alias, key_right, how)
    # 1. returns (starts with) the *OWNS* relationship, joins product IDs using the *PRODUCED_AT* relationship
    # 2. decorate owners
    # 3. decorate factories
    # 4. decorate products
    "join_chain": [
        ("owns", "factory_id", "produced_at", "factory_id", "inner"),
        ("owns", "owner_id", "owner", "owner_id", "inner"),
        ("owns", "factory_id", "factory", "factory_id", "inner"),
        ("owns", "product_id", "product", "product_id", "inner"),
    ],
    "filters": [lambda df: df[df["iso2"].isin(EUROPEAN_COUNTRIES)]],
    "column_order": [
        "factory",
        "inst_canon",
        "inst_type",
        "city_key",
        "iso2",
        "adm1",
        "adm2",
        "adm3",
        "adm4",
        "lat",
        "lon",
        "factory_status",
        "product",
        "product_lv1",
        "product_lv2",
        "article_id",
        # output product_id | owner_id | factory_id to identify them globally
    ],
}

# 2. indirect factory registry via capacities
FACTORY_REGISTRY_CAP = {
    "nodes": {
        "factory": {
            "label": "factory",
            "keep": [
                "name",
                "unique_id",
                "location_city",
                "location_country",
                "status",
                "article_id",
            ],
            "rename": {
                "unique_id": "factory_id",
                "name": "factory",
                "status": "factory_status",
            },
            "enrich": "factory_geo",
        },
        "owner": {
            "label": ["company", "joint_venture"],
            "keep": ["unique_id", "name_canon", "label"],
            "rename": {
                "unique_id": "owner_id",
                "name_canon": "inst_canon",
                "label": "inst_type",
            },
        },
        "product": {
            "label": "product",
            "keep": ["name", "unique_id", "product_lv1", "product_lv2"],
            "rename": {"unique_id": "product_id", "name": "product"},
        },
        "capacity": {
            "label": "capacity",
            "keep": ["unique_id"],
            "rename": {"unique_id": "capacity_id"},
        },
    },
    "edges": [
        {
            "alias": "owns",
            "type": "owns",
            "source_label": ["company", "joint_venture"],
            "target_label": "factory",
            "rename": {"source": "owner_id", "target": "factory_id"},
        },
        {
            "alias": "at",
            "type": "at",
            "source_label": "capacity",
            "target_label": "factory",
            "rename": {"source": "capacity_id", "target": "factory_id"},
        },
        {
            "alias": "quant",
            "type": "quantifies",
            "source_label": "capacity",
            "target_label": "product",
            "rename": {"source": "capacity_id", "target": "product_id"},
        },
    ],
    "join_chain": [
        ("owns", "factory_id", "at", "factory_id", "inner"),
        ("owns", "capacity_id", "quant", "capacity_id", "inner"),
        ("owns", "owner_id", "owner", "owner_id", "inner"),
        ("owns", "factory_id", "factory", "factory_id", "inner"),
        ("owns", "product_id", "product", "product_id", "inner"),
    ],
    "filters": [lambda df: df[df["iso2"].isin(EUROPEAN_COUNTRIES)]],
    "column_order": [
        "article_id",
        "factory",
        "inst_canon",
        "inst_type",
        "product",
        "product_lv1",
        "product_lv2",
        "city_key",
        "iso2",
        "adm1",
        "adm2",
        "adm3",
        "adm4",
        "lat",
        "lon",
        "factory_status",
    ],
}

# 3. indirect factory registry via investments
FACTORY_REGISTRY_INV = {
    "nodes": {
        "factory": {
            "label": "factory",
            "keep": [
                "name",
                "unique_id",
                "location_city",
                "location_country",
                "status",
                "article_id",
            ],
            "rename": {
                "unique_id": "factory_id",
                "name": "factory",
                "status": "factory_status",
            },
            "enrich": "factory_geo",
        },
        "owner": {
            "label": ["company", "joint_venture"],
            "keep": ["unique_id", "name_canon", "label"],
            "rename": {
                "unique_id": "owner_id",
                "name_canon": "inst_canon",
                "label": "inst_type",
            },
        },
        "product": {
            "label": "product",
            "keep": ["name", "unique_id", "product_lv1", "product_lv2"],
            "rename": {"unique_id": "product_id", "name": "product"},
        },
        "investment": {
            "label": "investment",
            "keep": ["unique_id"],
            "rename": {"unique_id": "investment_id"},
        },
    },
    "edges": [
        {
            "alias": "owns",
            "type": "owns",
            "source_label": ["company", "joint_venture"],
            "target_label": "factory",
            "rename": {"source": "owner_id", "target": "factory_id"},
        },
        {
            "alias": "funds",
            "type": "funds",
            "source_label": "investment",
            "target_label": "factory",
            "rename": {"source": "investment_id", "target": "factory_id"},
        },
        {
            "alias": "targets",
            "type": "targets",
            "source_label": "investment",
            "target_label": "product",
            "rename": {"source": "investment_id", "target": "product_id"},
        },
    ],
    "join_chain": [
        ("owns", "factory_id", "funds", "factory_id", "inner"),
        ("owns", "investment_id", "targets", "investment_id", "inner"),
        ("owns", "owner_id", "owner", "owner_id", "inner"),
        ("owns", "factory_id", "factory", "factory_id", "inner"),
        ("owns", "product_id", "product", "product_id", "inner"),
    ],
    "filters": [lambda df: df[df["iso2"].isin(EUROPEAN_COUNTRIES)]],
    "column_order": [
        "article_id",
        "factory",
        "inst_canon",
        "inst_type",
        "product",
        "product_lv1",
        "product_lv2",
        "city_key",
        "iso2",
        "adm1",
        "adm2",
        "adm3",
        "adm4",
        "lat",
        "lon",
        "factory_status",
    ],
}

FACTORY_TECH_SPEC = {
    "nodes": {
        "factory": {
            "label": "factory",
            "keep": [
                "name",
                "unique_id",
                "location_city",
                "location_country",
                "status",
                "article_id",
            ],
            "rename": {
                "unique_id": "factory_id",
                "name": "factory",
                "status": "factory_status",
            },
            "enrich": "factory_geo",  # pluggable enricher
        },
        "capacity": {
            "label": "capacity",
            "keep": ["amount", "unique_id", "status", "phase", "additional"],
            "rename": {"unique_id": "capacity_id", "amount": "capacity"},
        },
        "investment": {
            "label": "investment",
            "keep": ["amount", "unique_id", "status", "phase", "is_total"],
            "rename": {
                "unique_id": "investment_id",
                "amount": "investment",
                "status": "investment_status",
                "phase": "investment_phase",
            },
        },
        "product": {
            "label": "product",
            "keep": ["name", "unique_id", "product_lv1", "product_lv2"],
            "rename": {"unique_id": "product_id", "name": "product"},
        },
        "owner": {
            "label": ["company", "joint_venture"],
            "keep": ["name", "unique_id", "name_canon", "label"],
            "rename": {
                "unique_id": "owner_id",
                "name": "institution",
                "name_canon": "inst_canon",
                "label": "inst_type",
            },
        },
    },
    "edges": [
        {
            "alias": "quant",
            "type": "quantifies",
            "source_label": "capacity",
            "target_label": "product",
            "rename": {"source": "capacity_id", "target": "product_id"},
        },
        {
            "alias": "at",
            "type": "at",
            "source_label": "capacity",
            "target_label": "factory",
            "rename": {"source": "capacity_id", "target": "factory_id"},
        },
        {
            "alias": "owns",
            "type": "owns",
            "source_label": ["company", "joint_venture"],
            "target_label": "factory",
            "rename": {"source": "owner_id", "target": "factory_id"},
        },
        {
            "alias": "enables",
            "type": "enables",
            "source_label": "investment",
            "target_label": "capacity",
            "rename": {"source": "investment_id", "target": "capacity_id"},
        },
    ],
    # Join: (left_alias, key_left, right_alias, key_right, how)
    # 1. returns the QUANTIFY relationship, and merges with the AT relationship (we keep quant as the df name)
    # 2. merges any investments which ENABLE the capacity
    # 3. returns the above and merges with the OWNS relationship
    # 4. decorates the factory node
    # 5. decorates the capacity node
    # 6. decorates the product node
    # 7. decorates the owner node
    "join_chain": [
        (
            "quant",
            "capacity_id",
            "at",
            "capacity_id",
            "inner",
        ),  # capacity→product ∩ capacity→factory
        (
            "quant",
            "capacity_id",
            "enables",
            "capacity_id",
            "left",
        ),  # 👈 keep capacity rows; add investment_id if exists
        ("quant", "factory_id", "owns", "factory_id", "inner"),  # add owner
        ("quant", "factory_id", "factory", "factory_id", "inner"),  # enrich factory
        ("quant", "capacity_id", "capacity", "capacity_id", "inner"),  # enrich capacity
        ("quant", "product_id", "product", "product_id", "inner"),  # enrich product
        ("quant", "owner_id", "owner", "owner_id", "inner"),  # enrich owner
        (
            "quant",
            "investment_id",
            "investment",
            "investment_id",
            "left",
        ),  # 👈 decorate investment only where present
    ],
    "filters": [lambda df: df[df["iso2"].isin(EUROPEAN_COUNTRIES)]],
    "column_order": [
        "article_id",
        "institution",
        "inst_canon",
        "inst_type",
        "factory",
        "city_key",
        "iso2",
        "adm1",
        "adm2",
        "adm3",
        "adm4",
        "bbox",
        "lat",
        "lon",
        "capacity",
        "capacity_id",
        "product",
        "product_lv1",
        "product_lv2",
        "investment",
        "investment_status",
        "investment_phase",
        "is_total",
        "phase",
        "status",
        "additional",
        "factory_status",
        "investment_id",
    ],
}

### JOINT VENTURES REGISTRY

COMPANY_FORMS_JV_SPEC = {
    "nodes": {
        "company": {
            "label": "company",
            "keep": ["unique_id", "name_canon"],
            "rename": {
                "unique_id": "company_id",
                "name": "company",
                "name_canon": "company_canon",
            },
        },
        "joint_venture": {
            "label": "joint_venture",
            "keep": ["unique_id", "name_canon"],
            "rename": {
                "unique_id": "jv_id",
                "name": "jv_name",
                "name_canon": "jv_canon",
            },
        },
    },
    "edges": [
        {
            "alias": "forms",
            "type": "forms",
            "source_label": "company",
            "target_label": "joint_venture",
            "rename": {"source": "company_id", "target": "jv_id"},
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

### COMPANY FUNDS FACTORY

INVESTMENT_FUNDS_SPEC = {
    "nodes": {
        "factory": {
            "label": "factory",
            "keep": [
                "name",
                "unique_id",
                "location_city",
                "location_country",
                "status",
                "article_id",
            ],
            "rename": {
                "unique_id": "factory_id",
                "name": "factory",
                "status": "factory_status",
            },
            "enrich": "factory_geo",  # enriches with adm1, adm2, bbox, lat, lon etc
        },
        "owner": {
            "label": ["company", "joint_venture"],
            "keep": ["unique_id", "name_canon", "label"],
            "rename": {
                "unique_id": "owner_id",
                "name_canon": "inst_canon",
                "label": "inst_type",
            },
        },
        "product": {
            "label": "product",
            "keep": ["name", "unique_id", "product_lv1", "product_lv2"],
            "rename": {"unique_id": "product_id", "name": "product"},
        },
        "investment": {
            "label": "investment",
            "keep": ["amount", "unique_id", "status", "phase", "is_total"],
            "rename": {"unique_id": "investment_id", "amount": "investment"},
        },
    },
    "edges": [
        {
            "alias": "owns",
            "type": "owns",
            "source_label": ["company", "joint_venture"],
            "target_label": "factory",
            "rename": {"source": "owner_id", "target": "factory_id"},
        },
        {
            "alias": "targets",
            "type": "targets",
            "source_label": "investment",
            "target_label": "product",
            "rename": {"source": "investment_id", "target": "product_id"},
        },
        {
            "alias": "funds",
            "type": "funds",
            "source_label": "investment",
            "target_label": "factory",
            "rename": {"source": "investment_id", "target": "factory_id"},
        },
    ],
    # Join: (left_alias, key_left, right_alias, key_right, how)
    # 1. starts with the *OWNS* relationship, joins investment IDs using the *FUNDS* relationship
    # 2. attach any products which the investment *TARGETS*
    # 3. decorate owners
    # 4. decorate factories
    # 5. decorate products
    # 6. decorate investments
    "join_chain": [
        ("owns", "factory_id", "funds", "factory_id", "inner"),
        ("owns", "investment_id", "targets", "investment_id", "inner"),
        ("owns", "owner_id", "owner", "owner_id", "inner"),
        ("owns", "factory_id", "factory", "factory_id", "inner"),
        ("owns", "product_id", "product", "product_id", "inner"),
        ("owns", "investment_id", "investment", "investment_id", "inner"),
    ],
    "filters": [lambda df: df[df["iso2"].isin(EUROPEAN_COUNTRIES)]],
    "column_order": [
        "factory",
        "inst_canon",
        "inst_type",
        "city_key",
        "iso2",
        "adm1",
        "adm2",
        "adm3",
        "adm4",
        "lat",
        "lon",
        "investment",
        "status",
        "phase",
        "is_total",
        "factory_status",
        "product",
        "product_lv1",
        "product_lv2",
        "article_id",
        "investment_id",
        # output product_id | owner_id | factory_id to identify them globally
    ],
}
