def deduplicate_nodes_and_rels(df_nodes, df_rels):
    # remove duplicate rows by unique_id (nodes) and source-target-type triplet (rels)
    return (
        df_nodes.drop_duplicates(subset="unique_id"),
        df_rels.drop_duplicates(subset=["source", "target", "type"])
    )

def filter_nodes_by_label(df_nodes):
    # split df_all_nodes into filtered views containing each node label type
    return {
        "joint_venture": df_nodes[df_nodes["label"].str.lower() == "joint_venture"],
        "factory": df_nodes[df_nodes["label"].str.lower().str.contains("factory", na=False)].copy(),
        "capacity": df_nodes[df_nodes["label"].str.lower() == "capacity"],
        "product": df_nodes[df_nodes["label"].str.lower() == "product"],
        "company": df_nodes[df_nodes["label"].str.lower() == "company"],
        "investment": df_nodes[df_nodes["label"].str.lower() == "investment"],
        "owner": df_nodes[df_nodes["label"].str.lower().isin(["company", "joint_venture"])]
    }

def filter_rels_by_label(df_rels):
    # split df_all_rels into filtered views containing each relationship type
    return {
        "owns": df_rels[df_rels["type"].str.lower() == "owns"],                 #ownership
        "forms": df_rels[df_rels["type"].str.lower() == "owns"],                #ownership
        "at": df_rels[df_rels["type"].str.lower() == "at"],                     #technological
        "produced_at": df_rels[df_rels["type"].str.lower() == "produced_at"],   #technological
        "quantifies": df_rels[df_rels["type"].str.lower() == "quantifies"],     #technological
        "funds": df_rels[df_rels["type"].str.lower() == "funds"],               #financial-technological   
        "targets": df_rels[df_rels["type"].str.lower() == "targets"],           #financial-technological
        "enables": df_rels[df_rels["type"].str.lower() == "enables"],           #financial-technological
        "invests": df_rels[df_rels["type"].str.lower() == "invests"],           #financial-origin
        "receives": df_rels[df_rels["type"].str.lower() == "receives"]          #financial-origin
    }