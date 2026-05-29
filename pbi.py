import requests
import json
from datetime import datetime, timezone, timedelta
from db import get_db
import pymysql.cursors
TENANT_ID = "860892ca-232a-44ea-8378-13160e9f1c27"
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

def token_gecerli_mi(user_id):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM pbi_connections WHERE user_id = %s", (user_id,))
    conn = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not conn:
        return False
    return datetime.now(timezone.utc).timestamp() < conn['token_expires_at'] - 60

def token_yukle(user_id):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT token FROM pbi_connections WHERE user_id = %s", (user_id,))
    conn = cursor.fetchone()
    cursor.close()
    db.close()
    return conn['token'] if conn else None

def token_kaydet(user_id, access_token, expires_in):
    expires_at = datetime.now(timezone.utc).timestamp() + expires_in
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        INSERT INTO pbi_connections (user_id, tenant_id, token, token_expires_at)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE token=%s, token_expires_at=%s
    """, (user_id, TENANT_ID, access_token, expires_at, access_token, expires_at))
    db.commit()
    cursor.close()
    db.close()

def device_code_baslat():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode"
    data = {
        "client_id": CLIENT_ID,
        "scope": "https://analysis.windows.net/powerbi/api/Dataset.Read.All https://analysis.windows.net/powerbi/api/Workspace.Read.All offline_access"
    }
    response = requests.post(url, data=data)
    return response.json()

def device_code_tamamla(device_code):
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": CLIENT_ID,
        "device_code": device_code
    }
    response = requests.post(url, data=data)
    return response.json()

def datasetleri_getir(token):
    headers = {"Authorization": f"Bearer {token}"}
    aktif = []

    groups_response = requests.get("https://api.powerbi.com/v1.0/myorg/groups", headers=headers)
    groups = groups_response.json().get("value", [])
    groups.append({"id": None, "name": "My Workspace"})

    for group in groups:
        if group["id"]:
            datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group['id']}/datasets"
        else:
            datasets_url = "https://api.powerbi.com/v1.0/myorg/datasets"

        datasets_response = requests.get(datasets_url, headers=headers)
        datasets = datasets_response.json().get("value", [])

        for ds in datasets:
            if group["id"]:
                refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group['id']}/datasets/{ds['id']}/refreshes"
            else:
                refresh_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{ds['id']}/refreshes"

            refresh_response = requests.get(refresh_url, headers=headers)
            refreshes = refresh_response.json().get("value", [])

            if len(refreshes) > 0:
                r = refreshes[0]
                start = r.get("startTime")
                end = r.get("endTime")
                sure = 0
                if start and end:
                    try:
                        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
                        sure = (datetime.strptime(end, fmt) - datetime.strptime(start, fmt)).seconds
                    except:
                        pass

                aktif.append({
                    "id": ds["id"],
                    "workspace": group["name"],
                    "workspace_id": group["id"],
                    "name": ds["name"],
                    "son_refresh": r.get("endTime", "bilinmiyor"),
                    "son_durum": r.get("status", "bilinmiyor"),
                    "sure": sure
                })

    return aktif