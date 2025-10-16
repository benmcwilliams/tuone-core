CAPEX_DICT = {
  "version": "capex_v1",
  "currency": "EUR",
  "notes": "Per-unit CAPEX used for imputation; units are canonicalized upstream.",
  "entries": [
    {
      "product_lv1": "battery",
      "product_lv2_key": ("cell", "module_pack"),   # canonical, sorted tuple
      "capacity_unit": "EUR/GWh",                  # unit basis for the rate
      "capex_per_unit": 80_000_000,                # EUR per GWh/y
      "source": "Rhodium-Bruegel"
    },
    {
      "product_lv1": "battery",
      "product_lv2_key": ("cell",),
      "capacity_unit": "EUR/GWh",
      "capex_per_unit": 80_000_000,  
      "source": "Rhodium-Bruegel"
    },
    {
      "product_lv1": "battery",
      "product_lv2_key": ("module_pack",),
      "capacity_unit": "EUR/GWh",
      "capex_per_unit": 40_000_000,  
      "source": "Rhodium-Bruegel"
    },
    {
      "product_lv1": "vehicle",
      "product_lv2_key": ("electric",),
      "capacity_unit": "EUR/vehicle",
      "capex_per_unit": 5_500,                     # EUR per vehicle/y capacity
      "source": "Rhodium-Bruegel",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("ingot_wafer",),
      "capacity_unit": "EUR/GW",
      "capex_per_unit": 81_000_000,   # midpoint €25–30M/GW
      "source": "Rhodium-Bruegel",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("cell",),
      "capacity_unit": "EUR/GW",
      "capex_per_unit": 134_000_000,   # midpoint €35–45M/GW
      "source": "Rhodium-Bruegel",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("module",),
      "capacity_unit": "EUR/GW",
      "capex_per_unit": 83_000_000,   # midpoint €8–12M/GW
      "source": "Rhodium-Bruegel",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("cell", "module"),
      "capacity_unit": "EUR/GW",
      "capex_per_unit": 134_000_000,   # ~cell + module integrated
      "source": "Rhodium-Bruegel",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("deployment",),
      "capacity_unit": "MW",  
      "capex_per_unit": 900_000,      # EUR per MW
      "source": "ChatGPT",
    },
    {
      "product_lv1": "wind",
      "product_lv2_key": ("deployment",),
      "capacity_unit": "MW",
      "capex_per_unit": 1_500_000,    # EUR per MW
      "source": "ChatGPT",
    },
  ]
}