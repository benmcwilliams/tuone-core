# Default output unit mapping per (product_lv1, product_lv2)
# If an exact (lv1, lv2) key is not found, code will try (lv1, None).
# Allowed target units currently: "gigawatt hour", "gigawatt", "tonne", "vehicle".
DEFAULT_UNIT_MAP = {
    #batteries
    ("battery", "recycling"): "tonne",
    ("battery", "eam"): "tonne",
    ("battery", "cell"): "gigawatt hour",
    ("battery", "module_pack"): "gigawatt hour",
    #solar
    ("solar", "polysilicon"): "tonne",
    ("solar", "ingot_wafer"): "gigawatt",
    ("solar", "cell"): "gigawatt",
    ("solar", "module"): "gigawatt",
    ("solar", "deployment"): "megawatt",
    #vehicle
    ("vehicle", "electric"): "vehicle",
    ("vehicle", "fossil"): "vehicle",
    #wind
    ("wind", "deployment"): "megawatt",
    #nuclear
    ("nuclear", "deployment"): "megawatt",
    #hydro
    ("hydroelectric", "deployment"): "megawatt",
    #iron
    ("iron", "DRI"): "tonne",
    ("iron", "natural gas DRI"): "tonne",
    ("iron", "hydrogen DRI"): "tonne",
}



PRODUCT_CONVERSIONS = {
    # EAM: tonnes → GWh
    ("battery", "eam"): {
        "from": "tonne",
        "to":   "gigawatt hour",
        "multiplier": 1e-3,
    },

    # module/pack systems: units → GWh (assume 50 kWh/pack)
    ("battery", "module_pack"): {
        "from": ["unit", "battery packs", "battery systems", "battery modules", "batteries", "battery"],
        "to": "gigawatt hour",
        "multiplier": 50e-6,
    },

    #  generic battery catch-all when lv2 is missing (None)
    ("battery", None): {
        "from": ["batteries"],
        "to": "gigawatt hour",
        "multiplier": 50e-6,  # 50 kWh per unit → 0.00005 GWh
    },
}

# define overrides as a mapping of (product_lv1, product_lv2, metric) → multiplier
MULTIPLIER_OVERRIDE_MAP = {
    # For 1 tonne EAM = 1 kWh → GWh
    ("battery", "eam", "tonne"): 1 / 1e3,  # 1 kWh per kg → 1 MWh per tonne → 0.001 GWh

    # For EV/cars implied capacity
    ("battery", None, None): 50 / 1e6,     # 50 kWh per car → 0.00005 GWh

}

KEYWORD_MULTIPLIER_MAP = {
    ("ev", "car", "vehicle", "electric vehicle", "electric car", "vehicle electric", "evs", "bevs", "phevs", "phev"): 50 / 1e6,
    ("van","vans"): 80 / 1e6,
    ("truck", "electric truck", "trucks", "fret truck", "fret trucks", "electric heavy-duty vehicles", "heavy-duty vehicles", "heavy-duty"): 300 / 1e6,
    ("bus", "electric bus", "buses", "electric buses"): 350 / 1e6,
}
