import os
import json
import pandas as pd
import ast
import geopandas as gpd
import folium
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from folium.plugins import HeatMap, MarkerCluster
from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to fetch crime data
def fetch_crime_data(date):
    coordinates = "51.55519092818953,-0.30557383443798025:51.670170250593905,-0.30557383443798025:51.670170250593905,-0.12909406402138046:51.55519092818953,-0.12909406402138046:51.55519092818953,-0.30557383443798025"
    url = f"https://data.police.uk/api/crimes-street/all-crime?poly={coordinates}&date={date}"
    try:
        response = requests.get(url)
        logger.info(f"API URL: {url}")
        logger.info(f"API Response Status Code: {response.status_code}")
        if response.status_code == 200:
            crimes = response.json()
            if crimes:
                df = pd.DataFrame(crimes)
                df[['latitude', 'longitude']] = df['location'].apply(extract_lat_lon)
                return df.dropna(subset=['latitude', 'longitude'])
        else:
            logger.error(f"Error fetching crime data: {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Exception occurred while fetching crime data: {e}")
    return pd.DataFrame()

def extract_lat_lon(location_str):
    try:
        location_dict = ast.literal_eval(str(location_str).replace('null', 'None'))
        latitude = float(location_dict.get('latitude', None))
        longitude = float(location_dict.get('longitude', None))
        return pd.Series([latitude, longitude])
    except (ValueError, SyntaxError):
        return pd.Series([None, None])

app = Dash(__name__)
server = app.server

@app.callback(
    [Output('crime-map', 'srcDoc'),
     Output('crime-category-dropdown', 'options')],
    [Input('submit-date-button', 'n_clicks')],
    [State('date-input', 'value'), State('crime-category-dropdown', 'value')]
)
def update_crime_map(n_clicks, date_input, selected_category):
    if n_clicks > 0 and date_input:
        crime_data = fetch_crime_data(date_input)
        crime_categories = ['All Crime'] + crime_data['category'].unique().tolist()
        dropdown_options = [{'label': category, 'value': category} for category in crime_categories]

        if selected_category == 'All Crime':
            filtered_data_by_category = crime_data
        else:
            filtered_data_by_category = crime_data[crime_data['category'] == selected_category]

        if not filtered_data_by_category.empty:
            center_lat, center_lon = filtered_data_by_category['latitude'].mean(), filtered_data_by_category['longitude'].mean()
            map_barnet = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            heat_data = [[row['latitude'], row['longitude']] for idx, row in filtered_data_by_category.iterrows()]
            heatmap_layer = HeatMap(heat_data, name='Crime Heatmap').add_to(map_barnet)
            marker_cluster = MarkerCluster(name='Crime Markers').add_to(map_barnet)

            def get_marker_color(crime_category):
                category_colors = {
                    'anti-social-behaviour': 'blue',
                    'burglary': 'purple',
                    'criminal-damage-arson': 'orange',
                    'drugs': 'darkred',
                    'other-theft': 'green',
                    'possession-of-weapons': 'cadetblue',
                    'public-order': 'lightred',
                    'robbery': 'darkpurple',
                    'shoplifting': 'lightblue',
                    'theft-from-the-person': 'darkgreen',
                    'vehicle-crime': 'black',
                    'violent-crime': 'red',
                    'other-crime': 'gray'
                }
                return category_colors.get(crime_category, 'black')

            for idx, row in filtered_data_by_category.iterrows():
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=f'Category: {row["category"]}',
                    icon=folium.Icon(color=get_marker_color(row['category']))
                ).add_to(marker_cluster)

            legend_html = '''
                <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 250px; height: auto; 
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                ">
                <h4 style="margin-top: 5px; text-align: center;">Crime Category Legend</h4>
                <ul style="list-style-type:none; padding-left: 0;">
                    <li><span style="background-color: blue; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Anti-Social Behaviour</li>
                    <li><span style="background-color: purple; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Burglary</li>
                    <li><span style="background-color: orange; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Criminal Damage & Arson</li>
                    <li><span style="background-color: darkred; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Drugs</li>
                    <li><span style="background-color: green; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Other Theft</li>
                    <li><span style="background-color: cadetblue; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Possession of Weapons</li>
                    <li><span style="background-color: lightred; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Public Order</li>
                    <li><span style="background-color: darkpurple; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Robbery</li>
                    <li><span style="background-color: lightblue; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Shoplifting</li>
                    <li><span style="background-color: darkgreen; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Theft from the Person</li>
                    <li><span style="background-color: black; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Vehicle Crime</li>
                    <li><span style="background-color: red; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Violent Crime</li>
                    <li><span style="background-color: gray; display: inline-block; width: 12px; height: 12px; margin-right: 5px;"></span> Other Crime</li>
                </ul>
                </div>
                '''
            map_barnet.get_root().html.add_child(folium.Element(legend_html))
            crime_map_file_path = 'Barnet_Crime_Hotspots_Custom.html'
            map_barnet.save(crime_map_file_path)

            with open(crime_map_file_path, 'r') as f:
                html_map = f.read()
            return html_map, dropdown_options
        else:
            return "<h3>No crime data available for the selected date.</h3>", dropdown_options
    return "", [{'label': 'All Crime', 'value': 'All Crime'}]

