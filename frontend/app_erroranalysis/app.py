import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import base64
import io
import pandas as pd

from dash import Dash, html, Input, Output, State
from dash_extensions.callback import CallbackCache
from functools import reduce

from template import get_layout
from plot_functions import get_piechart_lists, get_sankey_lists

# Initialize app
app = Dash(__name__)
cc = CallbackCache()
server = app.server

# App layout
app.layout = get_layout()

#####################################
# Callbacks related to data uploads #
#####################################

@cc.cached_callback(
    Output("df", "data"),
    [
        Input("upload_word_errors", "contents"),
        Input("upload_word_errors", "filename")
    ]
)
def upload_word_errors(contents, filename):
    if contents is not None:
        # Parse the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8'))).reset_index()
            return df.to_json(date_format='iso', orient='split')
        except Exception as e:
            print(f"Error parsing uploaded file: {e}")
            return None
    else:
        # Read data from local file or generate sample data
        try:
            df = pd.read_csv('word_errors.csv').reset_index()
            return df.to_json(date_format='iso', orient='split')
        except FileNotFoundError:
            # Generate sample data if file not found
            df = pd.DataFrame({
                'Source': ['example', 'test', 'data'],
                'Destination': ['sample', 'demo', 'information'],
                'Count': [10, 5, 15],
                'Category': ['Substitutions', 'Deletions', 'Insertions']
            }).reset_index()
            return df.to_json(date_format='iso', orient='split')
        except Exception as e:
            print(f"Error reading local file: {e}")
            return None

@cc.callback(
    Output("upload_status_word_errors", "children"),
    [
        Input("df", "data"),
        State("upload_word_errors", "filename")
    ]
)
def update_word_errors_status(df_data, filename):
    if df_data is None:
        return "No file uploaded."
    if filename:
        return html.Span(f"Uploaded {filename}", style={"color": "green"})
    else:
        return html.Span("Using default data", style={"color": "green"})

@cc.cached_callback(
    Output("errors_df", "data"),
    [
        Input("upload_errors_context", "contents"),
        Input("upload_errors_context", "filename")
    ]
)
def upload_errors_context(contents, filename):
    if contents is not None:
        # Parse the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            errors_df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            return errors_df.to_json(date_format='iso', orient='split')
        except Exception as e:
            print(f"Error parsing uploaded file: {e}")
            return None
    else:
        # Read data from local file or generate sample data
        try:
            errors_df = pd.read_csv('errors_context.csv')
            return errors_df.to_json(date_format='iso', orient='split')
        except FileNotFoundError:
            # Generate sample data if file not found
            errors_df = pd.DataFrame({
                'filename': ['file1', 'file2', 'file3'],
                'ref': ['word1', 'word2', 'word3'],
                'hyp': ['wordA', 'wordB', 'wordC'],
                'type': ['substitute', 'delete', 'insert'],
                'ref_prev': ['', 'word0', ''],
                'ref_post': ['word2', '', 'word4'],
                'hyp_prev': ['', 'wordX', ''],
                'hyp_post': ['wordY', '', 'wordZ']
            })
            return errors_df.to_json(date_format='iso', orient='split')
        except Exception as e:
            print(f"Error reading local file: {e}")
            return None

@cc.callback(
    Output("upload_status_errors_context", "children"),
    [
        Input("errors_df", "data"),
        State("upload_errors_context", "filename")
    ]
)
def update_errors_context_status(errors_df_data, filename):
    if errors_df_data is None:
        return "No file uploaded."
    if filename:
        return html.Span(f"Uploaded {filename}", style={"color": "green"})
    else:
        return html.Span("Using default data", style={"color": "green"})

################################################
# Callbacks related to datatable and filtering #
################################################

