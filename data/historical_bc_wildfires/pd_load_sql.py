import pandas as pd
import sqlite3
import os

def pandas_dtype_to_sql(dtype):
    """
    Convert pandas dtype to SQL data type
    """
    dtype_str = str(dtype)
    
    if 'int' in dtype_str:
        return 'INTEGER'
    elif 'float' in dtype_str:
        return 'REAL'
    elif 'datetime' in dtype_str:
        return 'TIMESTAMP'
    elif 'bool' in dtype_str:
        return 'INTEGER'  # SQLite doesn't have a boolean type
    else:
        return 'TEXT'  # Default to TEXT for object and other types

def get_dataframe():
    """
    Load a pandas DataFrame based on user input
    """
    while True:
        file_path = input("Enter the path to your data file (CSV, Excel, etc.): ")
        try:
            # Convert the input string to a raw string by handling escape sequences
            file_path = file_path.replace('\\', '\\\\')
            file_path = os.path.expanduser(file_path)

        except Exception as e:
            print(f"Error loading file: {e}")
            retry = input("Would you like to try again? (y/n): ")
            if retry.lower() not in ['y', 'yes']:
                return None

        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found. Using hardcoded file path. Try to fix code later.")

            
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_extension == '.json':
                df = pd.read_json(file_path)
            else:
                print(f"Unsupported file format: {file_extension}")
                continue
                
            print(f"Successfully loaded DataFrame with {df.shape[0]} rows and {df.shape[1]} columns. \n")
            return df
        except Exception as e:
            print(f"Error loading file: {str(e)}")

def create_column_type_dict(df):
    """
    Create a dictionary of column names and their SQL data types
    """
    column_types = {}
    
    for column in df.columns:
        sql_type = pandas_dtype_to_sql(df[column].dtype)
        column_types[column] = sql_type
    
    return column_types

def manually_enter_dict():
    """
    Allow user to manually enter a dictionary of column names and types
    """
    column_types = {}
    print("Enter your column names and types. Type 'done' when finished.")
    print("Valid SQL types: INTEGER, REAL, TEXT, TIMESTAMP, etc.")
    
    while True:
        column_name = input("Column name (or 'done' to finish): ")
        
        if column_name.lower() == 'done':
            break
            
        column_type = input(f"SQL type for column '{column_name}': ").upper()
        column_types[column_name] = column_type
    
    return column_types

def generate_create_table_sql(table_name, column_types):
    """
    Generate SQL CREATE TABLE statement based on column_types dictionary
    """
    sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    
    # Add columns
    column_definitions = []
    for column, dtype in column_types.items():
        # Replace any spaces in column names with underscores for SQL compatibility
        safe_column = column.replace(' ', '_')
        column_definitions.append(f"    {safe_column} {dtype}")
    
    sql += ",\n".join(column_definitions)
    sql += "\n);"
    
    return sql

def main():
    # Step 1: Load the DataFrame
    df = get_dataframe()
    
    # Step 2: Create dictionary of column types
    column_types = create_column_type_dict(df)
    
    # Step 3: Print the dictionary for confirmation
    print("\nColumn name to data type mapping:")
    for column, dtype in column_types.items():
        print(f"{column}: {dtype}")
    
    # Ask for confirmation
    confirmation = input("\nIs this mapping correct? (Yes/No): ")
    
    if confirmation.lower() not in ['yes', 'y']:
        print("Please enter your own column type dictionary:")
        column_types = manually_enter_dict()
    
    # Step 4: Get database file path
    db_path = input("\nEnter the local file path to your database file (will be created if it doesn't exist): ")
    
    # Step 5: Get table name
    table_name = input("Enter the name for your table: ")
    
    # Step 6: Generate the CREATE TABLE SQL
    create_query = generate_create_table_sql(table_name, column_types)
    
    # Print the generated SQL
    print("\nGenerated SQL Query:")
    print(create_query)

    # Step 7: Ask if user wants to execute the query
    execute = input("\nDo you want to execute this query and create the table? (Yes/No): ")
    
    if execute.lower() in ['yes', 'y']:
        try:
            # Connect to database
            # db_path = input("Please provide a local file path for the database:")

            # Connect to the local database file
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(create_query)
            conn.commit()

        except Exception as e:
            print(f"Error executing SQL: {str(e)}")
        
        print(f"Table '{table_name}' created successfully in database '{db_path}'. \n\n")

        
        # Ask if user wants to insert the data
        insert_data = input("Do you want to insert the DataFrame data into the table? (Yes/No): ")
        
        if insert_data.lower() in ['yes', 'y']:
            # Clean column names for SQL compatibility
            df.columns = [col.replace(' ', '_') for col in df.columns]
            
            # Insert data
            df.to_sql(table_name, conn, if_exists='append', index=False)
            print(f"Data inserted successfully into table '{table_name}'. \n\n")
        
        conn.close()
            
    else:
        print("The query was not executed. Terminating code.")
    
    
    # Return the query for further use
    return create_query

# Run the program
if __name__ == "__main__":
    create_query = main()