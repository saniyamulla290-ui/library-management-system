import pymysql
import sys

def main():
    host = '127.0.0.1'
    user = 'root'
    password = 'Root@123'
    port = 3306
    db_name = 'library_db'

    print(f"Connecting to MySQL at {host}:{port} with user '{user}'...")
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
        print(f"Database '{db_name}' has been verified/created successfully!")
        connection.close()
    except Exception as e:
        print("\n[WARNING] Could not connect to local MySQL server to create database.")
        print(f"Error Details: {e}")
        print("\nPlease make sure:")
        print("1. Your MySQL server is running (e.g., via XAMPP, WAMP, or as a service).")
        print("2. The credentials (host, user, password, port) match your local setup.")
        print(f"3. You create a database named '{db_name}' manually in MySQL before running migrations.")
        sys.exit(1)

if __name__ == '__main__':
    main()
