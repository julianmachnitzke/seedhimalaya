from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, send_file; 
import geopandas as gpd
from shapely.geometry import Point
import requests
import pandas as pd
from rtree import index as index_func
import os
import json
import shutil
from werkzeug.utils import secure_filename
import zipfile
from datetime import datetime 
import subprocess
import numpy as np
import matplotlib.pyplot as plt

scripts_dir = os.path.dirname(__file__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(scripts_dir, '..', 'urbs_master', 'Input', 'json')
app.secret_key = 'your_secret_key'  # Cambia questa stringa con una chiave segreta sicura

# Load data from Excel files
demand_data_folder = 'demand_data'
poor_household_data = pd.read_excel(os.path.join(demand_data_folder, 'poor_household.xlsx'))
rich_household_data = pd.read_excel(os.path.join(demand_data_folder, 'rich_household.xlsx'))
average_household_data = pd.read_excel(os.path.join(demand_data_folder, 'average_household.xlsx'))
hospital_data = pd.read_excel(os.path.join(demand_data_folder, 'hospital.xlsx'))
school_data = pd.read_excel(os.path.join(demand_data_folder, 'school.xlsx'))

# Create a new blank Excel file if it does not exist
new_excel_file = 'new_total_demand.xlsx'
if not os.path.exists(new_excel_file):
    pd.DataFrame(columns=['Total']).to_excel(new_excel_file, index=False)

# Function to update new Excel file with intermediate results
def update_new_excel_file():
    try:
        new_data = pd.read_excel(new_excel_file)
        print("Loaded existing new_total_demand.xlsx file")
    except ValueError:  # Se il file è vuoto
        new_data = pd.DataFrame(columns=['Total'])
        print("Created new DataFrame for new_total_demand.xlsx")

    max_rows = 8762
    commodities = session.get('commodities', {})
    
    total_series = pd.Series([0] * max_rows)
    for commodity, count in commodities.items():
        print(f"Processing {commodity} with count {count}")
        if commodity == 'Low-income Household':
            total_series += poor_household_data.iloc[:, 0].fillna(0) * count
        elif commodity == 'High-income Household':
            total_series += rich_household_data.iloc[:, 0].fillna(0) * count
        elif commodity == 'Primary Health-Care Center':
            total_series += hospital_data.iloc[:, 0].fillna(0) * count
        elif commodity == 'School':
            total_series += school_data.iloc[:, 0].fillna(0) * count
        elif commodity == 'Average-income Household':
            total_series += average_household_data.iloc[:, 0].fillna(0) * count

    print("Total series calculated:", total_series.head())

    if 'Total' in new_data.columns:
        new_data['Total'] = total_series
    else:
        new_data = pd.DataFrame({'Total': total_series})

    new_data.to_excel(new_excel_file, index=False)
    print("Updated new_excel_file:", new_data.head())

def calculate_total_demand():
    update_new_excel_file()
    new_data = pd.read_excel(new_excel_file)
    total_demand = new_data['Total'].sum()
    print("Total demand calculated:", total_demand)
    return total_demand

@app.route('/get_chart_data', methods=['GET'])
def get_chart_data():
    new_data = pd.read_excel(new_excel_file)
    labels = [f't{i}' for i in range(len(new_data))]
    values = new_data['Total'].tolist()
    return jsonify({'labels': labels, 'values': values})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/demand')
def demand():
    return render_template('demand.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/runurbs')
def runurbs():
    return render_template('runurbs.html')

@app.route('/urbsresults')
def urbsresults():
    return render_template('urbsresult.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    commodity = request.form['commodity']
    quantity = int(request.form['quantity'])
    
    if 'commodities' not in session:
        session['commodities'] = {}
    if commodity in session['commodities']:
        session['commodities'][commodity] += quantity
    else:
        session['commodities'][commodity] = quantity
    
    print("Session commodities updated:", session['commodities'])
    total_demand = calculate_total_demand()
    session['total_demand'] = total_demand
    
    return jsonify({'total_demand': total_demand})

def sum_first_column(file_path):
    df = pd.read_excel(file_path)
    return df.iloc[:, 0].sum()

@app.route('/upload_and_sum', methods=['GET', 'POST'])
def upload_and_sum():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No files loaded'
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected'
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            sum_result = sum_first_column(file_path)
            return render_template('demand.html', sum_result=sum_result)
    
    return render_template('demand.html')

@app.route('/generate_json')
def generate_json():
    if os.path.exists(new_excel_file):
        data = pd.read_excel(new_excel_file)
    elif 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            data = pd.read_excel(file_path)
    else:
        return jsonify({'error': 'No files available for JSON generation'})

    json_list = []
    for i, total in enumerate(data['Total']):
        json_list.append({
            "support_timeframe": 2020,
            "t": i,
            "Mid": {
                "Elec": total
            }
        })

    json_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'demand.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(json_list, json_file, ensure_ascii=False, indent=4)

    return redirect(url_for('process'))

@app.route('/reset_total_series', methods=['POST'])
def reset_total_series():
    # Reset the session commodities
    session['commodities'] = {}

    # Clear the Excel file
    pd.DataFrame(columns=['Total']).to_excel(new_excel_file, index=False)
    print("Total series and new_total_demand.xlsx have been reset")

    return jsonify({'status': 'success'})


@app.route('/process')
def process():
    return render_template('process.html')

# Function to add data to JSON file without overwriting
def add_data_to_json(data, json_filename):
    json_path = os.path.join(os.getcwd(), json_filename)

    # Check if the JSON file exists
    if not os.path.exists(json_path):
        # Create an empty JSON file if it doesn't exist
        with open(json_path, 'w') as json_file:
            json.dump([], json_file)

    with open(json_path, 'r') as json_file:
        try:
            existing_data = json.load(json_file)
        except json.JSONDecodeError:
            existing_data = []

    existing_data.append(data)

    with open(json_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

# Route for the hydroelectric process
@app.route('/process_hydro', methods=['POST'])
def process_hydro():
    if request.json.get('action') == 'hydro':
        try:
            process_path = os.path.join(os.getcwd(), 'process.xlsx')
            demand_path = os.path.join(os.getcwd(), 'processdemand.xlsx')

            if not os.path.exists(process_path):
                return jsonify({'status': 'failure', 'error': 'process.xlsx not found'})
            if not os.path.exists(demand_path):
                return jsonify({'status': 'failure', 'error': 'processdemand.xlsx not found'})

            df_process = pd.read_excel(process_path)
            df_demand = pd.read_excel(demand_path)

            first_row_process = df_process.iloc[0].to_dict()  # Select the 7th row from process.xlsx
            first_row_demand = df_demand.iloc[0].to_dict()    # Select the 1st row from processdemand.xlsx
            fifth_row_demand = df_demand.iloc[1].to_dict()
            
            add_data_to_json(first_row_process, 'process.json')
            add_data_to_json(first_row_demand, 'processdemand.json')
            add_data_to_json(fifth_row_demand, 'processdemand.json')

            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'failure', 'error': str(e)})
    return jsonify({'status': 'failure', 'error': 'Invalid action'})

# Route for the solar process
@app.route('/process_solar', methods=['POST'])
def process_solar():
    if request.json.get('action') == 'solar':
        try:
            process_path = os.path.join(os.getcwd(), 'process.xlsx')
            demand_path = os.path.join(os.getcwd(), 'processdemand.xlsx')

            if not os.path.exists(process_path):
                return jsonify({'status': 'failure', 'error': 'process.xlsx not found'})
            if not os.path.exists(demand_path):
                return jsonify({'status': 'failure', 'error': 'processdemand.xlsx not found'})

            df_process = pd.read_excel(process_path)
            df_demand = pd.read_excel(demand_path)

            first_row_process = df_process.iloc[1].to_dict()  # Select the 2nd row from process.xlsx
            first_row_demand = df_demand.iloc[4].to_dict()    # Select the 1st row from processdemand.xlsx
            fifth_row_demand = df_demand.iloc[5].to_dict()    # Select the 5th row from processdemand.xlsx

            add_data_to_json(first_row_process, 'process.json')
            add_data_to_json(first_row_demand, 'processdemand.json')
            add_data_to_json(fifth_row_demand, 'processdemand.json')

            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'failure', 'error': str(e)})
    return jsonify({'status': 'failure', 'error': 'Invalid action'})

