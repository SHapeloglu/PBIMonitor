import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "olapcomt_PowerBIMonitor",
    "password": "olapcomt_PowerBIMonitor",
    "database": "olapcomt_PowerBIMonitor"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
    db.close()
    print("DB bağlantısı başarılı!")