CAPEX_DICT = {
  "version": "capex_v1",
  "currency": "EUR",
  "notes": "Per-unit CAPEX used for imputation; units are canonicalized upstream.",
  "entries": [
    {
      "product_lv1": "battery",
      "product_lv2_key": ("cell", "module_pack"),   # canonical, sorted tuple
      "capacity_unit": "GWh/year",               # unit basis for the rate
      "capex_per_unit": 70_000_000,              # EUR per GWh/y
      "source": "Bruegel internal v2025-07"
    },
    {
      "product_lv1": "battery",
      "product_lv2_key": ("cell"),
      "capacity_unit": "GWh/year",
      "capex_per_unit": 90_000_000,  # combined line estimate
      "source": "Engineering estimate"
    },
    {
      "product_lv1": "vehicle",
      "product_lv2_key": ("electric"),
      "capacity_unit": "vehicles/year",
      "capex_per_unit": 12_000,    # EUR per vehicle/y capacity
      "source": "OEM benchmarking 2024",
    }
  ]
}