# Route for the wind process
@app.route('/process_wind', methods=['POST'])
def process_wind():
    if request.json.get('action') == 'wind':
        try:
            process_path = os.path.join(os.getcwd(), 'process.xlsx')
            demand_path = os.path.join(os.getcwd(), 'processdemand.xlsx')

            if not os.path.exists(process_path):
                return jsonify({'status': 'failure', 'error': 'process.xlsx not found'})
            if not os.path.exists(demand_path):
                return jsonify({'status': 'failure', 'error': 'processdemand.xlsx not found'})

            df_process = pd.read_excel(process_path)
            df_demand = pd.read_excel(demand_path)

            first_row_process = df_process.iloc[8].to_dict()  # Select the 2nd row from process.xlsx
            first_row_demand = df_demand.iloc[2].to_dict()    # Select the 1st row from processdemand.xlsx
            fifth_row_demand = df_demand.iloc[3].to_dict()    # Select the 5th row from processdemand.xlsx

            add_data_to_json(first_row_process, 'process.json')
            add_data_to_json(first_row_demand, 'processdemand.json')
            add_data_to_json(fifth_row_demand, 'processdemand.json')

            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'failure', 'error': str(e)})
    return jsonify({'status': 'failure', 'error': 'Invalid action'})

# Route for the gasplant process
@app.route('/process_gasplant', methods=['POST'])
def process_gasplant():
    if request.json.get('action') == 'gasplant':
        try:
            process_path = os.path.join(os.getcwd(), 'process.xlsx')
            demand_path = os.path.join(os.getcwd(), 'processdemand.xlsx')

            if not os.path.exists(process_path):
                return jsonify({'status': 'failure', 'error': 'process.xlsx not found'})
            if not os.path.exists(demand_path):
                return jsonify({'status': 'failure', 'error': 'processdemand.xlsx not found'})

            df_process = pd.read_excel(process_path)
            df_demand = pd.read_excel(demand_path)

            first_row_process = df_process.iloc[3].to_dict()  # Select the 2nd row from process.xlsx
            first_row_demand = df_demand.iloc[6].to_dict()    # Select the 1st row from processdemand.xlsx
            fifth_row_demand = df_demand.iloc[7].to_dict()    # Select the 5th row from processdemand.xlsx

            add_data_to_json(first_row_process, 'process.json')
            add_data_to_json(first_row_demand, 'processdemand.json')
            add_data_to_json(fifth_row_demand, 'processdemand.json')

            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'failure', 'error': str(e)})
    return jsonify({'status': 'failure', 'error': 'Invalid action'})

