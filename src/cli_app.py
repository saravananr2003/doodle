import sqlite3
import os

DB_FILE = 'entity360.db'

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Read and execute DDL
    with open('ddl_sqlite.sql', 'r') as ddl_file:
        cursor.executescript(ddl_file.read())

    # Read and execute DML
    with open('dml_sqlite.sql', 'r') as dml_file:
        cursor.executescript(dml_file.read())

    conn.commit()
    conn.close()

def main():
    if not os.path.exists(DB_FILE):
        initialize_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Entity360 Configuration")
    print("Select a product to configure.")
    print("")

    cursor.execute("SELECT name, id, is_active FROM data_products ORDER BY name ASC")
    products = cursor.fetchall()

    for name, product_id, is_active in products:
        status = "active" if is_active == 1 else "inactive"
        print(f"{name} (ID: {product_id}) - Configuration {status}")

    conn.close()

if __name__ == "__main__":
    main()
