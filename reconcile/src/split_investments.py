import math 
import pandas as pd

def _as_iter(x):
    return x if isinstance(x, (list, tuple)) else [x]

def _is_missing(x):
    return (
        x is None
        or (isinstance(x, float) and math.isnan(x))
        or (isinstance(x, (pd.Float64Dtype,)) if hasattr(pd, "Float64Dtype") else False)
    )

def multiply_vals(value, mult):
    """
    Multiply a scalar or a list/tuple of numbers by `mult`, preserving shape.
    - If `value` is None/NaN -> return None
    - If `mult` is None/NaN -> treat as 1
    - If any element in a list is None/NaN -> keep it as None
    """
    # whole input missing
    if _is_missing(value):
        return None

    # default multiplier if missing
    if _is_missing(mult):
        mult = 1

    vals = _as_iter(value)
    out = []
    for v in vals:
        if _is_missing(v):
            out.append(None)
        else:
            out.append(v * mult)

    return out if isinstance(value, (list, tuple)) else out[0]

def distribute_vehicle_battery_split(
    df,
    id_col="investment_id",
    lv1_col="product_lv1",
    lv2_col="product_lv2",
    amount_cols=("amount_value", "amount_EUR", "amount_USD"),
    *,
    sample_count=10,   # how many example IDs to show in the log
    verbose=True
):
    """
    Split shared investments across categories for each unique `investment_id`.

    Category rules (case-insensitive), based on presence (ignores other pairs):
      1) {(vehicle, electric), (battery, module_pack)}                  -> 80% / 20%
      2) {(vehicle, electric), (vehicle, fossil)}                       -> 50% / 50%
      3) {(vehicle, electric), (vehicle, fossil), (battery, module_pack)} -> 40% / 40% / 20%

    - If none of the above presence-sets match, no split is applied for that investment_id.
    - If a category appears multiple times within the same investment_id, its
      category weight is split equally across those rows.
    - Preserves list-shaped amounts and None/NaN via `multiply_vals`.
    - Adds:
        * split_investment: bool
        * split_rule: one of {"veh_vs_bat_80_20","veh_e_vs_veh_f_50_50","three_way_40_40_20"} for affected rows
    """

    VEH_E = ("vehicle", "electric")
    VEH_F = ("vehicle", "fossil")
    BAT_M = ("battery", "module_pack")

    out = df.copy()

    if "split_investment" not in out.columns:
        out["split_investment"] = False
    if "split_rule" not in out.columns:
        out["split_rule"] = pd.Series(index=out.index, dtype="object")

    affected_ids = []
    samples = []  # [{inv_id, rows:[{idx, lv1, lv2, eur_before, usd_before}]}]

    # group by investment
    for inv_id, g in out.groupby(id_col, sort=False):
        # Canonicalize category pairs (lowercase, str-cast handles NaN -> 'nan')
        pairs = set(zip(g[lv1_col].astype(str).str.lower(),
                        g[lv2_col].astype(str).str.lower()))

        # Consider only canonical categories (ignore ('vehicle',''), ('vehicle','nan'), etc.)
        present = set()
        if VEH_E in pairs: present.add(VEH_E)
        if VEH_F in pairs: present.add(VEH_F)
        if BAT_M in pairs: present.add(BAT_M)

        # Decide weights based on presence (not exact equality on all pairs)
        weights = None
        split_rule = None
        if present == {VEH_E, BAT_M}:
            weights = {VEH_E: 0.80, BAT_M: 0.20}
            split_rule = "veh_vs_bat_80_20"
        elif present == {VEH_E, VEH_F}:
            weights = {VEH_E: 0.50, VEH_F: 0.50}
            split_rule = "veh_e_vs_veh_f_50_50"
        elif present == {VEH_E, VEH_F, BAT_M}:
            weights = {VEH_E: 0.40, VEH_F: 0.40, BAT_M: 0.20}
            split_rule = "three_way_40_40_20"
        else:
            # No split for this group
            continue

        affected_ids.append(inv_id)

        # Capture BEFORE snapshot for examples
        if len(samples) < sample_count:
            rows_before = []
            for i, row in g.iterrows():
                rows_before.append({
                    "idx": i,
                    "lv1": row[lv1_col],
                    "lv2": row[lv2_col],
                    "eur_before": row.get("amount_EUR"),
                    "usd_before": row.get("amount_USD"),
                })
            samples.append({"inv_id": inv_id, "rows": rows_before})

        # Build per-category index lists
        idxs_by_cat = {}
        for cat in weights.keys():
            idxs = g[(g[lv1_col].str.lower() == cat[0]) &
                     (g[lv2_col].str.lower() == cat[1])].index
            idxs_by_cat[cat] = idxs

        # Compute per-row scaling factors (category weight split equally across its rows)
        factors_by_idx = {}
        for cat, cat_weight in weights.items():
            idxs = idxs_by_cat.get(cat, [])
            if len(idxs) == 0:
                continue
            per_row = cat_weight / len(idxs)
            for idx in idxs:
                factors_by_idx[idx] = per_row

        # Apply factors column-wise using multiply_vals
        for idx, factor in factors_by_idx.items():
            for col in amount_cols:
                out.at[idx, col] = multiply_vals(out.at[idx, col], factor)

        # Mark flags
        affected_mask = g.index.isin(list(factors_by_idx.keys()))
        affected_idxs = g.index[affected_mask]
        out.loc[affected_idxs, "split_investment"] = True
        out.loc[affected_idxs, "split_rule"] = split_rule

    # ----- Logging -----
    if verbose:
        rows_changed = int(out["split_investment"].sum())
        print("---- Vehicle/Battery split (extended) ----")
        print(f"Affected investment_ids: {len(affected_ids)}")
        print(f"Rows updated: {rows_changed}")

        for s in samples:
            inv_id = s["inv_id"]

            # Optional: include company name in header if present
            try:
                company_name = (
                    out.loc[out[id_col] == inv_id, "company"].iloc[0]
                    if "company" in out.columns
                    else None
                )
            except Exception:
                company_name = None

            header = f"\nExample investment_id: {inv_id}"
            if company_name:
                header += f"  |  company: {company_name}"
            print(header)

            for r in s["rows"]:
                idx = r["idx"]
                eur_after = out.at[idx, "amount_EUR"] if "amount_EUR" in out.columns else None
                usd_after = out.at[idx, "amount_USD"] if "amount_USD" in out.columns else None
                rule = out.at[idx, "split_rule"] if "split_rule" in out.columns else None
                print(
                    f"  [{idx}] {r['lv1']}/{r['lv2']}: "
                    f"EUR {r['eur_before']} → {eur_after} | "
                    f"USD {r['usd_before']} → {usd_after} "
                    f"| rule={rule}"
                )

    return out