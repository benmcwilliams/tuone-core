import sys
from pathlib import Path

import logging
from typing import Any

import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

from mongo_client import articles_collection
from src.flatten_helpers import flatten_dict
from src.logger import setup_logger
from normalise_government_amounts import normalise_government_amounts


GOV_ARTICLE_QUERY = {
    "nodes": {"$exists": True},
    "relationships": {"$exists": True},
    "meta.tag": "government",
}

GOV_ARTICLE_PROJECTION = {
    "_id": 1,
    "nodes": 1,
    "relationships": 1,
    "meta.tag": 1,
    "meta.date": 1,
}

OUTPUT_DIR = Path(__file__).resolve().parent / "storage" / "output" / "government"
OUTPUT_CSV = OUTPUT_DIR / "government_policy_long.csv"
OUTPUT_XLSX = OUTPUT_DIR / "government_policy_long.xlsx"
OUTPUT_CLEAN_CSV = OUTPUT_DIR / "government_policy_long_clean.csv"
OUTPUT_CLEAN_XLSX = OUTPUT_DIR / "government_policy_long_clean.xlsx"
ARTICLE_BASE_URL = "https://tuone.bruegel.org/articles/government/"


def flatten_government_articles() -> tuple[pd.DataFrame, pd.DataFrame]:
    docs = list(articles_collection.find(GOV_ARTICLE_QUERY, GOV_ARTICLE_PROJECTION).sort("_id", 1))
    logging.info("Loaded %d government-tagged articles.", len(docs))

    all_nodes: list[dict[str, Any]] = []
    all_rels: list[dict[str, Any]] = []

    for doc in docs:
        article_id = str(doc.get("_id"))
        article_date = doc.get("meta", {}).get("date")

        for node in doc.get("nodes", []):
            node_id = node.get("id")
            node_type = node.get("type")
            if not node_id or not node_type:
                continue
            raw_props = {k: v for k, v in node.items() if k not in ["id", "type"]}
            flat_props = flatten_dict(raw_props)
            flat_props.update(
                {
                    "article_id": article_id,
                    "article_date": article_date,
                    "id": node_id,
                    "label": str(node_type).lower(),
                }
            )
            all_nodes.append(flat_props)

        for rel_idx, rel in enumerate(doc.get("relationships", [])):
            source = rel.get("source")
            target = rel.get("target")
            rel_type = rel.get("type")
            if not source or not target or not rel_type:
                continue
            raw_props = {k: v for k, v in rel.items() if k not in ["source", "target", "type", "group"]}
            flat_props = flatten_dict(raw_props)
            flat_props.update(
                {
                    "article_id": article_id,
                    "article_date": article_date,
                    "source": source,
                    "target": target,
                    "type": str(rel_type).lower(),
                    "group": rel.get("group", "unspecified"),
                    "rel_row_id": f"{article_id}:rel:{rel_idx}",
                }
            )
            all_rels.append(flat_props)

    nodes = pd.DataFrame(all_nodes)
    rels = pd.DataFrame(all_rels)

    if nodes.empty:
        logging.warning("No nodes found for government-tagged articles.")
        return nodes, rels

    nodes["unique_id"] = nodes["article_id"] + "_" + nodes["id"]

    if rels.empty:
        logging.warning("No relationships found for government-tagged articles.")
        return nodes, rels

    lookup = nodes[["article_id", "id", "unique_id", "label"]].copy()

    src_lookup = lookup.rename(
        columns={
            "id": "src_node_id",
            "unique_id": "source_unique_id",
            "label": "source_label",
        }
    )
    rels = rels.merge(
        src_lookup,
        left_on=["article_id", "source"],
        right_on=["article_id", "src_node_id"],
        how="left",
    ).drop(columns=["src_node_id"], errors="ignore")

    tgt_lookup = lookup.rename(
        columns={
            "id": "tgt_node_id",
            "unique_id": "target_unique_id",
            "label": "target_label",
        }
    )
    rels = rels.merge(
        tgt_lookup,
        left_on=["article_id", "target"],
        right_on=["article_id", "tgt_node_id"],
        how="left",
    ).drop(columns=["tgt_node_id"], errors="ignore")

    rels["source"] = rels["source_unique_id"]
    rels["target"] = rels["target_unique_id"]
    rels = rels.drop(columns=["source_unique_id", "target_unique_id"], errors="ignore")

    return nodes, rels


