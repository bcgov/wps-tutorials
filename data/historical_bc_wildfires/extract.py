import ee
import logging
import os
import time
import datetime as dt
import pandas as pd
from utils import *
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    # Load environment variables
    load_dotenv()

    # Authentication
    # Get the secret project name from userdata
    project_name = os.environ['PROJECT_NAME']
    if not project_name:
        raise ValueError("PROJECT_NAME environment variable is required. Please set it in your .env file.")

    # Trigger the authentication flow.
    ee.Authenticate()

    # Initialize the library.
    ee.Initialize(project=project_name)


    start_time = time.time()

    df = create_dataframe() # [:300]

    datetime_col = input("\n Enter the column name of the DATETIME column in your dataset: ")

    df["ignition_datetime"] = convert_float_to_datetime(df[datetime_col])

    weather_data = process_dataframe(df, batch_size=100)

    end_time = time.time()
    print(f"Execution took {end_time - start_time:.2f} seconds, or {((end_time - start_time) / 60):.2f} minutes, or {((end_time - start_time) / 3600):.2f} hours")

    save_results_to_downloads(weather_data)


if __name__ == "__main__":
    main()