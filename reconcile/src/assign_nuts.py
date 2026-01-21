# pip install pandas geopandas shapely pyogrio

import pandas as pd
import geopandas as gpd
from pathlib import Path

RECONCILE_DIR = Path(__file__).resolve().parents[1]   # src/ -> reconcile/
NUTS2_GEOJSON = RECONCILE_DIR / "storage/input" / "NUTS_RG_03M_2024_4326_LEVL_2.geojson"

def assign_nuts2_to_dataframe(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    nuts2_geojson: str = NUTS2_GEOJSON
) -> pd.DataFrame:
    """
    Assign NUTS-2 regions to points in a DataFrame based on lat/lon coordinates.
    
    Args:
        df: Input DataFrame with lat/lon columns
        lat_col: Name of latitude column (default: "lat")
        lon_col: Name of longitude column (default: "lon")
        nuts2_geojson: Path to NUTS-2 GeoJSON file
    
    Returns:
        DataFrame with added columns: nuts2_id, nuts2_name
        Points without NUTS-2 match will have NaN in these columns.
    """
    # Skip if lat/lon columns are missing
    if lat_col not in df.columns or lon_col not in df.columns:
        return df
    
    # Filter out rows with missing coordinates
    valid_coords = df[[lat_col, lon_col]].notna().all(axis=1)
    if not valid_coords.any():
        # No valid coordinates, return df with empty NUTS columns
        df["nuts2_id"] = None
        df["nuts2_name"] = None
        return df
    
    # 1) Convert to GeoDataFrame (lon, lat) in EPSG:4326
    gdf_points = gpd.GeoDataFrame(
        df[valid_coords].copy(),
        geometry=gpd.points_from_xy(
            df.loc[valid_coords, lon_col], 
            df.loc[valid_coords, lat_col]
        ),
        crs="EPSG:4326",
    )
    
    # 2) Read NUTS-2 polygons
    gdf_nuts2 = gpd.read_file(nuts2_geojson)[["NUTS_ID", "NAME_LATN", "geometry"]]
    
    # 3) Spatial join: attach NUTS-2 attributes to each point
    joined = gpd.sjoin(
        gdf_points,
        gdf_nuts2,
        how="left",
        predicate="within",  # points within polygons
    ).drop(columns=["index_right"])
    
    # 4) Merge back to original df, preserving all rows
    df = df.copy()
    df["nuts2_id"] = None
    df["nuts2_name"] = None
    df.loc[valid_coords, "nuts2_id"] = joined["NUTS_ID"].values
    df.loc[valid_coords, "nuts2_name"] = joined["NAME_LATN"].values
    
    return df