def build_government_option_b_long(nodes: pd.DataFrame, rels: pd.DataFrame) -> pd.DataFrame:
    if nodes.empty or rels.empty:
        return pd.DataFrame()

    governments = (
        nodes[nodes["label"] == "government"][["article_id", "unique_id", "name"]]
        .rename(columns={"unique_id": "government_id", "name": "government_name"})
        .copy()
    )
    governments["government_name"] = governments["government_name"].fillna(governments["government_id"])

    products = (
        nodes[nodes["label"] == "product"][["article_id", "unique_id", "name"]]
        .rename(columns={"unique_id": "product_id", "name": "product_name"})
        .copy()
    )

    measures = (
        nodes[nodes["label"].isin(["support_package", "tax_cut"])][
            ["article_id", "unique_id", "label", "name", "status", "amount"]
        ]
        .rename(
            columns={
                "unique_id": "measure_id",
                "label": "measure_type",
                "name": "measure_name",
                "status": "measure_status",
                "amount": "measure_amount_raw",
            }
        )
        .copy()
    )
    measures["measure_name"] = measures["measure_name"].fillna(measures["measure_id"])
    measures["measure_status"] = measures["measure_status"].fillna("unclear")

    tax_measures = measures[measures["measure_type"] == "tax_cut"][
        ["article_id", "measure_id", "measure_name", "measure_status", "measure_amount_raw"]
    ].rename(
        columns={
            "measure_id": "included_tax_id",
            "measure_name": "included_tax_name",
            "measure_status": "included_tax_status",
            "measure_amount_raw": "included_tax_amount_raw",
        }
    )

    issues = rels[
        (rels["type"] == "issues")
        & (rels["source_label"] == "government")
        & (rels["target_label"].isin(["support_package", "tax_cut"]))
    ][["article_id", "article_date", "rel_row_id", "source", "target"]].rename(
        columns={
            "rel_row_id": "issues_rel_id",
            "source": "government_id",
            "target": "issued_measure_id",
        }
    )

    targets = rels[
        (rels["type"] == "targets")
        & (rels["source_label"].isin(["support_package", "tax_cut"]))
        & (rels["target_label"] == "product")
    ][["article_id", "rel_row_id", "source", "target"]].rename(
        columns={
            "rel_row_id": "targets_rel_id",
            "source": "targeting_measure_id",
            "target": "product_id",
        }
    )

    includes = rels[
        (rels["type"] == "includes")
        & (rels["source_label"] == "support_package")
        & (rels["target_label"] == "tax_cut")
    ][["article_id", "rel_row_id", "source", "target"]].rename(
        columns={
            "rel_row_id": "includes_rel_id",
            "source": "support_package_id",
            "target": "included_tax_id",
        }
    )

    base = issues.merge(governments, on=["article_id", "government_id"], how="left")
    base = base.merge(
        measures.add_prefix("issued_").rename(columns={"issued_article_id": "article_id"}),
        on=["article_id", "issued_measure_id"],
        how="left",
    )

    direct_targets = (
        base.merge(
            targets,
            left_on=["article_id", "issued_measure_id"],
            right_on=["article_id", "targeting_measure_id"],
            how="inner",
        )
        .merge(products, on=["article_id", "product_id"], how="left")
        .copy()
    )
    direct_targets["target_path"] = "direct_measure_target"
    direct_targets["target_hops"] = 1
    direct_targets["parent_support_package_id"] = None
    direct_targets["included_tax_id"] = None
    direct_targets["included_tax_name"] = None
    direct_targets["included_tax_status"] = None
    direct_targets["included_tax_amount_raw"] = None

    pkg_issues = base[base["issued_measure_type"] == "support_package"].copy()
    nested_targets = pkg_issues.merge(
        includes,
        left_on=["article_id", "issued_measure_id"],
        right_on=["article_id", "support_package_id"],
        how="inner",
    )
    nested_targets = nested_targets.merge(
        targets,
        left_on=["article_id", "included_tax_id"],
        right_on=["article_id", "targeting_measure_id"],
        how="inner",
    )
    nested_targets = nested_targets.merge(
        tax_measures,
        on=["article_id", "included_tax_id"],
        how="left",
    )
    nested_targets = nested_targets.merge(products, on=["article_id", "product_id"], how="left")
    nested_targets["target_path"] = "included_tax_target"
    nested_targets["target_hops"] = 2
    nested_targets["parent_support_package_id"] = nested_targets["issued_measure_id"]

    decorated = pd.concat([direct_targets, nested_targets], ignore_index=True, sort=False)

    decorated_issue_keys = decorated[["article_id", "issues_rel_id"]].drop_duplicates()
    undecorated = base.merge(decorated_issue_keys, on=["article_id", "issues_rel_id"], how="left", indicator=True)
    undecorated = undecorated[undecorated["_merge"] == "left_only"].copy()
    undecorated["product_id"] = None
    undecorated["product_name"] = None
    undecorated["targeting_measure_id"] = None
    undecorated["target_path"] = "no_product_link"
    undecorated["target_hops"] = 0
    undecorated["parent_support_package_id"] = None
    undecorated["included_tax_id"] = None
    undecorated["included_tax_name"] = None
    undecorated["included_tax_status"] = None
    undecorated["included_tax_amount_raw"] = None
    undecorated["includes_rel_id"] = None
    undecorated["targets_rel_id"] = None

    combined = pd.concat([decorated, undecorated], ignore_index=True, sort=False)

    out = combined[
        [
            #"government_id",
            "government_name",
            #"issued_measure_id",
            "issued_measure_type",
            "issued_measure_name",
            "issued_measure_status",
            "issued_measure_amount_raw",
            #"targeting_measure_id",
            #"parent_support_package_id",
            #"included_tax_id",
            "included_tax_name",
            "included_tax_status",
            "included_tax_amount_raw",
            #"product_id",
            "product_name",
            "target_path",
            "target_hops",
            #"issues_rel_id",
            #"includes_rel_id",
            #"targets_rel_id",
            "article_date",
            "article_id",
        ]
    ].copy()

    # Keep all rows; only remove exact duplicate lineages from repeated KG edges.
    out = out.drop_duplicates()
    out = out.rename(columns={"article_date": "date"})
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m")
    out["article_id"] = out["article_id"].astype(str)
    out["article_id"] = out["article_id"].apply(
        lambda aid: f'=HYPERLINK("{ARTICLE_BASE_URL}{aid}", "{aid}")'
    )
    out = out.sort_values(by=["government_name"], ascending=True, na_position="last").reset_index(drop=True)
    return out


def main(write_excel: bool = True, normalise_amounts: bool = True) -> pd.DataFrame:
    setup_logger()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    nodes, rels = flatten_government_articles()
    df_long = build_government_option_b_long(nodes, rels)

    df_long.to_csv(OUTPUT_CSV, index=False)
    logging.info("Wrote government long table CSV: %s", OUTPUT_CSV)

    if write_excel:
        df_long.to_excel(OUTPUT_XLSX, index=False)
        logging.info("Wrote government long table Excel: %s", OUTPUT_XLSX)

    if normalise_amounts:
        df_clean = normalise_government_amounts(df_long)
        df_clean.to_csv(OUTPUT_CLEAN_CSV, index=False)
        logging.info("Wrote government clean table CSV: %s", OUTPUT_CLEAN_CSV)
        if write_excel:
            df_clean.to_excel(OUTPUT_CLEAN_XLSX, index=False)
            logging.info("Wrote government clean table Excel: %s", OUTPUT_CLEAN_XLSX)
        logging.info("Rows: raw=%d | clean=%d", len(df_long), len(df_clean))
        return df_clean

    logging.info("Rows: %d", len(df_long))
    return df_long


if __name__ == "__main__":
    main(write_excel=True, normalise_amounts=True)