# Route for the lignite process
@app.route('/process_ligniteplant', methods=['POST'])
def process_ligniteplant():
    if request.json.get('action') == 'ligniteplant':
        try:
            process_path = os.path.join(os.getcwd(), 'process.xlsx')
            demand_path = os.path.join(os.getcwd(), 'processdemand.xlsx')

            if not os.path.exists(process_path):
                return jsonify({'status': 'failure', 'error': 'process.xlsx not found'})
            if not os.path.exists(demand_path):
                return jsonify({'status': 'failure', 'error': 'processdemand.xlsx not found'})

            df_process = pd.read_excel(process_path)
            df_demand = pd.read_excel(demand_path)

            first_row_process = df_process.iloc[9].to_dict()  # Select the 2nd row from process.xlsx
            first_row_demand = df_demand.iloc[12].to_dict()    # Select the 1st row from processdemand.xlsx
            fifth_row_demand = df_demand.iloc[13].to_dict()    # Select the 5th row from processdemand.xlsx

            add_data_to_json(first_row_process, 'process.json')
            add_data_to_json(first_row_demand, 'processdemand.json')
            add_data_to_json(fifth_row_demand, 'processdemand.json')

            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'failure', 'error': str(e)})
    return jsonify({'status': 'failure', 'error': 'Invalid action'})

