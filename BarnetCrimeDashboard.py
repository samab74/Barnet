#!/usr/bin/env python
# coding: utf-8

# In[3]:


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

# Load the GeoJSON files from URLs
try:
    lsoa_geojson_data = requests.get('https://github.com/samab74/Barnet-Dashboard/raw/main/lsoa_with_crime_counts.geojson').json()
    wards_geojson_data = requests.get('https://raw.githubusercontent.com/samab74/Barnet-Dashboard/main/OSBoundaryLine%20-%20BarnetWards.geojson').json()
except Exception as e:
    print(f"Error loading GeoJSON files: {e}")

# Convert GeoJSON to GeoDataFrames
try:
    lsoa_gdf = gpd.GeoDataFrame.from_features(lsoa_geojson_data["features"])
    wards_gdf = gpd.GeoDataFrame.from_features(wards_geojson_data["features"])

    # Ensure both GeoDataFrames use the same CRS (Coordinate Reference System)
    lsoa_gdf = lsoa_gdf.set_crs("EPSG:4326")
    wards_gdf = wards_gdf.set_crs("EPSG:4326")

    # Perform spatial join to map LSOAs to wards using the 'predicate' parameter
    lsoa_wards_gdf = gpd.sjoin(lsoa_gdf, wards_gdf, how="left", predicate="intersects")

    # Convert the result back to a DataFrame
    df = pd.DataFrame(lsoa_wards_gdf.drop(columns='geometry'))
except Exception as e:
    print(f"Error processing GeoDataFrames: {e}")

# Load crime dataset from URL
try:
    crime_data = pd.read_csv('https://raw.githubusercontent.com/samab74/Barnet-Dashboard/main/barnet_crimes.csv')
except Exception as e:
    print(f"Error loading crime data: {e}")

# Extract latitude and longitude
def extract_lat_lon(location_str):
    try:
        location_dict = ast.literal_eval(str(location_str).replace('null', 'None'))
        latitude = float(location_dict.get('latitude', None))
        longitude = float(location_dict.get('longitude', None))
        return pd.Series([latitude, longitude])
    except (ValueError, SyntaxError):
        return pd.Series([None, None])

try:
    crime_data[['latitude', 'longitude']] = crime_data['location'].apply(extract_lat_lon)
    filtered_crime_data = crime_data.dropna(subset=['latitude', 'longitude'])
    crime_categories = ['All Crime'] + filtered_crime_data['category'].unique().tolist()
except Exception as e:
    print(f"Error processing crime data: {e}")

# Continue with the rest of your code as is...


# Extract latitude and longitude
def extract_lat_lon(location_str):
    try:
        location_dict = ast.literal_eval(str(location_str).replace('null', 'None'))
        latitude = float(location_dict.get('latitude', None))
        longitude = float(location_dict.get('longitude', None))
        return pd.Series([latitude, longitude])
    except (ValueError, SyntaxError):
        return pd.Series([None, None])

try:
    crime_data[['latitude', 'longitude']] = crime_data['location'].apply(extract_lat_lon)
    filtered_crime_data = crime_data.dropna(subset=['latitude', 'longitude'])
    crime_categories = ['All Crime'] + filtered_crime_data['category'].unique().tolist()
except Exception as e:
    print(f"Error processing crime data: {e}")

