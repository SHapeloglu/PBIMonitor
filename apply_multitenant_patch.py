#!/usr/bin/env python3
"""
Multi-tenant OAuth Duzeltmesi - Patch Script
Sabit TENANT_ID yerine 'organizations' endpoint kullanilir,
gercek kullanicinin tenant_id'si token'dan cikarilip DB'ye kaydedilir.

Calistirma: cd /root/pbimonitor_final && python3 apply_multitenant_patch.py
"""

BASE = "/root/pbimonitor_final"

def patch_file(path, replacements, label):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        if old not in content:
            print(f"[HATA] {label}: eslesme bulunamadi, dosya degismis olabilir!")
            print("--- Aranan metin (ilk 100 karakter) ---")
            print(old[:100])
            raise SystemExit(1)
        content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] {label} yamalandi.")


pbi_path = f"{BASE}/pbi.py"

old_imports = '''import requests
from datetime import datetime, timezone
from db import get_db

TENANT_ID = "860892ca-232a-44ea-8378-13160e9f1c27"
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"'''

new_imports = '''import requests
import base64
import json
from datetime import datetime, timezone
from db import get_db

# Multi-tenant SaaS: sabit TENANT_ID yerine 'organizations' endpoint kullanilir.
# Bu sayede herhangi bir is/okul Azure AD hesabi (farkli kiraci) baglanabilir.
AUTH_ENDPOINT = "organizations"
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"


def _tid_from_access_token(access_token):
    """Access token (JWT) icindeki 'tid' claim'ini imza dogrulamadan okur.
    Sadece kayit/bilgi amaclidir, guvenlik dogrulamasi API tarafinda zaten yapilir."""
    try:
        payload_b64 = access_token.split(".")[1]
        padding = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
        return payload.get("tid", "unknown")
    except Exception:
        return "unknown"'''

patch_file(pbi_path, [(old_imports, new_imports)], "pbi.py (import + tid helper)")

old_refresh_url = '''    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "refresh_token",'''

new_refresh_url = '''    url = f"https://login.microsoftonline.com/{AUTH_ENDPOINT}/oauth2/v2.0/token"
    data = {
        "grant_type": "refresh_token",'''

patch_file(pbi_path, [(old_refresh_url, new_refresh_url)], "pbi.py (token_yenile URL)")

old_token_kaydet = '''def token_kaydet(user_id, access_token, expires_in, refresh_token=None):
    expires_at = datetime.now(timezone.utc).timestamp() + expires_in
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO pbi_connections (user_id, tenant_id, token, token_expires_at, refresh_token)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE token=%s, token_expires_at=%s, refresh_token=%s
    """, (user_id, TENANT_ID, access_token, expires_at, refresh_token, access_token, expires_at, refresh_token))
    db.commit()
    cursor.close()
    db.close()'''

new_token_kaydet = '''def token_kaydet(user_id, access_token, expires_in, refresh_token=None):
    expires_at = datetime.now(timezone.utc).timestamp() + expires_in
    gercek_tenant_id = _tid_from_access_token(access_token)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO pbi_connections (user_id, tenant_id, token, token_expires_at, refresh_token)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE token=%s, token_expires_at=%s, refresh_token=%s, tenant_id=%s
    """, (user_id, gercek_tenant_id, access_token, expires_at, refresh_token, access_token, expires_at, refresh_token, gercek_tenant_id))
    db.commit()
    cursor.close()
    db.close()'''

patch_file(pbi_path, [(old_token_kaydet, new_token_kaydet)], "pbi.py (token_kaydet)")

old_devicecode = '''def device_code_baslat():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode"
    data = {
        "client_id": CLIENT_ID,
        "scope": SCOPE
    }
    response = requests.post(url, data=data)
    return response.json()

def device_code_tamamla(device_code):
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"'''

new_devicecode = '''def device_code_baslat():
    url = f"https://login.microsoftonline.com/{AUTH_ENDPOINT}/oauth2/v2.0/devicecode"
    data = {
        "client_id": CLIENT_ID,
        "scope": SCOPE
    }
    response = requests.post(url, data=data)
    return response.json()

def device_code_tamamla(device_code):
    url = f"https://login.microsoftonline.com/{AUTH_ENDPOINT}/oauth2/v2.0/token"'''

patch_file(pbi_path, [(old_devicecode, new_devicecode)], "pbi.py (device code URLs)")

print("\nTum dosyalar basariyla yamalandi.")
print("HATIRLATMA: Azure Portal'da App Registration > Authentication kismindan")
print("'Supported account types' ayarinin 'Accounts in any organizational directory'")
print("(Multitenant) olarak ayarlandigini dogrula, aksi halde bu kod duzeltmesi tek basina yetmez.")