@app.route('/save_process_data', methods=['POST'])
def save_process_data():
    try:
        data = {
            "Site": request.form.get('site'),
            "Process": request.form.get('process'),
            "inst-cap": float(request.form.get('inst-cap', 0)),
            "cap-lo": float(request.form.get('cap-lo', 0)),
            "cap-up": float(request.form.get('cap-up', 0)),
            "max-grad": float('inf') if request.form.get('max-grad') == 'Infinity' else float(request.form.get('max-grad', 0)),
            "min-fraction": float(request.form.get('min-fraction', 0.0)),
            "inv-cost": float(request.form.get('inv-cost', 0.0)),
            "fix-cost": float(request.form.get('fix-cost', 0.0)),
            "var-cost": float(request.form.get('var-cost', 0.0)),
            "wacc": float(request.form.get('wacc', 0.0)),
            "depreciation": float(request.form.get('depreciation', 0)),
            "area-per-cap": float('NaN'),  # Handle NaN appropriately
            "support_timeframe": int(request.form.get('support_timeframe', 0))
        }

        add_data_to_json(data, 'process.json')

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)})
    


#river finding 

SHAPEFILE_PATH = os.path.join(scripts_dir, '..', 'static', 'hydrorivers', 'HydroRIVERS_v10_as_clipped2_rpj.shp')

# Load the shapefile into a GeoDataFrame
gdf = gpd.read_file(SHAPEFILE_PATH)

# Ensure the shapefile is in a projected coordinate system for accurate distance calculation
if gdf.crs.is_geographic:
    gdf = gdf.to_crs(epsg=32644)  # UTM Zone 44N for Northern India

# Build a spatial index for the geometries
spatial_index = index_func.Index()
for idx, geometry in enumerate(gdf.geometry):
    spatial_index.insert(idx, geometry.bounds)




