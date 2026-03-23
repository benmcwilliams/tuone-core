# Default output unit mapping per (product_lv1, product_lv2)
# If an exact (lv1, lv2) key is not found, code will try (lv1, None).
# Allowed target units currently: "gigawatt hour", "gigawatt", "tonne", "vehicle".
DEFAULT_UNIT_MAP = {
    #batteries
    ("battery", "recycling"): "tonne",
    ("battery", "eam"): "gigawatt hour",
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
    # Sum of cathode (~2 kg/kWh), anode (~1 kg/kWh), electrolyte (~0.3 kg/kWh) and copper foil (~0.334 kg/kWh) gives ≈3.6–3.9 kg of material per kWh [oai_citation:0‡thundersaidenergy.com](https://thundersaidenergy.com/downloads/lithium-ion-batteries-energy-density/#:~:text=Today%E2%80%99s%20lithium%20ion%20batteries%20have,file%20here) [oai_citation:1‡americancopper.org](https://www.americancopper.org/assets/docs/ENEREGY%20STORAGE%20idtechex-copper-demand-in-energy-storage.pdf#:~:text=Copper%20Intensity%20at%20Cell%20Level,ion%20cell%20anode%20current%20collector).
    # One tonne (1 000 kg) therefore corresponds to ~250–275 kWh, or ≈0.00026 GWh per tonne.
    ("battery", "eam"): {
        "from": "tonne",
        "to":   "gigawatt hour",
        "multiplier": 2.6e-4,
    },

    # Cathode active material (CAM): tonnes → GWh
    ("battery", "eam", "cathode"): {
        "from": "tonne",
        "to":   "gigawatt hour",
        "multiplier": 5.0e-4,  
    },

    # Anode active material (graphite): tonnes → GWh
    ("battery", "eam", "anode"): {
        "from": "tonne",
        "to":   "gigawatt hour",
        "multiplier": 1.0e-3,  
    },

    # Electrolyte: tonnes → GWh (roughly 1 - 1,500 tonnes electrolyte per GWh)
    ("battery", "eam", "electrolyte"): {
        "from": "tonne",
        "to":   "gigawatt hour",
        "multiplier": 1.5e-3,
    },

    # Copper foil: tonnes → GWh
    ("battery", "eam", "copper_foil"): {
        "from": "tonne",
        "to":   "gigawatt hour",
        "multiplier": 3.0e-3,    #
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
