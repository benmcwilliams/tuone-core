CAPEX_DICT = {
  "version": "capex_v1",
  "currency": "EUR",
  "notes": "Per-unit CAPEX used for imputation; units are canonicalized upstream.",
  "entries": [
    {
      "product_lv1": "battery",
      "product_lv2_key": ("cell", "module_pack"),   # canonical, sorted tuple
      "capacity_unit": "GWh/year",                  # unit basis for the rate
      "capex_per_unit": 100_000_000,                # EUR per GWh/y
      "source": "Ben estimate"
    },
    {
      "product_lv1": "battery",
      "product_lv2_key": ("cell"),
      "capacity_unit": "GWh/year",
      "capex_per_unit": 90_000_000,  
      "source": "Ben estimate"
    },
    {
      "product_lv1": "battery",
      "product_lv2_key": ("module_pack"),
      "capacity_unit": "GWh/year",
      "capex_per_unit": 25_000_000,  
      "source": "Ben estimate"
    },
    {
      "product_lv1": "vehicle",
      "product_lv2_key": ("electric"),
      "capacity_unit": "vehicles/year",
      "capex_per_unit": 12_000,                     # EUR per vehicle/y capacity
      "source": "Ben estimate",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("ingot_wafer",),
      "capacity_unit": "GW/year",
      "capex_per_unit": 27_500_000,   # midpoint €25–30M/GW
      "source": "Industry benchmarks 2023–2025 (China/EU/US)",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("cell",),
      "capacity_unit": "GW/year",
      "capex_per_unit": 40_000_000,   # midpoint €35–45M/GW
      "source": "Industry benchmarks 2023–2025 (China/EU/US)",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("module",),
      "capacity_unit": "GW/year",
      "capex_per_unit": 10_000_000,   # midpoint €8–12M/GW
      "source": "Industry benchmarks 2023–2025 (China/EU/US)",
    },
    {
      "product_lv1": "solar",
      "product_lv2_key": ("cell", "module"),
      "capacity_unit": "GW/year",
      "capex_per_unit": 47_500_000,   # ~cell + module integrated
      "source": "Industry benchmarks 2023–2025 (China/EU/US)",
    }
  ]
}