@app.route('/api/renewables', methods=['POST'])
def renewables():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')

    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    def generate_discharge_timeseries(yearly_avg_discharge, year=2023):
        # Define the number of hours in a year (non-leap year)
        hours_in_year = 365 * 24
        
        # Time index for the entire year
        time_index = pd.date_range(start=f'{year}-01-01', end=f'{year+1}-01-01', freq='H', inclusive='left')


        
        # Define the seasonal variation using a sine wave for simplicity
        # Peak discharge during the monsoon (around day 200 to 275)
        day_of_year = np.arange(1, 366)
        seasonal_variation = np.sin(2 * np.pi * (day_of_year - 200) / 365) * 0.5 + 1
        
        # Extend the seasonal variation to hourly data
        seasonal_variation_hourly = np.repeat(seasonal_variation, 24)
        
        # Define daily variations using a random noise model
        daily_variation = 0.1 * np.random.randn(hours_in_year)
        
        # Combine seasonal and daily variations
        discharge = seasonal_variation_hourly + daily_variation
        
        # Normalize to match the yearly average discharge
        discharge = discharge / discharge.mean() * yearly_avg_discharge
        
        # Create a DataFrame for the time series
        discharge_timeseries = pd.DataFrame({'discharge': discharge}, index=time_index)
        
        return discharge_timeseries
    
    def plot_discharge_timeseries(discharge_timeseries, output_path):
        # Plot the discharge time series
        plt.figure(figsize=(15, 6))
        plt.plot(discharge_timeseries.index, discharge_timeseries['discharge'], label='Discharge (m³/s)')
        plt.xlabel('Date')
        plt.ylabel('Discharge (m³/s)')
        plt.title('Hourly Discharge Time Series')
        plt.legend()
        plt.grid(True)
        plt.savefig(output_path)
        plt.close()



    def get_nearest_lines_within_distance():
        distance_km = 5
        
        latitude = lat
        longitude = lon
        
        point = Point(longitude, latitude)
        
        # Reproject the point to the same CRS as the shapefile
        point = gpd.GeoSeries([point], crs='EPSG:4326').to_crs(gdf.crs).iloc[0]
        
        # Convert distance to the same unit as the CRS of the shapefile (meters)
        distance_m = distance_km * 1000
        
        
        # Create a circular buffer around the point
        buffer = point.buffer(distance_m)
        
        # Clip the river lines with the buffer
        clipped_rivers = gdf[gdf.intersects(buffer)]
        
            
        
        if clipped_rivers.empty: 
            avg_q = 0
            discharge_timeseries = generate_discharge_timeseries(avg_q)
        else:
            avg_q = max(clipped_rivers['DIS_AV_CMS'])
            discharge_timeseries = generate_discharge_timeseries(avg_q)
        
        # Save the discharge time series to JSON
        discharge_timeseries_json = discharge_timeseries.to_json(orient='split', date_format='iso')
        
        avg_q_json = json.dumps({'DIS_AV_CMS': avg_q, 'discharge_timeseries': discharge_timeseries_json})
        output_dir = os.path.join(scripts_dir, '..', 'urbs_master', 'Input', 'json')
        output_path = os.path.join(output_dir, 'avg_q.json')
        with open(output_path, 'w') as f:
            f.write(avg_q_json)
        
        # Plot and save the discharge time series plot
        plot_output_dir = os.path.join(scripts_dir, '..', 'static', 'images')
        plot_output_path = os.path.join(plot_output_dir, 'discharge_timeseries_plot.png')
        plot_discharge_timeseries(discharge_timeseries, plot_output_path)
        
        return avg_q_json
    
    get_nearest_lines_within_distance()


    token = '1408b994667748f3aff7aff50a56759c3e85cb89'  # Replace with your actual token
    api_base = 'https://www.renewables.ninja/api/'


    s = requests.session()
    s.headers = {'Authorization': 'Token ' + token}

    # PV API call
    pv_url = api_base + 'data/pv'
    pv_args = {
        'lat': lat,
        'lon': lon,
        'date_from': '2023-01-01',
        'date_to': '2023-12-31',
        'dataset': 'merra2',
        'capacity': 1.0,
        'system_loss': 0.1,
        'tracking': 0,
        'tilt': 35,
        'azim': 180,
        'format': 'json'
    }

    # Wind API call
    wind_url = api_base + 'data/wind'
    wind_args = {
        'lat': lat,
        'lon': lon,
        'date_from': '2023-01-01',
        'date_to': '2023-12-31',
        'capacity': 1.0,
        'height': 100,
        'turbine': 'Vestas V80 2000',
        'format': 'json'
    }

    try:
        # PV request
        pv_response = s.get(pv_url, params=pv_args)
        pv_response.raise_for_status()
        pv_parsed_response = pv_response.json()
        pv_data = pd.read_json(json.dumps(pv_parsed_response['data']), orient='map')
        pv_metadata = pv_parsed_response['metadata']

        # Wind request
        wind_response = s.get(wind_url, params=wind_args)
        wind_response.raise_for_status()
        wind_parsed_response = wind_response.json()
        wind_data = pd.read_json(json.dumps(wind_parsed_response['data']), orient='map')
        wind_metadata = wind_parsed_response['metadata']

        # Save the data to JSON files
        pv_data_file = os.path.join(app.config['UPLOAD_FOLDER'], 'pv_data.json')
        pv_data.to_json(pv_data_file)

        wind_data_file = os.path.join(app.config['UPLOAD_FOLDER'], 'wind_data.json')
        wind_data.to_json(wind_data_file)

        # Response data
        response_data = {
            'message': 'Success',
            'pv_json_file': 'pv_data.json',
            'wind_json_file': 'wind_data.json'
        }

        return jsonify(response_data)

    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500
    

