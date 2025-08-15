import sqlite3
import pandas as pd


def init_sqlite_db(table_name, db_name, df):
    """"
    This function is meant to initialize our SQLite database for storing our raw historical wildfires data.
    """
    # Connect to SQLite database (creates one if it doesn't exist)
    conn = sqlite3.connect(f'{db_name}.db')
    cursor = conn.cursor()

    # Create table
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        FIRE_NO TEXT,
        FIRE_YEAR INTEGER,
        RSPNS_TYPC TEXT,
        IGN_DATE DATE,
        FR_T_DTE DATE,
        FIRE_CAUSE TEXT,
        FIRELABEL TEXT,
        FRCNTR INTEGER,
        ZONE INTEGER,
        FIRE_ID INTEGER,
        FIRE_TYPE TEXT,
        INCDNT_NM TEXT,
        GEO_DESC TEXT,
        LATITUDE REAL,
        LONGITUDE REAL,
        SIZE_HA REAL,
        FCODE TEXT,
        SHAPE TEXT, 
        OBJECTID INTEGER,
        X_COORDINATE REAL,
        Y_COORDINATE REAL
    )
    """

    # Execute the query
    cursor.execute(create_table_query)

    # Loading Pandas DataFrame into our SQL table
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


# Executing our code:
if __name__ == "__main__":
    table ='historical_bc_wildfires'
    db = 'bc_wildfires'

    # Extracting our dataset
    data = "https://raw.githubusercontent.com/vanislekahuna/wps-labs/refs/heads/main/data/bc_data_catalogue_historical_fires.csv"
    wildfire_df = pd.read_csv(data)

    # Initializing our SQLite database and then creating a table for our raw historical bc wildfire data.
    init_sqlite_db(
        table_name=table, 
        db_name=db,
        df=wildfire_df
    )