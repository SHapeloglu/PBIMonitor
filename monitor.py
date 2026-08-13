import requests
from datetime import datetime, timezone, timedelta
from db import get_db
from crypto_utils import decrypt

def son_24_saat_mi(tarih_str):
    return son_n_saat_mi(tarih_str, 24)

def son_n_saat_mi(tarih_str, saat):
    try:
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        tarih = datetime.strptime(tarih_str, fmt).replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - tarih < timedelta(hours=saat)
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
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.status_code
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return 0

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
    try:
        cursor.execute(
            "INSERT INTO alarm_log (dataset_id, durum, mesaj, kanal) VALUES (%s, %s, %s, %s)",
            (dataset_id, durum, mesaj, kanal)
        )
        db.commit()
    except Exception as e:
        print(f"Alarm log error: {e}")
    finally:
        cursor.close()
        db.close()

def refresh_history_kaydet(dataset_id, refresh_time, duration_seconds, status):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO refresh_history (dataset_id, refresh_time, duration_seconds, status) VALUES (%s, %s, %s, %s)",
            (dataset_id, refresh_time, duration_seconds, status)
        )
        db.commit()
    except Exception as e:
        print(f"Refresh history error: {e}")
    finally:
        cursor.close()
        db.close()

def smtp_yukle(user):
    """Kullanicinin DB'deki SMTP ayarlarini dict olarak dondurur."""
    return {
        "host": user.get("smtp_host") or "",
        "port": user.get("smtp_port") or 587,
        "user": user.get("smtp_user") or user.get("email") or "",
        "password": decrypt(user.get("smtp_password")) or ""
    }

def gateway_log_kaydet(user_id, gateway_id, gateway_name, datasource_id, datasource_name, durum, mesaj):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO gateway_status_log
                (user_id, gateway_id, gateway_name, datasource_id, datasource_name, durum, mesaj)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, gateway_id, gateway_name, datasource_id, datasource_name, durum, mesaj))
        db.commit()
    except Exception as e:
        print(f"Gateway log error: {e}")
    finally:
        cursor.close()
        db.close()


