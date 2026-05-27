import requests
from datetime import datetime, timezone, timedelta
from db import get_db

def son_24_saat_mi(tarih_str):
    try:
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        tarih = datetime.strptime(tarih_str, fmt).replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - tarih < timedelta(hours=24)
    except:
        return False

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

def mail_gonder(konu, mesaj, alici, smtp_config):
    import smtplib
    from email.mime.text import MIMEText
    try:
        msg = MIMEText(mesaj)
        msg["Subject"] = konu
        msg["From"] = smtp_config.get("user")
        msg["To"] = alici
        with smtplib.SMTP(smtp_config.get("host"), smtp_config.get("port", 587)) as server:
            server.starttls()
            server.login(smtp_config.get("user"), smtp_config.get("password"))
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Mail error: {e}")
        return False

def alarm_log_kaydet(dataset_id, durum, mesaj, kanal):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO alarm_log (dataset_id, durum, mesaj, kanal) VALUES (%s, %s, %s, %s)",
        (dataset_id, durum, mesaj, kanal)
    )
    db.commit()
    cursor.close()
    db.close()

def dataset_kontrol(user_id, datasets):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Kullanıcının SMTP ayarlarını çek
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    sonuclar = []

    for ds in datasets:
        # Dataset config çek
        cursor.execute("""
            SELECT dc.*, d.id as db_dataset_id 
            FROM datasets d
            LEFT JOIN dataset_config dc ON dc.dataset_id = d.id
            WHERE d.user_id = %s AND d.pbi_dataset_id = %s
        """, (user_id, ds["id"]))
        config = cursor.fetchone()

        if not config:
            sonuclar.append({
                "name": ds["name"],
                "durum": ds["son_durum"],
                "sure": ds["sure"],
                "alarm": []
            })
            continue

        alarm_gonderildi = []
        print(f"Kontrol: {ds['name']} | Durum: {ds['son_durum']} | 24saat: {son_24_saat_mi(ds['son_refresh'])}")
        if son_24_saat_mi(ds["son_refresh"]):
            if ds["son_durum"] == "Failed":
                mesaj = (
                    f"🚨 PBI ALARM\n"
                    f"Dataset: {ds['name']}\n"
                    f"Workspace: {ds['workspace']}\n"
                    f"Durum: FAILED\n"
                    f"Zaman: {ds['son_refresh']}"
                )
                if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                    whatsapp_gonder(mesaj, config["phone_number_id"], config["wa_token"], config["alici_whatsapp"])
                    alarm_log_kaydet(config["db_dataset_id"], "Failed", mesaj, "WhatsApp")
                    alarm_gonderildi.append("WhatsApp")

                if config.get("hata_mail") and config.get("alici_mail"):
                    smtp = {"host": "mail.bidanismanlik.com", "port": 587, "user": user["email"], "password": ""}
                    mail_gonder("🚨 PBI ALARM", mesaj, config["alici_mail"], smtp)
                    alarm_log_kaydet(config["db_dataset_id"], "Failed", mesaj, "Email")
                    alarm_gonderildi.append("Email")

            elif ds["sure"] > (config.get("normal_sure") or 300):
                mesaj = (
                    f"⚠️ PBI UYARI\n"
                    f"Dataset: {ds['name']}\n"
                    f"Workspace: {ds['workspace']}\n"
                    f"Refresh süresi anormal: {ds['sure']} saniye"
                )
                if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                    whatsapp_gonder(mesaj, config["phone_number_id"], config["wa_token"], config["alici_whatsapp"])
                    alarm_log_kaydet(config["db_dataset_id"], "Yavaş", mesaj, "WhatsApp")
                    alarm_gonderildi.append("WhatsApp")

                if config.get("hata_mail") and config.get("alici_mail"):
                    smtp = {"host": "mail.bidanismanlik.com", "port": 587, "user": user["email"], "password": ""}
                    mail_gonder("⚠️ PBI UYARI", mesaj, config["alici_mail"], smtp)
                    alarm_log_kaydet(config["db_dataset_id"], "Yavaş", mesaj, "Email")
                    alarm_gonderildi.append("Email")

            else:
                if config.get("basarili_mail") and config.get("alici_mail"):
                    mesaj = (
                        f"✅ PBI OK\n"
                        f"Dataset: {ds['name']}\n"
                        f"Workspace: {ds['workspace']}\n"
                        f"Son refresh: {ds['son_refresh']}\n"
                        f"Süre: {ds['sure']} saniye"
                    )
                    smtp = {"host": "mail.bidanismanlik.com", "port": 587, "user": user["email"], "password": ""}
                    mail_gonder("✅ PBI Rapor", mesaj, config["alici_mail"], smtp)
                    alarm_log_kaydet(config["db_dataset_id"], "OK", mesaj, "Email")
                    alarm_gonderildi.append("Email (rapor)")

        sonuclar.append({
            "name": ds["name"],
            "durum": ds["son_durum"],
            "sure": ds["sure"],
            "alarm": alarm_gonderildi
        })

    cursor.close()
    db.close()
    return sonuclar