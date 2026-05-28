import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "olapcomt_PowerBIMonitor",
    "password": "DB_SIFREN",
    "database": "olapcomt_PowerBIMonitor",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci"
}

def get_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SET NAMES utf8mb4")
    cursor.execute("SET CHARACTER SET utf8mb4")
    cursor.execute("SET character_set_connection=utf8mb4")
    cursor.close()
    return conn