@cc.callback(
    [
        Output("datatable", "data"),
        Output("datatable", "selected_rows")
    ],
    [
        Input("df", "data"),
        Input("datatable", "data"),
        Input("datatable", "selected_rows"),
        Input("categories", "value"),
        Input("search_source_word", "value"),
        Input("search_target_word", "value"),
        Input("min_count", "value"),
        Input("max_count", "value")
    ],
)
def update_filtered_rows(df_data, data, selected_rows, categories, search_source_word, search_target_word, min_count, max_count):
    if df_data is None:
        return None, []
    df = pd.read_json(io.StringIO(df_data), orient='split')

    # Categories filter
    filters = [df["Category"].isin(categories)]

    # Search words
    if search_source_word != "":
        filters.append(df["Source"].str.contains(search_source_word))
    if search_target_word != "":
        filters.append(df["Destination"].str.contains(search_target_word))

    # Min count filter
    if min_count is not None:
        filters.append(df["Count"] >= min_count)
    if max_count is not None:
        filters.append(df["Count"] <= max_count)

    # Apply filters and return index
    filtered_rows = df[reduce(lambda f1, f2: f1 & f2, filters)].index

    # Update selected rows
    new_selected_rows = []
    if selected_rows is not None and len(selected_rows) > 0:
        selected_index = data[selected_rows[0]]["index"]
        if selected_index in filtered_rows:
            new_selected_rows.append(filtered_rows.get_loc(selected_index))

    # Update datatable data
    filtered_data = df.loc[filtered_rows].to_dict("records")
    return filtered_data, new_selected_rows

@app.callback(
    [
        Output("search_source_word", "value"),
        Output("search_target_word", "value"),
        Output("min_count", "value"),
        Output("max_count", "value")
    ],
    Input("clear_filters", "n_clicks")
)
def clear_filters(n_clicks):
    return "", "", None, None

@app.callback(
    Output("selected_index", "data"),
    [
        Input("datatable", "data"),
        Input("datatable", "selected_rows")
    ],
    prevent_initial_call=True
)
def update_selected_index(data, selected_rows):
    if selected_rows is not None and len(selected_rows) > 0:
        return data[selected_rows[0]]["index"]
    return None

@app.callback(
    Output("datatable", "selected_rows", allow_duplicate=True),
    Input("deselect_table", "n_clicks"),
    prevent_initial_call=True
)
def deselect_table(n_clicks):
    return []

##################################################################
# Callbacks related to updating selected source and target words #
##################################################################

@cc.callback(
    Output("source_word", "value"),
    [
        Input("df", "data"),
        Input("selected_index", "data")
    ]
)
def update_source_words(df_data, selected_index):
    if df_data is None or selected_index is None:
        return ""
    df = pd.read_json(io.StringIO(df_data), orient='split')
    source_word = df.loc[selected_index]["Source"]
    if type(source_word) != str:
        return ""
    return source_word

@app.callback(
    [
        Output("source_word", "value", allow_duplicate=True),
        Output("keywords", "value")
    ],
    Input("deselect_source_word", "n_clicks"),
    prevent_initial_call=True
)
def deselect_source_word(n_clicks):
    return "", None

@cc.callback(
    Output("selected_rows", "data"),
    [
        Input("df", "data"),
        Input("source_word", "value"),
        Input("target_word", "value"),
        Input("toggle_mode", "value")
    ]
)
def update_selected_rows(df_data, source_word, target_word, toggle_mode):
    if df_data is None:
        return pd.Index([])
    df = pd.read_json(io.StringIO(df_data), orient='split')

    if toggle_mode == "GT":
        if source_word == "":
            return pd.Index([])
        selected_rows = df[df["Source"] == source_word].index
    else:
        if target_word == "":
            return pd.Index([])
        selected_rows = df[df["Destination"] == target_word].index
    return selected_rows

@cc.callback(
    Output("target_word", "value"),
    [
        Input("df", "data"),
        Input("selected_index", "data")
    ]
)
def update_target_word(df_data, selected_index):
    if df_data is None or selected_index is None:
        return ""
    df = pd.read_json(io.StringIO(df_data), orient='split')
    target_word = df.loc[selected_index]["Destination"]
    if type(target_word) != str:
        return ""
    return target_word