# Create the dictionary for renaming columns
short_names = {
    'FeatureID': 'Feat ID',
    'LSOA21CD': 'LSOA Code',
    'LSOA21NM': 'LSOA Name',
    'Lower layer Super Output Areas Code': 'LSOA Code',
    'Lower layer Super Output Areas_deprivation': 'LSOA Deprivation',
    'Does not apply_deprivation': 'No Deprivation',
    'Household is deprived in four dimensions': 'Deprived 4D',
    'Household is deprived in one dimension': 'Deprived 1D',
    'Household is deprived in three dimensions': 'Deprived 3D',
    'Household is deprived in two dimensions': 'Deprived 2D',
    'Household is not deprived in any dimension': 'Not Deprived',
    'Does not apply_economic': 'No Economic',
    'Economically active (excluding full-time students): In employment: Employee: Full-time': 'Econ Active FT',
    'Economically active (excluding full-time students): In employment: Employee: Part-time': 'Econ Active PT',
    'Economically active (excluding full-time students): In employment: Self-employed with employees: Full-time': 'Econ Self-Empl FT',
    'Economically active (excluding full-time students): In employment: Self-employed with employees: Part-time': 'Econ Self-Empl PT',
    'Economically active (excluding full-time students): In employment: Self-employed without employees: Full-time': 'Econ Self-NoEmp FT',
    'Economically active (excluding full-time students): In employment: Self-employed without employees: Part-time': 'Econ Self-NoEmp PT',
    'Economically active (excluding full-time students): Unemployed: Seeking work or waiting to start a job already obtained: Available to start working within 2 weeks': 'Econ Unemp Seek',
    'Economically active and a full-time student: In employment: Employee: Full-time': 'Econ Active FT Student Emp FT',
    'Economically active and a full-time student: In employment: Employee: Part-time': 'Econ Active FT Student Emp PT',
    'Economically active and a full-time student: In employment: Self-employed with employees: Full-time': 'Econ Active FT Student SelfEmp FT',
    'Economically active and a full-time student: In employment: Self-employed with employees: Part-time': 'Econ Active FT Student SelfEmp PT',
    'Economically active and a full-time student: In employment: Self-employed without employees: Full-time': 'Econ Active FT Student NoEmp FT',
    'Economically active and a full-time student: Unemployed: Seeking work or waiting to start a job already obtained: Available to start working within 2 weeks': 'Econ Active FT Student Unemp',
    'Economically inactive: Long-term sick or disabled': 'Econ Inactive Sick',
    'Economically inactive: Looking after home or family': 'Econ Inactive Home',
    'Economically inactive: Other': 'Econ Inactive Other',
    'Economically inactive: Retired': 'Econ Inactive Retired',
    'Economically inactive: Student': 'Econ Inactive Student',
    'Apprenticeship': 'Apprenticeship',
    'Does not apply': 'No Apply',
    'Level 1 and entry level qualifications: 1 to 4 GCSEs grade A* to C, Any GCSEs at other grades, O levels or CSEs (any grades), 1 AS level, NVQ level 1, Foundation GNVQ, Basic or Essential Skills': 'Qual Level 1',
    'Level 2 qualifications: 5 or more GCSEs (A* to C or 9 to 4), O levels (passes), CSEs (grade 1), School Certification, 1 A level, 2 to 3 AS levels, VCEs, Intermediate or Higher Diploma, Welsh Baccalaureate Intermediate Diploma, NVQ level 2, Intermediate GNVQ, City and Guilds Craft, BTEC First or General Diploma, RSA Diploma': 'Qual Level 2',
    'Level 3 qualifications: 2 or more A levels or VCEs, 4 or more AS levels, Higher School Certificate, Progression or Advanced Diploma, Welsh Baccalaureate Advance Diploma, NVQ level 3; Advanced GNVQ, City and Guilds Advanced Craft, ONC, OND, BTEC National, RSA Advanced Diploma': 'Qual Level 3',
    'Level 4 qualifications or above: degree (BA, BSc), higher degree (MA, PhD, PGCE), NVQ level 4 to 5, HNC, HND, RSA Higher Diploma, BTEC Higher level, professional qualifications (for example, teaching, nursing, accountancy)': 'Qual Level 4+',
    'No qualifications': 'No Qual',
    'Other: vocational or work-related qualifications, other qualifications achieved in England or Wales, qualifications achieved outside England or Wales (equivalent not stated or unknown)': 'Other Qual',
    'Asian, Asian British or Asian Welsh: Bangladeshi': 'Asian Bangladeshi',
    'Asian, Asian British or Asian Welsh: Chinese': 'Asian Chinese',
    'Asian, Asian British or Asian Welsh: Indian': 'Asian Indian',
    'Asian, Asian British or Asian Welsh: Other Asian': 'Asian Other',
    'Asian, Asian British or Asian Welsh: Pakistani': 'Asian Pakistani',
    'Black, Black British, Black Welsh, Caribbean or African: African': 'Black African',
    'Black, Black British, Black Welsh, Caribbean or African: Caribbean': 'Black Caribbean',
    'Black, Black British, Black Welsh, Caribbean or African: Other Black': 'Black Other',
    'Does not apply_ethnicity': 'No Ethnicity',
    'Mixed or Multiple ethnic groups: Other Mixed or Multiple ethnic groups': 'Mixed Other',
    'Mixed or Multiple ethnic groups: White and Asian': 'Mixed White Asian',
    'Mixed or Multiple ethnic groups: White and Black African': 'Mixed White Black African',
    'Mixed or Multiple ethnic groups: White and Black Caribbean': 'Mixed White Black Caribbean',
    'Other ethnic group: Any other ethnic group': 'Other Ethnic',
    'Other ethnic group: Arab': 'Ethnic Arab',
    'White: English, Welsh, Scottish, Northern Irish or British': 'White British',
    'White: Gypsy or Irish Traveller': 'White Gypsy/Traveller',
    'White: Irish': 'White Irish',
    'White: Other White': 'White Other',
    'White: Roma': 'White Roma',
    'Female': 'Female',
    'Male': 'Male',
    'Population': 'Population',
    'total_crime': 'Total Crime'
}