def transform_data(input_directory, output_directory):
    try:
        # Paths to the JSON files
        wind_data_path = os.path.join(input_directory, 'wind_data.json')
        pv_data_path = os.path.join(input_directory, 'pv_data.json')
        avg_q_path = os.path.join(input_directory, 'avg_q.json')

        # Read wind data
        with open(wind_data_path, 'r') as f:
            wind_data = json.load(f)

        # Read pv data
        with open(pv_data_path, 'r') as f:
            pv_data = json.load(f)

        # Read avg_q data and parse discharge_timeseries
        with open(avg_q_path, 'r') as f:
            avg_q_data = json.load(f)
            discharge_timeseries_json = json.loads(avg_q_data['discharge_timeseries'])
            discharge_timeseries = pd.DataFrame(discharge_timeseries_json['data'],
                                                 columns=discharge_timeseries_json['columns'],
                                                 index=discharge_timeseries_json['index'])

        transformed_data = []

        # Assuming wind_data and pv_data have the same timestamps and lengths
        for i in range(len(wind_data)):
            timestamp = list(wind_data.keys())[i]
            wind_electricity = wind_data[timestamp]['electricity']
            pv_electricity = pv_data[timestamp]['electricity']
            
            # Get the corresponding discharge value for the current index
            hydro_value = discharge_timeseries.iloc[i]['discharge']
            max_hydro = max(discharge_timeseries['discharge'])
            if hydro_value != 0:
                hydro_value = hydro_value / max_hydro * 0.55

            entry = {
                "support_timeframe": 2020,
                "t": i,
                "Mid": {
                    "Wind": wind_electricity,
                    "Solar": pv_electricity,
                    "Hydro": hydro_value
                }
            }
            transformed_data.append(entry)

        # Write transformed data to new JSON file
        output_path = os.path.join(output_directory, 'supim.json')

        with open(output_path, 'w') as f:
            json.dump(transformed_data, f, indent=4)

        print(f"Transformation complete. File saved as {output_path}.")

    except Exception as e:
        print(f"An error occurred: {e}")



@app.route('/transform_files', methods=['POST'])
def transform_files_route():
    source_directory = os.path.join(scripts_dir, '..', 'urbs_master', 'Input', 'json')
    destination_directory = os.path.join(scripts_dir, '..', 'urbs_master', 'Input', 'json')
    
    success = transform_data(source_directory, destination_directory)
    
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure', 'error': 'Failed to move files'})


    
def move_files(source_dir, destination_dir):

    try:
        # Source file paths
        source_process = os.path.join(source_dir, 'process.json')
        source_processdemand = os.path.join(source_dir, 'processdemand.json')
        
        # Destination file paths
        dest_process = os.path.join(destination_dir, 'process1.json')
        dest_processdemand = os.path.join(destination_dir, 'processdemand.json')
        
        # Move files
        shutil.move(source_process, dest_process)
        shutil.move(source_processdemand, dest_processdemand)
        
        print(f"Files moved successfully from {source_dir} to {destination_dir}")
        return True
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return False
    

@app.route('/move_files', methods=['POST'])
def move_files_route():
    source_directory = os.path.join(scripts_dir, '..')
    destination_directory = os.path.join(scripts_dir, '..', 'urbs_master', 'Input', 'json')
    
    success = move_files(source_directory, destination_directory)
    
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure', 'error': 'Failed to move files'})
    
    

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




RESULTS_FOLDER = os.path.join(scripts_dir, '..', 'result')
WORKING_DIR = os.path.join(scripts_dir, '..')

# Function to clear results folder
def clear_results_folder():
    print(f"Clearing results folder: {RESULTS_FOLDER}")
    for filename in os.listdir(RESULTS_FOLDER):
        file_path = os.path.join(RESULTS_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

# Function to clear result text files
def clear_result_txt():
    print(f"Clearing result text files in: {WORKING_DIR}")
    try:
        for filename in os.listdir(WORKING_DIR):
            if 'resultsingle-year' in filename and filename.endswith('.log'):
                file_path = os.path.join(WORKING_DIR, filename)
                os.remove(file_path)
                print(f'Deleted: {file_path}')
    except Exception as e:
        print(f'Failed to clear result text files. Reason: {e}')

# Function to move result PNG files
def move_result_png_file():
    source_folder = os.path.join(scripts_dir, '..', 'result')
    target_folder = os.path.join(scripts_dir, '..', 'static', 'images')

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print(f'Created target directory: {target_folder}')

    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith('.png') and 'Mid' in file:
                source_file_path = os.path.join(root, file)
                target_file_path = os.path.join(target_folder, file)
                try:
                    shutil.copy(source_file_path, target_file_path)
                    print(f'Copied: {source_file_path} to {target_file_path}')
                except Exception as e:
                    print(f'Failed to copy {source_file_path}. Reason: {e}')


def create_zip_of_results():
    zip_filename = os.path.join(RESULTS_FOLDER, 'results.zip')
    print(f"Creating zip file: {zip_filename}")
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(RESULTS_FOLDER):
                for file in files:
                    if file != 'results.zip':
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, RESULTS_FOLDER))
    except Exception as e:
        print(f"Failed to create zip file: {str(e)}")
        raise RuntimeError(f"Failed to create zip file: {str(e)}")
    return zip_filename


@app.route('/runurbs', methods=['POST'])
def run_urbs_script():
    try:
        # Assuming these functions clear previous results (they are not provided in the code)
        clear_results_folder()
        clear_result_txt()

        script_path = os.path.join(scripts_dir, '..', 'urbs_master', 'run_single_year.py')
        subprocess.run(['python', script_path], check=True)

        message = "URBS run successfully"
        print(message)  # Log the success message to the console
        # Redirect to /urbsresults with the success message
        return redirect(url_for('urbsresults', message=message))
    
    except subprocess.CalledProcessError as e:
        error_message = f"An error occurred while running the script: {e}"
        print(error_message)  # Log the error message to the console
        return error_message

def create_plot_from_excel():
    # Define the base path and target filename
    base_path = os.path.join(scripts_dir, '..', 'urbs_master', 'result')
    target_filename = 'scenario_base.xlsx'
    
    # Find the correct folder
    target_folder = None
    for folder_name in os.listdir(base_path):
        if folder_name.startswith('single-year'):
            target_folder = folder_name
            break
    
    # Construct the full file path
    if target_folder is not None:
        file_path = os.path.join(base_path, target_folder, target_filename)
    else:
        raise FileNotFoundError("No folder starting with 'single-year' found in the result directory.")
    
    # Load the headers from the second line of the Excel file
    sheet_name = '2020.Mid.Elec timeseries'
    header_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=2)
    headers = header_df.iloc[1].tolist()
    
    # Load the data starting from line 4
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, skiprows=3)
    
    # Set the headers
    df.columns = headers
    
    # Set the first column as the index (assuming it's the timestep)
    df.set_index(df.columns[0], inplace=True)

    # df = df.iloc[:336]
    
    # List of columns to plot if they exist
    columns_to_plot = ['Photovoltaics', 'Wind park', 'Hydro plant', 'Slack powerplant']
    columns_present = [col for col in columns_to_plot if col in df.columns]
    
    # Create the plot
    plt.figure(figsize=(14, 8))
    
    # Plot the stack plot data
    plt.stackplot(df.index,
                  *[df[col] for col in columns_present],
                  labels=columns_present,
                  colors=['orange', 'lightgreen', 'blue', 'grey'][:len(columns_present)])
    
    # Plot the 'Demand' as a black line if it exists
    if 'Demand' in df.columns:
        df['Demand'] = df['Demand']
        plt.plot(df.index, df['Demand'], color='black', label='Demand', linewidth=1)
    
    plt.xlabel('Time in hours')
    plt.ylabel('Power (kW)')
    plt.title('Elec in Mid')
    plt.legend(loc='upper right')
    plt.grid(True)
    
    # Define the path to save the image
    save_path = os.path.join(scripts_dir, '..', 'static', 'images')
    
    # Ensure the save directory exists
    os.makedirs(save_path, exist_ok=True)
    
    # Save the plot as a PNG image
    image_filename = os.path.join(save_path, 'elec_in_mid.png')
    plt.savefig(image_filename)
    



@app.route('/urbsresults', methods=['POST'])
def upload_urbs_results():
    move_result_png_file()
    create_plot_from_excel()
    zip_filename = create_zip_of_results()

    zip_filepath = zip_filename
    zip_filename = 'results.zip'

    image_filename = 'elec_in_mid.png'
    image_filename2 = 'scenario_base-2020-Slack-Mid-all.png'

    return render_template('results.html', image_filename=image_filename,image_filename2=image_filename2, zip_filename=zip_filename, zip_filepath=zip_filepath)


# Endpoint for downloading results.zip
@app.route('/download/<filename>', methods=['GET'])
def download_results(filename):
    directory = RESULTS_FOLDER  # Update this with the path to your zip files folder
    return send_from_directory(directory, filename, as_attachment=True)



if __name__ == '__main__':
    app.run(debug=True)