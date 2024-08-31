import mysql.connector
from mysql.connector import Error

def create_connection():
    """Create and return a MySQL database connection with autocommit enabled."""
    try:
        # Replace these values with your MySQL server configuration
        connection = mysql.connector.connect(
            host='localhost',          # MySQL server hostname or IP address
            user='root',      # MySQL username
            password='analytics22',  # MySQL password
            database='k8',   # MySQL database name
            autocommit=True  # Enable autocommit
        )

        if connection.is_connected():
            print('Successfully connected to MySQL database')
            return connection

    except Error as e:
        print(f'Error: {e}')
        return None

def close_connection(connection):
    """Close the MySQL database connection."""
    if connection.is_connected():
        connection.close()
        print('MySQL connection closed')
