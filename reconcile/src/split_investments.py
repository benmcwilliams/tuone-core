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
    sample_count=2,   # how many example IDs to show in the log
    verbose=True):
    """
    If a unique investment_id appears in both:
      - (vehicle, electric)
      - (battery, module_pack)
    then overwrite amounts:
      - 80% for vehicle/electric rows
      - 20% for battery/module_pack rows
    Adds boolean column 'split_investment' = True for affected rows.
    Prints a concise log (can disable via verbose=False).
    """

    VEH = ("vehicle", "electric")
    BAT = ("battery", "module_pack")

    out = df.copy()
    out["split_investment"] = False

    affected_ids = []
    # For logging: capture a lightweight "before" snapshot for up to `sample_count` IDs
    samples = []  # [{inv_id, rows:[{idx, lv1, lv2, eur_before, usd_before}]}]

    for inv_id, g in out.groupby(id_col, sort=False):
        pairs = set(zip(g[lv1_col].astype(str).str.lower(), g[lv2_col].astype(str).str.lower()))
        if pairs == {VEH, BAT}:
            affected_ids.append(inv_id)

            # Collect BEFORE snapshot for examples (from the original data, not yet scaled)
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

            mask_veh = (g[lv1_col].str.lower() == VEH[0]) & (g[lv2_col].str.lower() == VEH[1])
            mask_bat = (g[lv1_col].str.lower() == BAT[0]) & (g[lv2_col].str.lower() == BAT[1])

            # Apply scaling
            for col in amount_cols:
                out.loc[g.index[mask_veh], col] = out.loc[g.index[mask_veh], col].apply(lambda v: multiply_vals(v, 0.80))
                out.loc[g.index[mask_bat], col] = out.loc[g.index[mask_bat], col].apply(lambda v: multiply_vals(v, 0.20))

            out.loc[g.index, "split_investment"] = True

    # ----- Logging -----
    if verbose:
        rows_changed = int(out["split_investment"].sum())
        print("---- Vehicle/Battery split ----")
        print(f"Affected investment_ids: {len(affected_ids)}")
        print(f"Rows updated: {rows_changed}")

        # Fill AFTER values for samples and print them
        for s in samples:
            inv_id = s["inv_id"]
            print(f"\nExample investment_id: {inv_id}")
            for r in s["rows"]:
                idx = r["idx"]
                eur_after = out.at[idx, "amount_EUR"] if "amount_EUR" in out.columns else None
                usd_after = out.at[idx, "amount_USD"] if "amount_USD" in out.columns else None
                print(
                    f"  [{idx}] {r['lv1']}/{r['lv2']}: "
                    f"EUR {r['eur_before']} → {eur_after} | "
                    f"USD {r['usd_before']} → {usd_after}"
                )

    return out