# List of variables to exclude
variables_to_exclude = [
    'FeatureID', 'LSOA21CD', 'LSOA21NM', 
    'Lower layer Super Output Areas Code', 'Lower layer Super Output Areas_deprivation',
    'Does not apply_deprivation', 'index_right', 'ONSWardCode', 'WardName'
]

# Initialize the Dash app
app = Dash(__name__)

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
                        {'label': short_names.get(var, var), 'value': var} 
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
                        {'label': short_names.get(var, var), 'value': var} 
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
                        {'label': short_names.get(var, var), 'value': var} 
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

def fetch_crime_data(date):
    coordinates = "51.55519092818953,-0.30557383443798025:51.670170250593905,-0.30557383443798025:51.670170250593905,-0.12909406402138046:51.55519092818953,-0.12909406402138046:51.55519092818953,-0.30557383443798025"
    url = f"https://data.police.uk/api/crimes-street/all-crime?poly={coordinates}&date={date}"
    response = requests.get(url)
    if response.status_code == 200:
        crimes = response.json()
        if crimes:
            df = pd.DataFrame(crimes)
            df[['latitude', 'longitude']] = df['location'].apply(extract_lat_lon)
            return df.dropna(subset=['latitude', 'longitude'])
    return pd.DataFrame()

def extract_lat_lon(location_str):
    try:
        location_dict = ast.literal_eval(str(location_str).replace('null', 'None'))
        latitude = float(location_dict.get('latitude', None))
        longitude = float(location_dict.get('longitude', None))
        return pd.Series([latitude, longitude])
    except (ValueError, SyntaxError):
        return pd.Series([None, None])

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
    
            # Updated Legend
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

