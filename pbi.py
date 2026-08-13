import requests
import base64
import json
from datetime import datetime, timezone
from db import get_db
from crypto_utils import encrypt, decrypt

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
        return "unknown"
SCOPE = "https://analysis.windows.net/powerbi/api/Dataset.Read.All https://analysis.windows.net/powerbi/api/Workspace.Read.All https://analysis.windows.net/powerbi/api/Gateway.Read.All offline_access"

def token_gecerli_mi(user_id):
    """Token gecerli mi kontrol eder; suresi dolmussa otomatik yenilemeyi dener."""
    return token_yukle(user_id) is not None

def token_yukle(user_id):
    """Gecerli access token'i dondurur. Suresi dolmussa refresh token ile otomatik yeniler."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pbi_connections WHERE user_id = %s", (user_id,))
    conn = cursor.fetchone()
    cursor.close()
    db.close()

    if not conn:
        return None

    if datetime.now(timezone.utc).timestamp() < conn['token_expires_at'] - 60:
        return decrypt(conn['token'])

    # Token suresi dolmus veya dolmak uzere - refresh token ile yenilemeyi dene
    if conn.get('refresh_token'):
        yeni = token_yenile(user_id, decrypt(conn['refresh_token']))
        if yeni:
            return yeni['access_token']

    return None

def token_yenile(user_id, refresh_token):
    """Refresh token kullanarak yeni access token alir ve DB'ye kaydeder."""
    url = f"https://login.microsoftonline.com/{AUTH_ENDPOINT}/oauth2/v2.0/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": refresh_token,
        "scope": SCOPE
    }
    try:
        response = requests.post(url, data=data)
        result = response.json()
    except Exception as e:
        print(f"Token yenileme istegi basarisiz: {e}")
        return None

    if "access_token" in result:
        token_kaydet(
            user_id,
            result["access_token"],
            result["expires_in"],
            result.get("refresh_token", refresh_token)  # bazen ayni refresh token donmez, yenisi gelirse onu kullan
        )
        return result

    print(f"Token yenileme hatasi (user_id={user_id}): {result.get('error_description', result)}")
    return None

def token_kaydet(user_id, access_token, expires_in, refresh_token=None):
    expires_at = datetime.now(timezone.utc).timestamp() + expires_in
    gercek_tenant_id = _tid_from_access_token(access_token)
    enc_token = encrypt(access_token)
    enc_refresh = encrypt(refresh_token)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO pbi_connections (user_id, tenant_id, token, token_expires_at, refresh_token)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE token=%s, token_expires_at=%s, refresh_token=%s, tenant_id=%s
    """, (user_id, gercek_tenant_id, enc_token, expires_at, enc_refresh, enc_token, expires_at, enc_refresh, gercek_tenant_id))
    db.commit()
    cursor.close()
    db.close()

def device_code_baslat():
    url = f"https://login.microsoftonline.com/{AUTH_ENDPOINT}/oauth2/v2.0/devicecode"
    data = {
        "client_id": CLIENT_ID,
        "scope": SCOPE
    }
    response = requests.post(url, data=data)
    return response.json()

def device_code_tamamla(device_code):
    url = f"https://login.microsoftonline.com/{AUTH_ENDPOINT}/oauth2/v2.0/token"
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

                # refreshSchedule kontrolu
                schedule_enabled = True
                try:
                    if group["id"]:
                        sched_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group['id']}/datasets/{ds['id']}/refreshSchedule"
                    else:
                        sched_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{ds['id']}/refreshSchedule"
                    sched_resp = requests.get(sched_url, headers=headers)
                    if sched_resp.status_code == 200:
                        schedule_enabled = sched_resp.json().get("enabled", True)
                except:
                    pass
                aktif.append({
                    "id": ds["id"],
                    "workspace": group["name"],
                    "workspace_id": group["id"],
                    "name": ds["name"],
                    "son_refresh": r.get("endTime", "bilinmiyor"),
                    "son_durum": r.get("status", "bilinmiyor"),
                    "sure": sure,
                    "schedule_enabled": schedule_enabled
                })

    return aktif


def datasource_dataset_eslestir(token, datasets):
    """
    Her dataset'in kullandigi datasource ID'lerini cekerek
    {datasource_id: [dataset_name, ...]} eslesmesi dondurur.
    """
    headers = {"Authorization": f"Bearer {token}"}
    esleme = {}
    for ds in datasets:
        ws_id = ds.get("workspace_id")
        ds_id = ds["id"]
        try:
            if ws_id:
                url = f"https://api.powerbi.com/v1.0/myorg/groups/{ws_id}/datasets/{ds_id}/datasources"
            else:
                url = f"https://api.powerbi.com/v1.0/myorg/datasets/{ds_id}/datasources"
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                continue
            for src in resp.json().get("value", []):
                src_id = src.get("datasourceId") or src.get("gatewayDatasourceId")
                if not src_id:
                    continue
                if src_id not in esleme:
                    esleme[src_id] = []
                esleme[src_id].append(ds["name"])
        except:
            pass
    return esleme

def gatewayleri_getir(token):
    """
    Kullanicinin erisebildigi gateway'leri ve her gateway'e bagli veri
    kaynaklarinin (datasource) baglanti durumunu dondurur.
    Gateway.Read.All scope'u gerektirir - eski baglantilar bu scope ile
    yetkilendirilmediyse bos liste doner, kullanicinin PBI baglantisini
    yeniden yapmasi (baglantiyi sifirla + tekrar bagla) gerekir.
    """
    headers = {"Authorization": f"Bearer {token}"}
    sonuc = []

    resp = requests.get("https://api.powerbi.com/v1.0/myorg/gateways", headers=headers)
    if resp.status_code != 200:
        return sonuc

    gateways = resp.json().get("value", [])

    for gw in gateways:
        gw_bilgi = {
            "id": gw["id"],
            "name": gw.get("name", "Bilinmeyen Gateway"),
            "type": gw.get("type", ""),
            "datasources": []
        }

        ds_resp = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/gateways/{gw['id']}/datasources",
            headers=headers
        )

        if ds_resp.status_code == 200:
            for ds in ds_resp.json().get("value", []):
                ds_bilgi = {
                    "id": ds["id"],
                    "name": ds.get("datasourceName", "Bilinmeyen Kaynak"),
                    "type": ds.get("datasourceType", ""),
                    "durum": "Bilinmiyor",
                    "hata_mesaji": None
                }

                durum_resp = requests.get(
                    f"https://api.powerbi.com/v1.0/myorg/gateways/{gw['id']}/datasources/{ds['id']}/status",
                    headers=headers
                )

                if durum_resp.status_code == 200:
                    ds_bilgi["durum"] = "Online"
                else:
                    ds_bilgi["durum"] = "Offline"
                    try:
                        hata = durum_resp.json()
                        ds_bilgi["hata_mesaji"] = hata.get("error", {}).get("message") or durum_resp.text[:300]
                    except Exception:
                        ds_bilgi["hata_mesaji"] = durum_resp.text[:300]

                gw_bilgi["datasources"].append(ds_bilgi)

        sonuc.append(gw_bilgi)

    return sonuc
