import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "olapcomt_PowerBIMonitor",
    "password": "BirNisan82",
    "database": "olapcomt_PowerBIMonitor",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db():
    return pymysql.connect(**DB_CONFIG)