@app.callback(
    Output('bar-chart', 'figure'),
    Output('ward-bar-chart', 'figure'),
    [Input('bar-variable-dropdown', 'value')]
)
def update_bar_charts(selected_variable):
    # Ensure the selected variable exists in the dataframe
    if selected_variable not in df.columns:
        raise ValueError(f"Selected variable {selected_variable} does not exist in the DataFrame")

    # Sort the dataframe by the selected variable
    sorted_df = df.sort_values(by=selected_variable, ascending=False)
    
    # Update LSOA bar chart
    lsoa_fig = px.bar(
        sorted_df,
        x='LSOA21NM',
        y=selected_variable,
        title=f'{short_names.get(selected_variable, selected_variable)} by LSOA',
        labels={'LSOA21NM': 'LSOA Name', selected_variable: short_names.get(selected_variable, selected_variable)},
        custom_data=['WardName']  # Include ward name in the custom data
    )
    lsoa_fig.update_layout(
        xaxis_title='LSOA Name',
        yaxis_title=short_names.get(selected_variable, selected_variable),
        xaxis={'categoryorder': 'total descending'},
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40},
        height=600
    )
    
    # Update hover template to include ward information
    lsoa_fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Value: %{y}<br>Ward: %{customdata[0]}"
    )
    
    # Update Ward bar chart
    ward_totals = df.groupby('WardName')[selected_variable].sum().reset_index()
    ward_fig = px.bar(
        ward_totals,
        x='WardName',
        y=selected_variable,
        title=f'Total {short_names.get(selected_variable, selected_variable)} by Ward',
        labels={'WardName': 'Ward Name', selected_variable: short_names.get(selected_variable, selected_variable)}
    )
    ward_fig.update_layout(
        xaxis_title='Ward Name',
        yaxis_title=short_names.get(selected_variable, selected_variable),
        xaxis={'categoryorder': 'total descending'},
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40},
        height=600
    )
    
    return lsoa_fig, ward_fig

