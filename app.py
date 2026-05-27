from flask import Flask, render_template, request, jsonify
import requests
import json
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

CONFIG_FILE = "config.json"
TOKEN_FILE = "token.json"

TENANT_ID = "860892ca-232a-44ea-8378-13160e9f1c27"
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"

def config_yukle():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def config_kaydet(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

def whatsapp_gonder(mesaj, phone_number_id, wa_token, alici):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {wa_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": alici,
        "type": "text",
        "text": {"body": mesaj}
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code

def mail_gonder(konu, mesaj, alici):
    import smtplib
    from email.mime.text import MIMEText
    config = config_yukle()
    smtp = config.get("smtp", {})
    try:
        msg = MIMEText(mesaj)
        msg["Subject"] = konu
        msg["From"] = smtp.get("user")
        msg["To"] = alici
        with smtplib.SMTP(smtp.get("host"), smtp.get("port", 587)) as server:
            server.starttls()
            server.login(smtp.get("user"), smtp.get("password"))
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Mail hatası: {e}")
        return False

def son_24_saat_mi(tarih_str):
    try:
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        tarih = datetime.strptime(tarih_str, fmt).replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - tarih < timedelta(hours=24)
    except:
        return False

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
                    "name": ds["name"],
                    "son_refresh": r.get("endTime", "bilinmiyor"),
                    "son_durum": r.get("status", "bilinmiyor"),
                    "sure": sure
                })

    return aktif

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/datasets")
def api_datasets():
    if not token_gecerli_mi():
        return jsonify({"error": "token_yok"}), 401
    token = token_yukle()
    datasets = datasetleri_getir(token)
    config = config_yukle()
    for ds in datasets:
        ds_config = config.get(ds["id"], {})
        ds["ayarlar"] = ds_config
    return jsonify(datasets)

@app.route("/api/ayarlar", methods=["POST"])
def ayarlar_kaydet():
    data = request.json
    config = config_yukle()
    dataset_id = data.get("dataset_id")
    config[dataset_id] = {
        "hata_whatsapp": data.get("hata_whatsapp", False),
        "hata_mail": data.get("hata_mail", False),
        "basarili_mail": data.get("basarili_mail", False),
        "alici_whatsapp": data.get("alici_whatsapp", ""),
        "alici_mail": data.get("alici_mail", ""),
        "normal_sure": data.get("normal_sure", 300)
    }
    config_kaydet(config)
    return jsonify({"status": "ok"})

@app.route("/api/kontrol")
def manuel_kontrol():
    if not token_gecerli_mi():
        return jsonify({"error": "token_yok"}), 401
    token = token_yukle()
    datasets = datasetleri_getir(token)
    config = config_yukle()
    sonuclar = []

    for ds in datasets:
        ds_config = config.get(ds["id"], {})
        alarm_gonderildi = []

        if son_24_saat_mi(ds["son_refresh"]):
            if ds["son_durum"] == "Failed":
                mesaj = f"🚨 PBI ALARM\nDataset: {ds['name']}\nWorkspace: {ds['workspace']}\nDurum: FAILED\nZaman: {ds['son_refresh']}"
                if ds_config.get("hata_whatsapp") and ds_config.get("alici_whatsapp"):
                    config_ana = config_yukle()
                    whatsapp_gonder(mesaj, config_ana.get("phone_number_id"), config_ana.get("wa_token"), ds_config["alici_whatsapp"])
                    alarm_gonderildi.append("WhatsApp")
                if ds_config.get("hata_mail") and ds_config.get("alici_mail"):
                    mail_gonder("🚨 PBI ALARM", mesaj, ds_config["alici_mail"])
                    alarm_gonderildi.append("Email")

            elif ds["sure"] > ds_config.get("normal_sure", 300):
                mesaj = f"⚠️ PBI UYARI\nDataset: {ds['name']}\nWorkspace: {ds['workspace']}\nRefresh süresi anormal: {ds['sure']} saniye"
                if ds_config.get("hata_whatsapp") and ds_config.get("alici_whatsapp"):
                    config_ana = config_yukle()
                    whatsapp_gonder(mesaj, config_ana.get("phone_number_id"), config_ana.get("wa_token"), ds_config["alici_whatsapp"])
                    alarm_gonderildi.append("WhatsApp")
                if ds_config.get("hata_mail") and ds_config.get("alici_mail"):
                    mail_gonder("⚠️ PBI UYARI", mesaj, ds_config["alici_mail"])
                    alarm_gonderildi.append("Email")

            else:
                if ds_config.get("basarili_mail") and ds_config.get("alici_mail"):
                    mesaj = f"✅ PBI OK\nDataset: {ds['name']}\nWorkspace: {ds['workspace']}\nSon refresh: {ds['son_refresh']}\nSüre: {ds['sure']} saniye"
                    mail_gonder("✅ PBI Rapor", mesaj, ds_config["alici_mail"])
                    alarm_gonderildi.append("Email (rapor)")

        sonuclar.append({
            "name": ds["name"],
            "durum": ds["son_durum"],
            "sure": ds["sure"],
            "alarm": alarm_gonderildi
        })

    return jsonify(sonuclar)

@app.route("/api/token_durum")
def token_durum():
    return jsonify({"gecerli": token_gecerli_mi()})

if __name__ == "__main__":
    app.run(debug=True)
