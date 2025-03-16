import sqlite3
import os

def test_database_loading():
    # Prompt the user to enter the file path to the local database file
    db_path = input("Enter the file path to the local database file: ")

    # Check if the file exists
    if not os.path.isfile(db_path):
        print(f"Error: The file '{db_path}' does not exist.")
        return

    # Prompt the user to enter the table name
    table_name = input("Enter the table name: ")

    # Give the user an option to use the default query or enter their own custom query
    use_default_query = input("Do you want to use the default query? (yes/no): ").lower()

    if use_default_query.lower() not in ['yes', 'y']:
        # Prompt the user to enter their own custom query
        query = input("Enter your custom query: ").strip()

    else:
        # Use the default query
        query = f"SELECT * FROM {table_name} LIMIT 5;"


    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the query
        cursor.execute(query)

        # Fetch and display the results
        results = cursor.fetchall()
        if results:
            print("Data loaded correctly. Here are the results:")
            # Get column names
            column_names = [description[0] for description in cursor.description]
            print(f"Column Names: {column_names} \n")
            print(f"Number of Rows: {len(results)} \n")
            print(f"Number of Columns: {len(column_names)} \n")
            for row in results:
                print(row)
        else:
            print("No data found.")

        # Close the database connection
        conn.close()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

# Run the script
if __name__ == "__main__":
    test_database_loading()
