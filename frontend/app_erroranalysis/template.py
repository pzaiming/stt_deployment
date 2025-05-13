from dash import html, dash_table, dcc
import dash_bootstrap_components as dbc
import pandas as pd


INPUT_STYLE = {
    "borderWidth": "1px",
    "borderStyle": "dashed",
    "borderRadius": "5px",
    "textAlign": "center",
    "margin": "10px",
    "padding": "10px" 
}

RED_BUTTON_STYLE = {
    "backgroundColor": "red",
    "border": "none"
}


def get_layout() -> html.Div:
    layout = dbc.Container([
        html.Header(
            html.H1("Error Analysis")
        ),
        html.Div([
            "Upload word_errors.csv",
            dcc.Upload(
                [
                    "Drag and Drop or ",
                    html.A("Select Files", style={"color": "blue"})
                ], style=INPUT_STYLE, id="upload_word_errors", multiple=False
            ),
            dcc.Interval(
                id='interval-component',
                interval=5*1000, # in milliseconds
                n_intervals=0
            ),
            html.Div(id="upload_status_word_errors")
        ], style={"display": "flex", "alignItems": "center"}),
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(
                    id="datatable",
                    sort_action="native",
                    sort_mode="multi",
                    row_selectable="single",
                    hidden_columns=["index"],
                    page_size=10,
                    css=[{"selector": ".show-hide", "rule": "display: none"}]
                ),
                dbc.Button("Deselect row", id="deselect_table", n_clicks=0)
            ], width=6),
            dbc.Col([
                html.Div(children=[
                    "Selected categories: ",
                    dcc.Checklist(
                        id="categories",
                        options=["Substitutions", "Deletions", "Insertions", "Correct"],
                        value=["Substitutions", "Deletions", "Insertions"]
                    ),
                ]),
                html.Br(),
                html.Div(children=[
                    "Search GT word: ",
                    dcc.Input("", id="search_source_word", type="text", placeholder="GT word")
                ]),
                html.Div(children=[
                    "Search STT word: ",
                    dcc.Input("", id="search_target_word", type="text", placeholder="STT word")
                ]),
                html.Div(children=[
                    "Minimum count: ",
                    dcc.Input(id="min_count", type="number", min=0, placeholder="Minimum count")
                ]),
                html.Div([
                    "Maximum count: ",
                    dcc.Input(id="max_count", type="number", min=0, placeholder="Maximum count")
                ]),
                dbc.Button("Clear filters", id="clear_filters", n_clicks=0)
            ], width=2),
            dbc.Col([
                html.H1("Stats"),
                html.Div(id="wer_stats")
            ], width=4)
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.P(children="Keywords separated by comma"),
                    dcc.Upload(
                        [
                            "Drag and Drop or ",
                            html.A("Select Files", style={"color": "blue"})
                        ], style=INPUT_STYLE, id="upload_keywords", multiple=False
                    ),
                    html.Div(id="upload_status"),
                    dcc.Input(id="input_keywords", type="text", placeholder="Keywords", style={"width": "100%"}),
                    dcc.Dropdown([], "", id="keywords", placeholder="Select keyword...")
                ]),
                width=3
            ),
            dbc.Col(
                html.Div([
                    html.P("Selected GT word:"),
                    dcc.Input("", id="source_word", type="text", placeholder="GT word"),
                    dbc.Button("Clear word", id="deselect_source_word", n_clicks=0)
            ]),
                width=3
            ),
            dbc.Col(
                html.Div([
                    html.P("Selected STT word:"),
                    dcc.Input("", id="target_word", type="text", placeholder="STT word"),
                    dbc.Button("Clear word", id="deselect_target_word", n_clicks=0)
            ]),
                width=3
            ),
            dbc.Col(
                html.Div([
                    html.P("Selected category:"),
                    dcc.Dropdown(["Substitutions", "Deletions", "Insertions"], "Substitutions", clearable=False, id="selected_category")
                ]),
                width=3
            )
        ]),
        html.Hr(),
        dbc.Row([
            html.Div([
                html.Span("Mode: ", id="mode_tooltip_target"),
                dcc.Dropdown(["GT", "STT"], "GT", clearable=False, id="toggle_mode", style={"width": "60px", "margin": "5px"})
            ], style={"display": "flex", "alignItems": "center"}),
            dbc.Tooltip(
                "GT mode shows what words the GT word was replaced with in the STT transcript. "
                "STT mode shows what words the STT word replaced from the GT.",
                target="mode_tooltip_target")
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(
                [
                    html.H1("Word Breakdown"),
                    dcc.Graph(id="pie"),
                ],
                width=3
            ),
            dbc.Col(
                [
                    html.H1("Substitutions Breakdown"),
                    dcc.Graph(id="graph")
                ],
                width=4
            ),
            dbc.Col(
                [
                    html.H1("Errors"),
                    html.Div([
                        "Upload errors_context.csv",
                        dcc.Upload(
                            [
                                "Drag and Drop or ",
                                html.A("Select Files", style={"color": "blue"})
                            ], style=INPUT_STYLE, id="upload_errors_context", multiple=False
                        ),
                    html.Div(id="upload_status_errors_context")
                    ], style={"display": "flex", "alignItems": "center"}),
                    html.Div("", id="alignments", style={
                        "height": "600px",
                        "overflowY": "scroll"
                    })
                ],
                width=5
            )
        ]),

        dcc.Store("df", data=None),
        dcc.Store("errors_df", data=None),
        dcc.Store("selected_index", data=None),
        dcc.Store("filtered_rows", data=pd.Index([])),
        dcc.Store("selected_rows", data=pd.Index([]))
    ],
    fluid=True)
    return layout