import requests
import base64
import json
import os
from datetime import datetime, timezone

tenant_id = "860892ca-232a-44ea-8378-13160e9f1c27"
client_id = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
TOKEN_FILE = "token.json"

def token_gecerli_mi():
    if not os.path.exists(TOKEN_FILE):
        return False
    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
    exp = data.get("expires_at", 0)
    return datetime.now(timezone.utc).timestamp() < exp - 60

def token_yukle():
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)["access_token"]

def token_al():
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/devicecode"
    data = {
        "client_id": client_id,
        "scope": "https://analysis.windows.net/powerbi/api/Dataset.Read.All https://analysis.windows.net/powerbi/api/Workspace.Read.All offline_access"
    }
    response = requests.post(url, data=data)
    result = response.json()

    print(result["message"])
    device_code = result["device_code"]
    input("Tarayıcıda giriş yaptıktan sonra Enter'a bas...")

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": client_id,
        "device_code": device_code
    }
    response = requests.post(url, data=data)
    result = response.json()

    expires_at = datetime.now(timezone.utc).timestamp() + result["expires_in"]
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "access_token": result["access_token"],
            "expires_at": expires_at
        }, f)

    print("Token alındı ve kaydedildi!\n")
    return result["access_token"]

# Token al veya yükle
if token_gecerli_mi():
    print("Kayıtlı token kullanılıyor...\n")
    token = token_yukle()
else:
    token = token_al()

# Tüm çalışma alanlarını ve datasetleri tara
headers = {"Authorization": f"Bearer {token}"}
aktif = []

groups_response = requests.get("https://api.powerbi.com/v1.0/myorg/groups", headers=headers)
groups = groups_response.json()["value"]
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
            aktif.append({
                "workspace": group["name"],
                "name": ds["name"],
                "son_refresh": refreshes[0].get("endTime", "bilinmiyor"),
                "son_durum": refreshes[0].get("status", "bilinmiyor"),
                "refreshes_raw": refreshes
            })

# Sonuçları göster
print(f"Toplam aktif dataset: {len(aktif)}\n")
for ds in aktif:
    print(f"[{ds['workspace']}] {ds['name']}")
    print(f"  Son refresh: {ds['son_refresh']}")
    print(f"  Durum: {ds['son_durum']}")

    # Süre hesapla
    r = ds["refreshes_raw"][0]
    start = r.get("startTime")
    end = r.get("endTime")
    if start and end:
        try:
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            sure = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            print(f"  Süre: {sure.seconds} saniye")
        except:
            print(f"  Süre: hesaplanamadı")
    print()