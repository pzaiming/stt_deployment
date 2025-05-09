import pandas as pd


RED_NODE = "rgba(214, 39, 40, 0.8)"
YELLOW_NODE = "rgba(188, 189, 34, 0.8)"
RED_LINK = "rgba(214, 39, 40, 0.2)"
YELLOW_LINK = "rgba(188, 189, 34, 0.2)"
BLUE_NODE = "rgba(31, 119, 180, 0.8)"

GREEN_PIE = "rgb(0, 204, 150)"
RED_PIE = "rgb(239, 85, 59)"
BLUE_PIE = "rgb(99, 110, 250)"
YELLOW_PIE = "rgb(254, 203, 82)"


def get_piechart_lists(df: pd.DataFrame):
    categories = df.groupby("Category")["Count"].sum()
    args = dict(
        labels=categories.index,
        values=categories.values
    )
    colors = []
    for cat in categories.index:
        if cat == "Deletions":
            colors.append(RED_PIE)
        elif cat == "Correct":
            colors.append(GREEN_PIE)
        elif cat == "Insertions":
            colors.append(BLUE_PIE)
        else:
            colors.append(YELLOW_PIE)
    return args, colors


def get_sankey_lists(df):
    node = {
        "label": [],
        "color": []
    }
    link = {
        "source": [],
        "target": [],
        "value": [],
        "color": [],
        "label": []
    }
    if df is None:
        return node, link

    # Generate node
    src_words = df["Source"].unique()
    src_vocab = {}
    for word in src_words:
        src_vocab[word] = len(src_vocab)
    dst_words = df["Destination"].unique()
    dst_vocab = {}
    for word in dst_words:
        dst_vocab[word] = len(src_vocab) + len(dst_vocab)

    node["label"] = list(src_vocab.keys()) + list(dst_vocab.keys())
    for i, label in enumerate(node["label"]):
        if pd.isna(label):
            node["label"][i] = "DELETED"
            node["color"].append(RED_NODE)
        else:
            node["color"].append(YELLOW_NODE)

    # Generate link
    for _, row in df.iterrows():
        link["source"].append(src_vocab[row["Source"]])
        link["target"].append(dst_vocab[row["Destination"]])
        link["value"].append(row["Count"])
        link["label"].append(row["Count"])
        if pd.isna(row["Destination"]):
            link["color"].append(RED_LINK)
        else:
            link["color"].append(YELLOW_LINK)
    
    return node, link


def get_barplot_lists(df: pd.DataFrame):
    args = {
        "x": df["Source"],
        "y": df["Count"],
        "marker_color": []
    }

    for _, row in df.iterrows():
        if row["Category"] == "Substitutions":
            color = YELLOW_NODE
        elif row["Category"] == "Deletions":
            color = RED_NODE
        else:
            color = BLUE_NODE
        args["marker_color"].append(color)

    return args