app.layout = html.Div([
    html.H1("LSOA Dashboard", style={'textAlign': 'center', 'padding': '10px'}),
    dcc.Tabs([
        dcc.Tab(label='LSOA Variable Heatmap', children=[
            html.Div([
                html.H2("LSOA Variable Heatmap", style={'textAlign': 'center', 'padding': '10px'}),
                html.Label("Select Variable for Map:"),
                dcc.Dropdown(
                    id='map-variable-dropdown',
                    options=[
                        {'label': var, 'value': var} 
                        for var in df.columns if var not in variables_to_exclude
                    ],
                    value='total_crime',  # Set default value
                    clearable=False
                ),
                html.Iframe(id='map', width='100%', height='600', style={'border': 'none'}),
                html.Br(),
                html.Label("Enter LSOA Name:"),
                dcc.Input(id='lsoa-input', type='text', placeholder='Enter LSOA name', style={'width': '50%'}),
                html.Button(id='submit-button', n_clicks=0, children='Submit', style={'margin-left': '10px'}),
                html.Div(id='lsoa-info', style={'margin-top': '20px'})
            ], style={'padding': '10px', 'border': '1px solid #ccc', 'border-radius': '5px', 'margin-bottom': '20px'}),
        ]),
        dcc.Tab(label='Bar Charts', children=[
            html.Div([
                html.H2("Bar Charts", style={'textAlign': 'center', 'padding': '10px'}),
                html.Label("Select Variable for Bar Charts:"),
                dcc.Dropdown(
                    id='bar-variable-dropdown',
                    options=[
                        {'label': var, 'value': var} 
                        for var in df.columns if var not in variables_to_exclude
                    ],
                    value='total_crime',  # Set default value
                    clearable=False
                ),
                dcc.Graph(id='bar-chart'),
                dcc.Graph(id='ward-bar-chart')
            ], style={'padding': '10px', 'border': '1px solid #ccc', 'border-radius': '5px', 'margin-bottom': '20px'}),
        ]),
        dcc.Tab(label='Barnet Crime Heatmap', children=[
            html.Div([
                html.H2("Barnet Crime Heatmap", style={'textAlign': 'center', 'padding': '10px'}),
                html.Label("Select Date:"),
                dcc.Input(id='date-input', type='text', placeholder='Enter date (YYYY-MM)', style={'width': '50%'}),
                html.Button(id='submit-date-button', n_clicks=0, children='Submit', style={'margin-left': '10px'}),
                html.Label("Select Crime Category:"),
                dcc.Dropdown(
                    id='crime-category-dropdown',
                    options=[{'label': category, 'value': category} for category in crime_categories],
                    value='All Crime',  # Set default value to 'All Crime'
                    clearable=False
                ),
                html.Iframe(id='crime-map', width='100%', height='600', style={'border': 'none'}),
            ], style={'padding': '10px', 'border': '1px solid #ccc', 'border-radius': '5px', 'margin-bottom': '20px'}),
        ]),
        dcc.Tab(label='Correlations', children=[
            html.Div([
                html.H2("Correlations with Total Crime", style={'textAlign': 'center', 'padding': '10px'}),
                dcc.Dropdown(
                    id='correlation-variable-dropdown',
                    options=[
                        {'label': var, 'value': var} 
                        for var in df.columns if var not in variables_to_exclude
                    ],
                    value='total_crime',  # Set default value
                    clearable=False
                ),
                html.Br(),
                html.Label("Select Ward:"),
                dcc.Dropdown(
                    id='correlation-lsoa-dropdown',
                    options=[
                        {'label': 'All Barnet', 'value': 'All Barnet'}] + 
                        [{'label': ward, 'value': ward} for ward in df['WardName'].unique()
                    ],
                    value='All Barnet',  # Default value
                    clearable=False
                ),
                dcc.Graph(id='correlation-scatter-plot'),
            ], style={'padding': '10px', 'border': '1px solid #ccc', 'border-radius': '5px', 'margin-bottom': '20px'}),
        ]),
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True, port=8060)