@app.callback(
    [
        Output("source_word", "value", allow_duplicate=True),
        Output("target_word", "value", allow_duplicate=True),
    ],
    [
        Input("graph", "clickData"),
        State("source_word", "value"),
        State("target_word", "value"),
        State("toggle_mode", "value")
    ],
    prevent_initial_call=True
)
def update_click_target_word(clickData, source_word, target_word, toggle_mode):
    if clickData is None:
        return source_word, target_word
    result = clickData["points"][0]
    word = result["label"]
    if "group" not in result or (toggle_mode == "GT" and word == source_word) or (toggle_mode == "STT" and word == target_word):
        word = ""

    if toggle_mode == "GT":
        target_word = word
    else:
        source_word = word

    return source_word, target_word

@app.callback(
    Output("target_word", "value", allow_duplicate=True),
    Input("deselect_target_word", "n_clicks"),
    prevent_initial_call=True
)
def deselect_target_word(n_clicks):
    return ""

@cc.callback(
    Output("selected_category", "value"),
    [
        Input("df", "data"),
        Input("selected_index", "data"),
        State("selected_category", "value")
    ]
)
def update_table_selected_category(df_data, selected_index, selected_category):
    if df_data is None or selected_index is None:
        return selected_category
    df = pd.read_json(io.StringIO(df_data), orient='split')
    return df.loc[selected_index]["Category"]

##################################
# Callbacks relating to keywords #
##################################

@app.callback(
    [
        Output("input_keywords", "value"),
        Output("upload_status", "children")
    ],
    [
        Input("upload_keywords", "contents"),
        State("upload_keywords", "filename")
    ],
    prevent_initial_call=True
)
def upload_input_keywords(contents, filename):
    if contents is None:
        return "", None

    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    try:
        result = decoded.decode("utf-8")
    except Exception as e:
        return "", html.P(f"Error uploading {filename}: {e}", style={"color": "red"})

    return result, html.P(f"Successfully uploaded {filename}", style={"color": "green"})

@app.callback(
    Output("keywords", "options"),
    Input("input_keywords", "value"),
    prevent_initial_call=True
)
def update_keywords(input_keywords):
    if input_keywords is None:
        return []
    input_keywords = input_keywords.strip()
    if len(input_keywords) == 0:
        return []
    return [word.strip() for word in input_keywords.split(",")]

@app.callback(
    Output("source_word", "value", allow_duplicate=True),
    Input("keywords", "value"),
    prevent_initial_call=True
)
def update_keywords_source_word(keywords):
    if keywords is None:
        return ""
    return keywords

##############################
# Callbacks related to stats #
##############################

@cc.callback(
    Output("wer_stats", "children"),
    [Input("df", "data")]
)
def update_wer_stats(df_data):
    if df_data is None:
        return []
    df = pd.read_json(io.StringIO(df_data), orient='split')

    cat_counts = df.groupby("Category")["Count"].sum()
    total_words = cat_counts.get("Correct", 0) + cat_counts.get("Substitutions", 0) + cat_counts.get("Deletions", 0)
    total_errors = cat_counts.get("Substitutions", 0) + cat_counts.get("Deletions", 0) + cat_counts.get("Insertions", 0)
    wer = total_errors / total_words if total_words > 0 else 0

    output = [
        html.P(f"Word Error Rate: {wer:.2%}"),
        html.P(f"Total words in GT: {total_words}"),
        html.P(f"Total errors in STT: {total_errors}"),
        html.Br(),
        html.P(f"Correct: {cat_counts.get('Correct', 0)}"),
        html.P(f"Substitutions: {cat_counts.get('Substitutions', 0)}"),
        html.P(f"Deletions: {cat_counts.get('Deletions', 0)}"),
        html.P(f"Insertions: {cat_counts.get('Insertions', 0)}")
    ]

    return output

