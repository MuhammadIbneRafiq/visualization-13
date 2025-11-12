from dash import Dash, dcc, html, dash_table, no_update, callback_context
import plotly.graph_objs as go
from dash.dependencies import State, Input, Output
from dash.exceptions import PreventUpdate

import pandas as pd
import numpy as np
import plotly.express as px
import json

# Load and prepare the shark attack data
file_path = 'data/Australian Shark-Incident Database Public Version.xlsx'
df_shark = pd.read_excel(file_path, index_col=0)

with open("data/australian-states.json") as f:
    aus_states_geojson = json.load(f)

app = Dash(
    __name__,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1.0, user-scalable=no",
        }
    ],
)
app.title = "Australian Shark Incident Analysis"
server = app.server

app.config["suppress_callback_exceptions"] = True

def build_upper_left_panel():
    return html.Div(
        id="upper-left",
        className="three columns",
        children=[
            html.P(
                className="section-title",
                children="Choose filters to see shark incident data",
            ),
            html.Div(
                className="control-row-1",
                children=[
                    html.Div(
                        id="state-select-outer",
                        children=[
                            html.Label("Select a State"),
                            dcc.Dropdown(
                                id="state-select",
                                options=[{"label": i, "value": i} for i in df_shark['State'].unique()],
                                value=df_shark['State'].unique()[0],
                            ),
                        ],
                    ),
                    html.Div(
                        id="select-metric-outer",
                        children=[
                            html.Label("Choose a Metric"),
                            dcc.Dropdown(
                                id="metric-select",
                                options=[
                                    {"label": "Victim Age", "value": "Victim.age"},
                                    {"label": "Shark Length", "value": "Shark.length.m"},
                                    {"label": "Shark name", "value": "Shark.common.name"},
                                    {"label": "Victim clothing", "value": "Shark.length.m"},
                                ],
                                value="Shark.common.name",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="region-select-outer",
                className="control-row-2",
                children=[
                    html.Label("Pick a Region"),
                    html.Div(
                        id="checklist-container",
                        children=dcc.Checklist(
                            id="region-select-all",
                            options=[{"label": "Select All Regions", "value": "All"}],
                            value=[],
                        ),
                    ),
                    html.Div(
                        id="region-select-dropdown-outer",
                        children=dcc.Dropdown(
                            id="region-select", multi=True, searchable=True,
                        ),
                    ),
                ],
            ),
        ],
    )

def generate_procedure_plot(raw_data, cost_select, region_select, provider_select):
    # Filter data based on region
    procedure_data = raw_data[raw_data['State'].isin(region_select)].reset_index()

    traces = []
    selected_index = procedure_data[
        procedure_data['Location'].isin(provider_select)
    ].index

    text = (
        procedure_data['Location']
        + "<br>"
        + "<b>"
        + procedure_data['Shark.common.name'].map(str)
        + "/<b> <br>"
        + "Incident Year: "
        + procedure_data['Incident.year'].map(str)
    )

    provider_trace = go.Box(
        y=procedure_data['Shark.common.name'],
        x=procedure_data[cost_select],
        name="",
        customdata=procedure_data['Location'],
        boxpoints="all",
        jitter=0,
        pointpos=0,
        hoveron="points",
        fillcolor="rgba(0,0,0,0)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="text",
        hovertext=text,
        selectedpoints=selected_index,
        selected=dict(marker={"color": "#FFFF00", "size": 13}),
        unselected=dict(marker={"opacity": 0.2}),
        marker=dict(
            line=dict(width=1, color="#000000"),
            color="#21c7ef",
            opacity=0.7,
            symbol="square",
            size=12,
        ),
    )

    traces.append(provider_trace)

    layout = go.Layout(
        showlegend=False,
        hovermode="closest",
        dragmode="select",
        clickmode="event+select",
        xaxis=dict(
            zeroline=False,
            automargin=True,
            showticklabels=True,
            title=dict(text="Metric", font=dict(color="#737a8d")),
            linecolor="#737a8d",
            tickfont=dict(color="#737a8d"),
            type="log",
        ),
        yaxis=dict(
            automargin=True,
            showticklabels=True,
            tickfont=dict(color="#737a8d"),
            gridcolor="#171b26",
        ),
        plot_bgcolor="#171b26",
        paper_bgcolor="#171b26",
    )
    return {"data": traces, "layout": layout}

def create_parallel_coordinates():
    # Select numerical columns for parallel coordinates
    numerical_cols = ['Victim.age', 'Shark.length.m', 'Latitude', 'Longitude', 'Incident.year']
    dimensions = []

    # Loop through the numerical columns and handle data conversion
    for col in numerical_cols:
       
        # Convert column to numeric, coercing errors to NaN
        numeric_series = pd.to_numeric(df_shark[col], errors='coerce')
        
        # Create the dimension for the plot
        dimensions.append(
            dict(
                range=[numeric_series.min(), numeric_series.max()],
                label=col.replace('.', ' '),
                values=numeric_series,
                ticktext=None,
                tickvals=None
            )
        )
    
    # Add categorical dimension for Shark Species
    dimensions.append(
        dict(
            range=[0, len(df_shark['Shark.common.name'].unique())],
            ticktext=df_shark['Shark.common.name'].unique(),
            tickvals=list(range(len(df_shark['Shark.common.name'].unique()))),
            label='Shark Species',
            values=[list(df_shark['Shark.common.name'].unique()).index(x) for x in df_shark['Shark.common.name']]
        )
    )
    
    # Create parallel coordinates plot
    fig = go.Figure(data=
        go.Parcoords(
            line=dict(
                color=df_shark['Incident.year'],
                colorscale='Viridis'
            ),
            dimensions=dimensions,
        )
    )
    
    # Update layout
    fig.update_layout(
        plot_bgcolor='#171b26',
        paper_bgcolor='#171b26',
        font=dict(color='#737a8d'),
        margin=dict(l=80, r=80, t=30, b=30),
    )
    
    return fig

# Add this to app layout in the lower container


# Define the layout
app.layout = html.Div(
    className="container scalable",
    children=[
        html.Div(
            id="banner",
            className="banner",
            children=[
                html.H6("Australian Shark attack"),
                html.Img(src=app.get_asset_url("plotly_logo_white.png")),
            ],
        ),
        html.Div(
            id="upper-container",
            className="row",
            children=[
                build_upper_left_panel(),
                html.Div(
                    id="geo-map-outer",
                    className="eight columns",
                    children=[
                        html.P(
                            id="map-title",
                            children="Shark Incidents in Australia",
                        ),
                        html.Div(
                            id="geo-map-loading-outer",
                            children=[
                                dcc.Loading(
                                    id="loading",
                                    children=dcc.Graph(
                                        id="geo-map",
                                        figure={
                                            "data": [],
                                            "layout": dict(
                                                plot_bgcolor="#171b26",
                                                paper_bgcolor="#171b26",
                                            ),
                                        },
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="lower-container",
            children=[
                # dcc.Graph(
                #     id="procedure-plot",
                #     figure=generate_procedure_plot(
                #         df_shark, 'Victim.age', df_shark['State'].unique(), []
                #     ),
                # ),
                # Add parallel coordinates plot
                html.Div(
                    className="twelve columns",
                    children=[
                        html.P(
                            className="section-title",
                            children="Parallel Coordinates View of Shark Incident Data",
                        ),
                        dcc.Graph(
                            id='parallel-coords-plot',
                            figure=create_parallel_coordinates()
                        )
                    ]
                )
            ],
        ),
    ],
)

@app.callback(
    [Output("region-select", "options"), Output("region-select", "value")],
    [Input("state-select", "value"), Input("region-select-all", "value")],
)
def update_region_dropdown(state_select, select_all):
    if not state_select:
        return [], []
        
    # Filter data for the selected state
    state_data = df_shark[df_shark["State"] == state_select]

    # Get unique regions and handle NaN values
    regions = state_data["Location"].fillna("Unknown Location").unique()
    
    # Convert all values to strings and filter out empty strings
    regions = [str(region) for region in regions if str(region).strip()]
    
    # Sort the cleaned list
    regions.sort()

    # Create dropdown options
    options = [{"label": region, "value": region} for region in regions]

    # Auto-select all regions if "Select All Regions" is checked
    if select_all and "All" in select_all:
        value = regions
    else:
        value = []

    return options, value
@app.callback(
    Output("checklist-container", "children"),
    [Input("region-select", "value")],
    [State("region-select", "options"), State("region-select-all", "value")],
)
def update_checklist(selected, select_options, checked):
    if len(selected) < len(select_options) and len(checked) == 0:
        raise PreventUpdate()

    elif len(selected) < len(select_options) and len(checked) == 1:
        return dcc.Checklist(
            id="region-select-all",
            options=[{"label": "Select All Regions", "value": "All"}],
            value=[],
        )

    elif len(selected) == len(select_options) and len(checked) == 1:
        raise PreventUpdate()

    return dcc.Checklist(
        id="region-select-all",
        options=[{"label": "Select All Regions", "value": "All"}],
        value=["All"],
    )

@app.callback(
    Output("cost-stats-container", "children"),
    [
        Input("geo-map", "selectedData"),
        Input("procedure-plot", "selectedData"),
        Input("metric-select", "value"),
        Input("state-select", "value"),
    ],
)
def update_hospital_datatable(geo_select, procedure_select, cost_select, state_select):
    state_agg = df_shark[df_shark['State'] == state_select]
    # make table from geo-select
    geo_data_dict = {
        "Location": [],
        "Shark Species": [],
        "Incident Year": [],
        "Maximum Metric": [],
        "Minimum Metric": [],
    }

    ctx = callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # make table from procedure-select
        if prop_id == "procedure-plot" and procedure_select is not None:
            for point in procedure_select["points"]:
                location = point["customdata"]
                dff = state_agg[state_agg["Location"] == location]

                if not dff.empty:
                    geo_data_dict["Location"].append(location)
                    shark_species = dff["Shark.common.name"].tolist()[0]
                    geo_data_dict["Shark Species"].append(shark_species)

                    year = dff["Incident.year"].tolist()[0]
                    geo_data_dict["Incident Year"].append(year)

                    geo_data_dict["Maximum Metric"].append(
                        dff[cost_select].max()
                    )
                    geo_data_dict["Minimum Metric"].append(
                        dff[cost_select].min()
                    )

        if prop_id == "geo-map" and geo_select is not None:
            for point in geo_select["points"]:
                location = point["customdata"][0]
                dff = state_agg[state_agg["Location"] == location]

                if not dff.empty:
                    geo_data_dict["Location"].append(location)
                    geo_data_dict["Shark Species"].append(dff["Shark.common.name"].tolist()[0])

                    year = dff["Incident.year"].tolist()[0]
                    geo_data_dict["Incident Year"].append(year)

                    geo_data_dict["Maximum Metric"].append(
                        dff[cost_select].max()
                    )
                    geo_data_dict["Minimum Metric"].append(
                        dff[cost_select].min()
                    )

        geo_data_df = pd.DataFrame(data=geo_data_dict)
        data = geo_data_df.to_dict("records")

    else:
        data = [{}]

    return dash_table.DataTable(
        id="cost-stats-table",
        columns=[{"name": i, "id": i} for i in geo_data_dict.keys()],
        data=data,
        filter_action="native",
        page_size=5,
        style_cell={"background-color": "#242a3b", "color": "#7b7d8d"},
        style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "0px 5px"},
    )

@app.callback(
    Output("procedure-stats-container", "children"),
    [
        Input("procedure-plot", "selectedData"),
        Input("geo-map", "selectedData"),
        Input("metric-select", "value"),
    ],
    [State("state-select", "value")],
)
def update_procedure_stats(procedure_select, geo_select, cost_select, state_select):
    procedure_dict = {
        "Shark Species": [],
        "Location": [],
        "Incident Year": [],
        "Metric Summary": [],
    }

    ctx = callback_context
    prop_id = ""
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if prop_id == "procedure-plot" and procedure_select is not None:
        for point in procedure_select["points"]:
            procedure_dict["Shark Species"].append(point["y"])
            procedure_dict["Location"].append(point["customdata"])
            procedure_dict["Incident Year"].append(point["x"])
            procedure_dict["Metric Summary"].append(("${:,.2f}".format(point["x"])))

    # Display all procedures at selected location
    location_select = []

    if prop_id == "geo-map" and geo_select is not None:
        for point in geo_select["points"]:
            location = point["customdata"][0]
            location_select.append(location)

        state_raw_data = df_shark[df_shark['State'] == state_select]
        location_filtered = state_raw_data[
            state_raw_data["Location"].isin(location_select)
        ]

        for i in range(len(location_filtered)):
            procedure_dict["Shark Species"].append(
                location_filtered.iloc[i]["Shark.common.name"]
            )
            procedure_dict["Location"].append(
                location_filtered.iloc[i]["Location"]
            )
            procedure_dict["Incident Year"].append(
                location_filtered.iloc[i]["Incident.year"]
            )
            procedure_dict["Metric Summary"].append(
                "${:,.2f}".format(location_filtered.iloc[0][cost_select])
            )

    procedure_data_df = pd.DataFrame(data=procedure_dict)

    return dash_table.DataTable(
        id="procedure-stats-table",
        columns=[{"name": i, "id": i} for i in procedure_dict.keys()],
        data=procedure_data_df.to_dict("records"),
        filter_action="native",
        sort_action="native",
        style_cell={
            "textOverflow": "ellipsis",
            "background-color": "#242a3b",
            "color": "#7b7d8d",
        },
        sort_mode="multi",
        page_size=5,
        style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "2px 12px 0px 12px"},
    )

# Create a mapping from state abbreviations to state codes
state_code_mapping = {
    "NSW": "1",  # New South Wales
    "VIC": "2",  # Victoria
    "QLD": "3",  # Queensland
    "WA": "4",   # Western Australia
    "SA": "5",   # South Australia
    "TAS": "6",  # Tasmania
    "NT": "7",   # Northern Territory
    "ACT": "8",  # Australian Capital Territory
}

@app.callback(
    Output("geo-map", "figure"),
    [Input("state-select", "value"), Input("metric-select", "value")]
)
def update_choropleth_map(state_select, selected_metric):
    # Map the selected state abbreviation to its corresponding state code
    state_code = state_code_mapping.get(state_select)

    # Filter the DataFrame based on the selected state abbreviation
    filtered_data = df_shark[df_shark['State'] == state_select]

    # Check if filtered_data is empty
    if filtered_data.empty:
        return {
            "data": [],
            "layout": go.Layout(
                title="No data available for the selected state",
                paper_bgcolor="#171b26",
                plot_bgcolor="#171b26",
            ),
        }

    # Generate the choropleth plot
    fig = px.choropleth(
        data_frame=filtered_data,
        geojson=aus_states_geojson,
        locations="State",  # Column in DataFrame
        featureidkey="properties.STATE_CODE",  # Match GeoJSON key to column
        color=selected_metric,
        hover_data=["Location", selected_metric],
        color_continuous_scale=px.colors.sequential.YlOrRd,
        labels={selected_metric: "Metric Value"},
    )

    # Update layout for better 
    fig.update_geos(
        fitbounds="locations",
        visible=True,  # Ensure the map is visible
        bgcolor="#171b26",  # Background color
        projection_type="mercator",  # Set projection to Mercator
        center={"lat": -25.2744, "lon": 133.7751},  # Center on Australia
        scope="world"  # Set the scope to Asia to focus on Australia
    )

    fig.update_layout(
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        title_text="Shark Incidents in Australian States",
        title_x=0.5,
        paper_bgcolor="#171b26",  # Match Dash's dark theme
    )

    return fig



if __name__ == "__main__":
    app.run_server(debug=True)