@app.callback(
    Output('map', 'srcDoc'),
    [Input('map-variable-dropdown', 'value')]
)
def update_variable_map(selected_variable):
    m = folium.Map(location=[51.6, -0.2], zoom_start=12)
    
    if selected_variable:
        values = [feature['properties'][selected_variable] for feature in lsoa_geojson_data['features']]
        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        colors = ['#800026', '#BD0026', '#E31A1C', '#FC4E2A', '#FD8D3C', '#FEB24C', '#FED976', '#FFEDA0', '#FFFFCC', '#FFFFFF']
        thresholds = [np.percentile(values, p) for p in percentiles]
        
        def get_color(value):
            for i, threshold in enumerate(thresholds):
                if value <= threshold:
                    return colors[i]
            return colors[-1]
        
        folium.GeoJson(
            lsoa_geojson_data,
            name='LSOA Variable',
            style_function=lambda x: {
                'fillColor': get_color(x['properties'][selected_variable]),
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.5,
            },
            tooltip=folium.GeoJsonTooltip(fields=['LSOA21NM', selected_variable], aliases=['LSOA:', short_names.get(selected_variable, selected_variable)])
        ).add_to(m)
        
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 250px; height: auto; 
                    border:2px solid grey; z-index:9999; font-size:14px;
                    background-color:white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                    ">
        <h4 style="margin-top: 5px; text-align: center;">Legend</h4>
        <ul style="list-style-type:none; padding-left: 0;">
        '''
        
        for i, percentile in enumerate(percentiles):
            color = colors[i]
            legend_html += f'<li><span style="background:{color}; width: 20px; height: 20px; display: inline-block;"></span> Top {percentile}%</li>'
        
        legend_html += '</ul></div>'
        
        m.get_root().html.add_child(folium.Element(legend_html))
    
    ward_style_function = lambda x: {
        'fillColor': 'none',
        'color': 'black',
        'weight': 3,
        'fillOpacity': 0.5,
    }
    
    folium.GeoJson(
        wards_geojson_data,
        name='Electoral Wards',
        style_function=ward_style_function,
        tooltip=folium.GeoJsonTooltip(fields=['WardName'], aliases=['Ward:'])
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    map_file_path = 'lsoa_variable_map.html'
    m.save(map_file_path)
    
    with open(map_file_path, 'r') as f:
        html_map = f.read()
    
    return html_map

@app.callback(
    Output('lsoa-info', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('lsoa-input', 'value'), State('map-variable-dropdown', 'value')]
)
def display_lsoa_info(n_clicks, lsoa_name, selected_variable):
    if n_clicks > 0 and lsoa_name:
        # Remove any leading/trailing spaces and convert to upper case for consistency
        lsoa_name = lsoa_name.strip().upper()
        
        # Filter the DataFrame for the given LSOA name
        lsoa_data = df[df['LSOA21NM'].str.contains(lsoa_name, case=False, na=False)]
        
        if not lsoa_data.empty:
            value = lsoa_data[selected_variable].values[0]

            # Remove duplicates
            df_unique = df.drop_duplicates(subset=['LSOA21NM'])

            # Compute the rank
            df_sorted = df_unique.sort_values(by=selected_variable, ascending=False).reset_index(drop=True)
            df_sorted['rank'] = df_sorted[selected_variable].rank(method='min', ascending=False)
            rank = df_sorted[df_sorted['LSOA21NM'].str.contains(lsoa_name, case=False, na=False)]['rank'].values[0]

            total_lsoas = df_unique['LSOA21NM'].nunique()  # Correctly count the number of unique LSOAs
            ward_name = lsoa_data['WardName'].values[0]  # Get ward name

            return [
                html.H4(f"Information for {lsoa_name}:"),
                html.P(f"Value of {short_names.get(selected_variable, selected_variable)}: {value}"),
                html.P(f"Rank: {int(rank)} out of {total_lsoas} LSOAs"),
                html.P(f"Ward: {ward_name}")  # Display ward name
            ]
        else:
            return html.P(f"No information found for LSOA: {lsoa_name}")
    return ""

@app.callback(
    Output('correlation-scatter-plot', 'figure'),
    [Input('correlation-variable-dropdown', 'value'), Input('correlation-lsoa-dropdown', 'value')]
)
def update_correlation_scatter_plot(selected_variable, selected_ward):
    # Filter numeric data
    numeric_df = df.select_dtypes(include=[np.number])
    
    # If a specific ward is selected, filter the data for that ward
    if selected_ward and selected_ward != "All Barnet":
        ward_data = df[df['WardName'] == selected_ward]
        if not ward_data.empty:
            numeric_df = ward_data.select_dtypes(include=[np.number])

    # Compute correlations
    correlation = numeric_df.corr()[selected_variable].sort_values(ascending=False).reset_index()
    correlation = correlation.rename(columns={'index': 'Variable', selected_variable: 'Correlation'})
    top_correlation = correlation.head(10).copy()

    # Determine the layout of the subplots dynamically
    num_plots = len(top_correlation)
    rows = (num_plots // 5) + (1 if num_plots % 5 else 0)
    cols = min(num_plots, 5)

    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[short_names.get(var, var) for var in top_correlation['Variable']],
        horizontal_spacing=0.1,  # Adjust horizontal spacing
        vertical_spacing=0.3  # Adjust vertical spacing
    )
    
    for i, variable in enumerate(top_correlation['Variable']):
        row = i // 5 + 1
        col = i % 5 + 1
        fig.add_trace(
            go.Scatter(
                x=numeric_df[variable],
                y=numeric_df[selected_variable],
                mode='markers',
                name=short_names.get(variable, variable)
            ),
            row=row,
            col=col
        )
    
    fig.update_layout(
        title=f'Scatter Plots of Top Correlations with {short_names.get(selected_variable, selected_variable)} in {selected_ward}',
        height=400 * rows,
        showlegend=False,
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40},
    )

    for i, variable in enumerate(top_correlation['Variable']):
        fig['layout'][f'xaxis{i+1}'].update(title=short_names.get(variable, variable), title_font_size=8)
        fig['layout'][f'yaxis{i+1}'].update(title=short_names.get(selected_variable, selected_variable), title_font_size=8)
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8060)  # Change port to 8060 or any other available port


# https://raw.githubusercontent.com/samab74/Barnet-Dashboard/main/OSBoundaryLine%20-%20BarnetWards.geojson
# https://raw.githubusercontent.com/samab74/Barnet-Dashboard/main/barnet_crimes.csv
# https://github.com/samab74/Barnet-Dashboard/raw/main/lsoa_with_crime_counts.geojson
# 

# In[ ]:




