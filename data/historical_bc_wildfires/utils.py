import ee
import geemap
import logging
import math
import random
import requests
import os
import sqlite3
import time
import datetime as dt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_float_to_datetime(series):
    """
    Converts a pandas Series of float-based date values to datetime.
    Handles:
    - 8-digit formats (YYYYMMDD)
    - 14-digit formats (YYYYMMDDHHMMSS)
    - Invalid lengths become NaT
    """
    # Initialize output series with NaT (same index/dtype as input)
    datetime_series = pd.Series(index=series.index,
                               data=series, # data=pd.NaT,
                               dtype='datetime64[ns]')

    # Process non-null values
    non_null = series.dropna()
    if non_null.empty:
        return datetime_series

    try:
        # Convert to integer then string (avoids scientific notation)
        str_dates = non_null.astype('int64').astype(str)

        # Identify valid date lengths
        mask_8 = str_dates.str.len() == 8    # Date only
        mask_14 = str_dates.str.len() == 14  # Date + time

        # Parse valid formats
        parsed_dates = pd.concat([
            pd.to_datetime(str_dates[mask_8], format='%Y%m%d', errors='coerce'),
            pd.to_datetime(str_dates[mask_14], format='%Y%m%d%H%M%S', errors='coerce')
        ]).sort_index()  # Maintain original order

        # Update result series with valid dates
        datetime_series.update(parsed_dates)

    except Exception as e:
        print(f"Conversion error: {str(e)}")

    return datetime_series


def check_available_datasets():
    """Check what ECMWF datasets are available."""
    try:
        # List available ECMWF collections
        collections = [
            'ECMWF/ERA5/HOURLY',
            'ECMWF/ERA5_LAND/HOURLY',
            'ECMWF/ERA5/DAILY',
            'ECMWF/CAMS/NRT'
        ]
        
        for collection in collections:
            try:
                dataset = ee.ImageCollection(collection)
                count = dataset.limit(1).size().getInfo()
                print(f"✅ \n {collection} - Available ({count} images found)")
            except Exception as e:
                print(f"❌ \n {collection} - Not available: {str(e)}")
                
    except Exception as e:
        print(f"\n Error checking datasets: {e}")


def wind_direction_to_text(wind_dir_deg):
    """
    Convert wind direction in degrees to 8-point cardinal direction.

    Args:
        wind_dir_deg (float): Wind direction in degrees (0-360)

    Returns:
        str: Cardinal direction as text (N, NE, E, SE, S, SW, W, NW)
    """
    # Define direction ranges and corresponding text
    directions = [
        (337.5, 360, "North"),
        (0, 22.5, "North"),
        (22.5, 67.5, "Northeast"),
        (67.5, 112.5, "East"),
        (112.5, 157.5, "Southeast"),
        (157.5, 202.5, "South"),
        (202.5, 247.5, "Southwest"),
        (247.5, 292.5, "West"),
        (292.5, 337.5, "Northwest")
    ]

    # Normalize the degree to be between 0 and 360
    wind_dir_deg = wind_dir_deg % 360

    # Find the matching direction
    for start, end, direction in directions:
        if (start <= wind_dir_deg < end) or (start <= wind_dir_deg <= end and end == 360):
            return direction

    # This should never happen if the ranges are correct
    return "Unknown"


def retry_with_backoff(max_retries=3, initial_delay=2, backoff_factor=2, exceptions=(ee.EEException,)):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retries before giving up
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exceptions to catch and retry on

    Returns:
        A decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay

            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if retries == max_retries:
                        # If we've hit max retries, re-raise the exception
                        raise

                    # Check if it's a timeout error
                    if "timed out" in str(e).lower():
                        # Add jitter to prevent synchronized retries
                        jitter = random.uniform(0, 0.1 * delay)
                        sleep_time = delay + jitter

                        logger.warning(f"Timeout error, retrying in {sleep_time:.1f} seconds... (Attempt {retries+1}/{max_retries})")
                        time.sleep(sleep_time)

                        # Increase delay for next retry
                        delay *= backoff_factor
                        retries += 1
                    else:
                        # Not a timeout error, re-raise immediately
                        raise
        return wrapper
    return decorator


def sample_point_data(weather_data, point, lat, lon, date_val):
    """
    Sample Earth Engine data at a specific point.

    Args:
        weather_data: Earth Engine Image with weather variables
        point: Earth Engine Geometry point
        lat: Latitude value for logging
        lon: Longitude value for logging
        date_val: Date value for logging

    Returns:
        Dictionary of sampled data or None if no data available
    """
    sample_result = weather_data.sample(point, 30).first()

    # Check if sample_result is null
    if sample_result is None or ee.Algorithms.IsEqual(sample_result, None).getInfo():
        logger.warning(f"No data at point ({lat}, {lon}) for date {date_val}")
        return None

    # Convert to dictionary
    return sample_result.toDictionary().getInfo()

# Apply the retry decorator to the sampling function
sample_point_data_with_retry = retry_with_backoff()(sample_point_data)


def get_weather_data(row):
    """
    Extract weather data from Google Earth Engine for a specific location and time.

    Args:
        row: DataFrame row containing 'ignition_datetime', 'LATITUDE', and 'LONGITUDE'

    Returns:
        dict: Weather data or NaN values if data cannot be retrieved
    """
    # Validate input data
    date_val = row.get('ignition_datetime')
    lat = row.get('LATITUDE')
    lon = row.get('LONGITUDE')
    fire_label = row.get('FIRELABEL')

    # Initialize default return values
    default_values = {
        'temperature_c': np.nan,
        'wind_speed_ms': np.nan,
        'wind_direction_deg': np.nan,
        'wind_direction': 'No data returned',
        'humidity_dewpoint_temperature_2m': np.nan,
        'soil_temperature_level_1': np.nan,
        'fire_label': fire_label,
        'ignition_datetime': date_val
    }

    try:
        # Check if we have all required values
        if date_val is None or pd.isna(date_val) or not isinstance(date_val, datetime):
            logger.warning(f"Fire label {fire_label} has an invalid ignition_datetime: {date_val}")
            return default_values

        if lat is None or pd.isna(lat) or lon is None or pd.isna(lon):
            logger.warning(f"Fire label {fire_label} has an invalid coordinates: lat={lat}, lon={lon}")
            return default_values

        # Convert datetime to Earth Engine format
        date = ee.Date(date_val)

        # Create point geometry
        point = ee.Geometry.Point([lon, lat])

        # Get ERA5 reanalysis data
        # era5 = ee.ImageCollection('ECMWF/ERA5/HOURLY')
        era5 = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')

        # Filter to the date (add buffer to ensure we get data)
        start_date = date.advance(-1, 'hour')
        end_date = date.advance(2, 'hour')
        era5_filtered = era5.filterDate(start_date, end_date)

        # Check if we have any images
        if era5_filtered.size().getInfo() == 0:
            logger.warning(f"No ERA5 data found for time range around {date_val} for the {fire_label} fire label")
            # return None
            return default_values

        # Get the image closest to our target time
        era5_list = era5_filtered.toList(era5_filtered.size())
        era5_img = ee.Image(era5_list.get(0))  # Get first image

        # Extract weather variables at the point (using resample for faster computation)
        weather_data = era5_img.select(
            ['temperature_2m', 'u_component_of_wind_10m',
             'v_component_of_wind_10m', 'dewpoint_temperature_2m', 'soil_temperature_level_1']).resample("bilinear")

        # Sample the point with error handling and retry
        try:
            # data = sample_point_data(weather_data, point, lat, lon, date_val)
            data = sample_point_data_with_retry(weather_data, point, lat, lon, date_val)

            # Check if data is empty
            if not data:
                logger.warning(f"Empty data returned for ({lat}, {lon}) at {date_val} for the {fire_label} fire label")
                # return None
                return default_values

            # Calculate wind speed and direction from u,v components
            u = data.get('u_component_of_wind_10m', 0)
            v = data.get('v_component_of_wind_10m', 0)
            wind_speed = (u**2 + v**2)**0.5

            # Avoid division by zero or undefined math
            if u == 0 and v == 0:
                wind_dir = 0  # No wind
            else:
                wind_dir = (270 - (180/3.14159) * math.atan2(v, u)) % 360

            # Convert temperature from K to C (handle None values)
            temp_k = data.get('temperature_2m')
            temp_c = temp_k - 273.15 if temp_k is not None else np.nan

            return {
                'temperature_c': temp_c,
                'wind_speed_ms': wind_speed,
                'wind_direction_deg': wind_dir,
                'wind_direction': wind_direction_to_text(wind_dir),
                'humidity_dewpoint_temperature_2m': data.get('dewpoint_temperature_2m'),
                'soil_temperature_level_1': data.get('soil_temperature_level_1'),
                'fire_label': fire_label,
                'ignition_datetime': date_val
            }

        except ee.EEException as e:
            logger.error(f"Earth Engine sampling error for ({lat}, {lon}) at {date_val}: {str(e)}")
            return default_values

    except Exception as e:
        logger.error(f"Error processing row: {str(e)}")
        # For debugging in development
        # import traceback
        # logger.error(traceback.format_exc())
        return default_values
    

def save_results_to_downloads(weather_data, filename='weather_data.csv', save_folder='temp_downloads'):
    """
    Save results directly to temporary downloads folder

    Args:
        weather_data: DataFrame to save
        filename: Name of the file to save

    Returns:
        Path where the file was saved
    """

    # Save to new folder in Downloads or create it if it doesn't exist
    # save_path = "/content/drive/MyDrive/Cyberse_Fire_King/Downloads"
    relative_path = '~/Downloads'
    expand = os.path.expanduser(relative_path)
    save_path = f'{expand}/{save_folder}'

    if not os.path.exists(save_path):
        os.makedirs(save_path)


    # Create full file path
    full_path = os.path.join(save_path, filename)

    # Save the DataFrame
    weather_data.to_csv(full_path, index=False)

    print(f"✅ Data successfully saved to: {full_path}")


def create_dataframe(hardcoded_path=None, sheet_name=None, db_name=None, table_name=None):
    """
    Create a Pandas DataFrame from a file path or a link.

    Parameters:
    - hardcoded_path (str, optional): The file path or link to be used. If None, the user will be prompted to enter it.
    - sheet_name (str, optional): The sheet name for Excel files or table name for SQL databases.
    - db_name (str, optional): The database name for SQL databases.
    - table_name (str, optional): The table name for SQL databases.
    """
    if hardcoded_path is None:
        filepath_or_link = input("/n Please enter the file path or link for the data source: ")
    else:
        filepath_or_link = hardcoded_path

    try:
        # Handle web URL
        if filepath_or_link.startswith(('http://', 'https://')):
            if filepath_or_link.endswith('.csv'):
                df = pd.read_csv(filepath_or_link)
                
            elif filepath_or_link.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(filepath_or_link, sheet_name=sheet_name)
                
            elif filepath_or_link.endswith('.json'):
                df = pd.read_json(filepath_or_link)
                
            elif filepath_or_link.endswith('.db'):
                response = requests.get(filepath_or_link)
                db_name = input("\n Please enter the DATABASE NAME ONLY (do not include the .db extension): ")
                table_name = input(f"\n Please enter the specific TABLE NAME you wish to access in the {db_name} database: ")
                
                with open(db_name, "wb") as f:
                    f.write(response.content)
          
                conn = sqlite3.connect(db_name)
                query = f"SELECT * FROM {table_name}" if table_name else "SELECT * FROM sqlite_master WHERE type='table';"
                df = pd.read_sql_query(query, conn)
                conn.close()
                
            else:
                raise ValueError("Unsupported file format from the URL.")
                
        else:
            # Handle local file path
            filepath_or_link = os.path.expanduser(filepath_or_link)
            if not os.path.exists(filepath_or_link):
                raise FileNotFoundError(f"The file {filepath_or_link} does not exist.")

            if filepath_or_link.endswith('.csv'):
                df = pd.read_csv(filepath_or_link)
                
            elif filepath_or_link.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(filepath_or_link, sheet_name=sheet_name)
                
            elif filepath_or_link.endswith('.json'):
                df = pd.read_json(filepath_or_link)
                
            elif filepath_or_link.endswith('.db'):
                conn = sqlite3.connect(filepath_or_link)
                query = f"SELECT * FROM {table_name}" if table_name else "SELECT * FROM sqlite_master WHERE type='table';"
                df = pd.read_sql_query(query, conn)
                conn.close()
                
            else:
                raise ValueError("Unsupported file format.")

        print("\n ✅ DataFrame created successfully:")
        return df

    except Exception as e:
        print(f"\n 🙄 An error occurred: {e}")
        return None


###################################
### Processing dataset function ###
###################################

def process_dataframe(df, batch_size=50, batch_delay=3):
    """
    Process the dataframe in batches to avoid Earth Engine quota issues.

    Args:
        df: DataFrame with wildfire data
        batch_size: Number of rows to process in each batch
        batch_delay: Delay in seconds between processing batches

    Returns:
        DataFrame with added weather data
    """

    df = df[df["ignition_datetime"].notna()].sort_values("ignition_datetime")

    results = []
    total_batches = (len(df) + batch_size - 1) // batch_size

    # Process in batches
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        batch_num = i//batch_size + 1

        # Clear progress reporting
        print(f"\n Processing batch {batch_num} of {total_batches} (rows {i} to {min(i+batch_size-1, len(df)-1)})")
        logger.info(f"\n Processing batch {batch_num} of {total_batches} (rows {i} to {min(i+batch_size-1, len(df)-1)})")

        # Apply to each row in this batch
        batch_results = batch.apply(get_weather_data, axis=1, result_type='expand')

        ### ADDITIONAL CHECK ###
        # Check if 'temp_c' key exists in the dictionary and is not empty # or not(bool(batch_results['temperature_c']))
        if 'temperature_c' not in batch_results or (len(batch_results['temperature_c'].value_counts()) == 0):
            print(f"Skipping batch {batch_num} of {total_batches} - no temperature data available \n\n")
            continue  # Skip to the next iteration of the loop

        else:
          results.append(batch_results)

          # Add progress information
          print(f"\n Completed batch {batch_num}/{total_batches} ({batch_num/total_batches*100:.1f}%) \n")
          logger.info(f"Completed batch {batch_num}/{total_batches} ({batch_num/total_batches*100:.1f}%)")

          # Saving each batch to ensure we don't waste computation:
          download_name = f"weather_data_batch_{batch_num}_of_{total_batches}.csv"
          save_results_to_downloads(batch_results, filename=download_name)

        # Add a delay between batches to reduce pressure on the API
        if batch_num < total_batches:
            print(f"\n Pausing for {batch_delay} second(s) before next batch... \n\n")
            logger.info(f"Pausing for {batch_delay} second(s) before next batch...")
            time.sleep(batch_delay)

    # Combine all batches
    if results:
        print("\n Concatenating weather results... \n\n")
        logger.info("Concatenating weather results...")
        weather_data = pd.concat(results)

        # Force completion of all pending operations
        print("\n Finalizing all Earth Engine operations...")
        ee.data.computeValue(ee.Number(1))  # This forces a sync point

        print("\n Weather data processing complete.")
        logger.info("Weather data processing complete.")
        return weather_data

    else:
        print("No weather data to process.")
        logger.warning("No weather data to process.")
        return df

###################################
###################################
###################################