########################################
# Callbacks related to figure plotting #
########################################

@cc.callback(
    Output("pie", "figure"),
    [
        Input("df", "data"),
        Input("source_word", "value"),
        Input("target_word", "value"),
        Input("selected_rows", "data"),
        Input("toggle_mode", "value")
    ])
def display_piechart(df_data, source_word: str, target_word: str, selected_rows: pd.Index, toggle_mode: str):
    if df_data is None:
        df = pd.DataFrame(columns=["Source", "Destination", "Count", "Category"])
    else:
        df = pd.read_json(io.StringIO(df_data), orient='split')

    selected_data = df.iloc[selected_rows]

    piechart_lists, colors = get_piechart_lists(selected_data)
    fig = go.Figure(data=[go.Pie(
        hole=.3,
        **piechart_lists
    )], layout=go.Layout(showlegend=False))
    fig.update_traces(
        textinfo="label+percent+value",
        textposition="inside",
        marker=dict(
            colors=colors,
            line=dict(
                color="#000000",
                width=1
            )
        )
    )
    fig.update_layout(
        annotations=[dict(
            text=source_word if toggle_mode == "GT" else target_word,
            showarrow=False
        )],
        uniformtext_minsize=12,
        uniformtext_mode="hide"
    )
    return fig

@app.callback(
    Output("selected_category", "value", allow_duplicate=True),
    Input("pie", "clickData"),
    prevent_initial_call=True
)
def update_click_selected_category(clickData):
    if clickData is not None:
        return clickData["points"][0]["label"]
    return "Substitutions"

@cc.callback(
    Output("graph", "figure"),
    [
        Input("df", "data"),
        Input("selected_rows", "data")
    ]
)
def display_figure(df_data, selected_rows: pd.Index):
    if df_data is None:
        df = pd.DataFrame(columns=["Source", "Destination", "Count", "Category"])
    else:
        df = pd.read_json(io.StringIO(df_data), orient='split')
    selected_data = df.loc[selected_rows]
    # Only show substitutions
    selected_data = selected_data[selected_data["Category"] == "Substitutions"]

    # Generate graph
    node, link = get_sankey_lists(selected_data)
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            **node
        ),
        link = link
    )])
    return fig

@cc.callback(
    Output("alignments", "children"),
    [
        Input("errors_df", "data"),
        Input("selected_category", "value"),
        Input("source_word", "value"),
        Input("target_word", "value")
    ]
)
def update_alignments(errors_df_data, selected_category, source_word, target_word):
    if errors_df_data is None:
        return ""
    errors_df = pd.read_json(io.StringIO(errors_df_data), orient='split')
    if selected_category is not None and (source_word != "" or target_word != ""):
        text = []
        categories = {"Substitutions": "substitute", "Deletions": "delete", "Insertions": "insert"}
        if selected_category in categories:
            cat = categories[selected_category]
            data = errors_df[errors_df["type"] == cat]
            if source_word != "" and (selected_category == "Deletions" or selected_category == "Substitutions"):
                data = data[data["ref"].str.strip() == source_word]
            if target_word != "" and (selected_category == "Insertions" or selected_category == "Substitutions"):
                data = data[data["hyp"].str.strip() == target_word]
            for _, row in data.iterrows():
                text.append(html.P(row['filename']))
                text.append(html.P([
                    f"GT:  {row['ref_prev']} ",
                    html.Span(row['ref'], style={"color": "green"}),
                    f" {row['ref_post']}"
                ], style={"font-family": "monospace", "white-space": "pre"}))
                text.append(html.P([
                    f"STT: {row['hyp_prev']} ",
                    html.Span(row['hyp'], style={"color": "red"}),
                    f" {row['hyp_post']}"
                ], style={"font-family": "monospace", "white-space": "pre"}))
                text.append(html.Br())
        return text
    return ""

cc.register(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)