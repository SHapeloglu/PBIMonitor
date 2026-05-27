import requests
import json
from datetime import datetime, timezone

tenant_id = "860892ca-232a-44ea-8378-13160e9f1c27"
client_id = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

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
token_data = {
    "access_token": result["access_token"],
    "expires_at": expires_at
}

with open("token.json", "w") as f:
    json.dump(token_data, f)

print("token.json oluşturuldu!")