def gateway_kontrol(user_id, gateways, datasource_esleme=None):
    """
    Gateway'lere bagli veri kaynaklarinin baglanti durumunu kontrol eder.
    Offline olan kaynaklar icin alarm gonderir ve gateway_status_log'a kaydeder.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if not user:
        return []

    smtp = smtp_yukle(user)
    sonuclar = []

    for gw in gateways:
        for ds in gw.get("datasources", []):
            durum = ds.get("durum", "Bilinmiyor")
            sonuclar.append({
                "gateway": gw["name"],
                "datasource": ds["name"],
                "type": ds.get("type", ""),
                "durum": durum,
                "hata_mesaji": ds.get("hata_mesaji")
            })

            if durum != "Offline":
                continue

            etkilenen = []
            if datasource_esleme:
                etkilenen = datasource_esleme.get(ds["id"], [])
            etkilenen_str = ", ".join(etkilenen) if etkilenen else "Bilgi alinamadi"
            mesaj = (
                f"[ALARM] Gateway Veri Kaynagi Baglanti Hatasi\n"
                f"Gateway: {gw['name']}\n"
                f"Veri Kaynagi: {ds['name']} ({ds.get('type', '')})\n"
                f"Etkilenen Datasetler: {etkilenen_str}\n"
                f"Hata: {ds.get('hata_mesaji') or 'Baglanti testi basarisiz'}"
            )
            gateway_log_kaydet(user_id, gw["id"], gw["name"], ds["id"], ds["name"], "Offline", mesaj)

            if user.get("gateway_alarm_whatsapp") and user.get("gateway_alici_whatsapp"):
                whatsapp_gonder(
                    mesaj,
                    user.get("gateway_phone_number_id"),
                    decrypt(user.get("gateway_wa_token")),
                    user["gateway_alici_whatsapp"]
                )
            if user.get("gateway_alarm_mail") and user.get("gateway_alici_mail") and smtp["host"]:
                mail_gonder("[ALARM] Gateway Baglanti Hatasi", mesaj, user["gateway_alici_mail"], smtp)

    return sonuclar


def dataset_kontrol(user_id, datasets):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    smtp = smtp_yukle(user)
    sonuclar = []

    for ds in datasets:
        print(f"Kontrol: {ds['name']} | Durum: {ds['son_durum']} | 24saat: {son_24_saat_mi(ds['son_refresh'])}")

        cursor.execute("""
            SELECT dc.*, d.id as db_dataset_id
            FROM datasets d
            LEFT JOIN dataset_config dc ON dc.dataset_id = d.id
            WHERE d.user_id = %s AND d.pbi_dataset_id = %s
        """, (user_id, ds["id"]))
        config = cursor.fetchone()

        if not config:
            sonuclar.append({"name": ds["name"], "durum": ds["son_durum"], "sure": ds["sure"], "alarm": []})
            continue

        alarm_gonderildi = []

        # Otomatik Duraklatma kontrolu
        if not ds.get("schedule_enabled", True):
            mesaj = (
                f"[ALARM] Otomatik Duraklatma\n"
                f"Dataset: {ds['name']}\n"
                f"Workspace: {ds['workspace']}\n"
                f"Power BI refresh zamanlayicisi devre disi birakildi"
            )
            if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                whatsapp_gonder(mesaj, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])
                alarm_log_kaydet(config["db_dataset_id"], "OtomatikDuraklatma", mesaj, "WhatsApp")
                alarm_gonderildi.append("WhatsApp (duraklatma)")
            if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                mail_gonder("[ALARM] Otomatik Duraklatma", mesaj, config["alici_mail"], smtp)
                alarm_log_kaydet(config["db_dataset_id"], "OtomatikDuraklatma", mesaj, "Email")
                alarm_gonderildi.append("Email (duraklatma)")

        beklenen_saat = config.get("beklenen_refresh_saat") or 24
        if not son_n_saat_mi(ds["son_refresh"], beklenen_saat):
            mesaj = (
                f"[ALARM] Kacirilan Refresh\n"
                f"Dataset: {ds['name']}\n"
                f"Workspace: {ds['workspace']}\n"
                f"Son {beklenen_saat} saatte refresh gerceklesmedi\n"
                f"Son bilinen refresh: {ds['son_refresh']}"
            )
            if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                whatsapp_gonder(mesaj, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])
                alarm_log_kaydet(config["db_dataset_id"], "KacirilnRefresh", mesaj, "WhatsApp")
                alarm_gonderildi.append("WhatsApp (kacirilan)")
            if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                mail_gonder("[ALARM] Kacirilan Refresh", mesaj, config["alici_mail"], smtp)
                alarm_log_kaydet(config["db_dataset_id"], "KacirilnRefresh", mesaj, "Email")
                alarm_gonderildi.append("Email (kacirilan)")

        elif son_24_saat_mi(ds["son_refresh"]):
            basarisiz_mi = ds["son_durum"] == "Failed"

            # Ardisik hata sayaci: basarisiz degilse sifirla
            if not basarisiz_mi and (config.get("ardisik_hata_sayisi") or 0) > 0:
                cursor.execute(
                    "UPDATE dataset_config SET ardisik_hata_sayisi = 0 WHERE dataset_id = %s",
                    (config["db_dataset_id"],)
                )
                db.commit()

            if basarisiz_mi:
                mesaj = (
                    f"[ALARM] PBI Dataset Hatasi\n"
                    f"Dataset: {ds['name']}\n"
                    f"Workspace: {ds['workspace']}\n"
                    f"Durum: FAILED\n"
                    f"Zaman: {ds['son_refresh']}"
                )
                if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                    whatsapp_gonder(mesaj, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])
                    alarm_log_kaydet(config["db_dataset_id"], "Failed", mesaj, "WhatsApp")
                    alarm_gonderildi.append("WhatsApp")
                if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                    mail_gonder("[ALARM] PBI Dataset Hatasi", mesaj, config["alici_mail"], smtp)
                    alarm_log_kaydet(config["db_dataset_id"], "Failed", mesaj, "Email")
                    alarm_gonderildi.append("Email")

                # Ardisik hata sayacini artir ve esik kontrolu yap
                cursor.execute(
                    "UPDATE dataset_config SET ardisik_hata_sayisi = ardisik_hata_sayisi + 1 WHERE dataset_id = %s",
                    (config["db_dataset_id"],)
                )
                db.commit()
                cursor.execute(
                    "SELECT ardisik_hata_sayisi FROM dataset_config WHERE dataset_id = %s",
                    (config["db_dataset_id"],)
                )
                sayac = cursor.fetchone()["ardisik_hata_sayisi"]
                esik = config.get("ust_uste_hata_esik") or 3

                if sayac == esik:
                    mesaj_ardisik = (
                        f"[KRITIK] Ardisik Basarisizlik\n"
                        f"Dataset: {ds['name']}\n"
                        f"Workspace: {ds['workspace']}\n"
                        f"Son {esik} kontrolde ust uste basarisiz oldu\n"
                        f"Zaman: {ds['son_refresh']}"
                    )
                    if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                        whatsapp_gonder(mesaj_ardisik, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])
                        alarm_log_kaydet(config["db_dataset_id"], "ArdisikHata", mesaj_ardisik, "WhatsApp")
                        alarm_gonderildi.append("WhatsApp (ardisik)")
                    if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                        mail_gonder("[KRITIK] Ardisik Basarisizlik", mesaj_ardisik, config["alici_mail"], smtp)
                        alarm_log_kaydet(config["db_dataset_id"], "ArdisikHata", mesaj_ardisik, "Email")
                        alarm_gonderildi.append("Email (ardisik)")

            elif ds["sure"] > (config.get("normal_sure") or 300):
                mesaj = (
                    f"[UYARI] PBI Yavas Refresh\n"
                    f"Dataset: {ds['name']}\n"
                    f"Workspace: {ds['workspace']}\n"
                    f"Refresh suresi: {ds['sure']} saniye"
                )
                if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                    whatsapp_gonder(mesaj, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])
                    alarm_log_kaydet(config["db_dataset_id"], "Yavas", mesaj, "WhatsApp")
                    alarm_gonderildi.append("WhatsApp")
                if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                    mail_gonder("[UYARI] PBI Yavas Refresh", mesaj, config["alici_mail"], smtp)
                    alarm_log_kaydet(config["db_dataset_id"], "Yavas", mesaj, "Email")
                    alarm_gonderildi.append("Email")

            elif ds["sure"] == 0:
                mesaj = (
                    f"[UYARI] Sifir Sureli Refresh\n"
                    f"Dataset: {ds['name']}\n"
                    f"Workspace: {ds['workspace']}\n"
                    f"Refresh 0 saniyede tamamlandi - veri guncellenmemis olabilir\n"
                    f"Zaman: {ds['son_refresh']}"
                )
                if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                    whatsapp_gonder(mesaj, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])
                    alarm_log_kaydet(config["db_dataset_id"], "SifirSure", mesaj, "WhatsApp")
                    alarm_gonderildi.append("WhatsApp (sifir sure)")
                if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                    mail_gonder("[UYARI] Sifir Sureli Refresh", mesaj, config["alici_mail"], smtp)
                    alarm_log_kaydet(config["db_dataset_id"], "SifirSure", mesaj, "Email")
                    alarm_gonderildi.append("Email (sifir sure)")

            else:
                # Refresh history kaydet
                refresh_history_kaydet(
                    config["db_dataset_id"], ds["son_refresh"], ds["sure"], ds["son_durum"]
                )

                # Sure anomalisi kontrolu
                sapma_esik = config.get("sure_sapma_yuzdesi") or 150
                sql_ort = (
                    "SELECT AVG(duration_seconds) as ort FROM ("
                    "SELECT duration_seconds FROM refresh_history"
                    " WHERE dataset_id = %s AND status = 'Completed'"
                    " ORDER BY refresh_time DESC LIMIT 10"
                    ") t"
                )
                cursor.execute(sql_ort, (config["db_dataset_id"],))
                row = cursor.fetchone()
                ortalama = row["ort"] if row and row["ort"] else None

                if ortalama and ortalama > 0 and ds["sure"] > ortalama * (sapma_esik / 100):
                    mesaj = (
                        f"[UYARI] Refresh Sure Anomalisi\n"
                        f"Dataset: {ds['name']}\n"
                        f"Workspace: {ds['workspace']}\n"
                        f"Su anki sure: {ds['sure']} saniye\n"
                        f"10 refresh ortalamasi: {int(ortalama)} saniye\n"
                        f"Esik: %{sapma_esik}"
                    )
                    if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                        whatsapp_gonder(mesaj, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])
                        alarm_log_kaydet(config["db_dataset_id"], "SureAnomali", mesaj, "WhatsApp")
                        alarm_gonderildi.append("WhatsApp (sure anomali)")
                    if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                        mail_gonder("[UYARI] Refresh Sure Anomalisi", mesaj, config["alici_mail"], smtp)
                        alarm_log_kaydet(config["db_dataset_id"], "SureAnomali", mesaj, "Email")
                        alarm_gonderildi.append("Email (sure anomali)")
                else:
                    if config.get("basarili_mail") and config.get("alici_mail") and smtp["host"]:
                        mesaj = (
                            f"[OK] PBI Refresh Basarili\n"
                            f"Dataset: {ds['name']}\n"
                            f"Workspace: {ds['workspace']}\n"
                            f"Son refresh: {ds['son_refresh']}\n"
                            f"Sure: {ds['sure']} saniye"
                        )
                        mail_gonder("[OK] PBI Rapor", mesaj, config["alici_mail"], smtp)
                        alarm_log_kaydet(config["db_dataset_id"], "OK", mesaj, "Email")
                        alarm_gonderildi.append("Email (rapor)")

        sonuclar.append({"name": ds["name"], "durum": ds["son_durum"], "sure": ds["sure"], "alarm": alarm_gonderildi})

    cursor.close()
    db.close()
    return sonuclar
