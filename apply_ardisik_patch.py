#!/usr/bin/env python3
"""
Ardisik Basarisizlik Alarmi - Patch Script
Calistirma: cd /root/pbimonitor_final && python3 apply_ardisik_patch.py
"""
import re

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


# ---------------------------------------------------------------------------
# 1) monitor.py
# ---------------------------------------------------------------------------
monitor_path = f"{BASE}/monitor.py"

old_monitor = '''        alarm_gonderildi = []

        if son_24_saat_mi(ds["son_refresh"]):
            if ds["son_durum"] == "Failed":
                mesaj = (
                    f"[ALARM] PBI Dataset Hatasi\\n"
                    f"Dataset: {ds['name']}\\n"
                    f"Workspace: {ds['workspace']}\\n"
                    f"Durum: FAILED\\n"
                    f"Zaman: {ds['son_refresh']}"
                )
                if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                    whatsapp_gonder(mesaj, config["phone_number_id"], config["wa_token"], config["alici_whatsapp"])
                    alarm_log_kaydet(config["db_dataset_id"], "Failed", mesaj, "WhatsApp")
                    alarm_gonderildi.append("WhatsApp")
                if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                    mail_gonder("[ALARM] PBI Dataset Hatasi", mesaj, config["alici_mail"], smtp)
                    alarm_log_kaydet(config["db_dataset_id"], "Failed", mesaj, "Email")
                    alarm_gonderildi.append("Email")

            elif ds["sure"] > (config.get("normal_sure") or 300):'''

new_monitor = '''        alarm_gonderildi = []

        if son_24_saat_mi(ds["son_refresh"]):
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
                    f"[ALARM] PBI Dataset Hatasi\\n"
                    f"Dataset: {ds['name']}\\n"
                    f"Workspace: {ds['workspace']}\\n"
                    f"Durum: FAILED\\n"
                    f"Zaman: {ds['son_refresh']}"
                )
                if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                    whatsapp_gonder(mesaj, config["phone_number_id"], config["wa_token"], config["alici_whatsapp"])
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
                        f"[KRITIK] Ardisik Basarisizlik\\n"
                        f"Dataset: {ds['name']}\\n"
                        f"Workspace: {ds['workspace']}\\n"
                        f"Son {esik} kontrolde ust uste basarisiz oldu\\n"
                        f"Zaman: {ds['son_refresh']}"
                    )
                    if config.get("hata_whatsapp") and config.get("alici_whatsapp"):
                        whatsapp_gonder(mesaj_ardisik, config["phone_number_id"], config["wa_token"], config["alici_whatsapp"])
                        alarm_log_kaydet(config["db_dataset_id"], "ArdisikHata", mesaj_ardisik, "WhatsApp")
                        alarm_gonderildi.append("WhatsApp (ardisik)")
                    if config.get("hata_mail") and config.get("alici_mail") and smtp["host"]:
                        mail_gonder("[KRITIK] Ardisik Basarisizlik", mesaj_ardisik, config["alici_mail"], smtp)
                        alarm_log_kaydet(config["db_dataset_id"], "ArdisikHata", mesaj_ardisik, "Email")
                        alarm_gonderildi.append("Email (ardisik)")

            elif ds["sure"] > (config.get("normal_sure") or 300):'''

patch_file(monitor_path, [(old_monitor, new_monitor)], "monitor.py")


# ---------------------------------------------------------------------------
# 2) app.py - ayarlar_kaydet
# ---------------------------------------------------------------------------
app_path = f"{BASE}/app.py"

old_app = '''    cursor.execute("""
        INSERT INTO dataset_config
            (dataset_id, hata_whatsapp, hata_mail, basarili_mail, alici_whatsapp, alici_mail, normal_sure, phone_number_id, wa_token)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            hata_whatsapp=%s, hata_mail=%s, basarili_mail=%s,
            alici_whatsapp=%s, alici_mail=%s, normal_sure=%s,
            phone_number_id=%s, wa_token=%s
    """, (
        dataset_id,
        data.get('hata_whatsapp', False), data.get('hata_mail', False), data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''), data.get('alici_mail', ''), data.get('normal_sure', 300),
        data.get('phone_number_id', ''), data.get('wa_token', ''),
        data.get('hata_whatsapp', False), data.get('hata_mail', False), data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''), data.get('alici_mail', ''), data.get('normal_sure', 300),
        data.get('phone_number_id', ''), data.get('wa_token', '')
    ))'''

new_app = '''    cursor.execute("""
        INSERT INTO dataset_config
            (dataset_id, hata_whatsapp, hata_mail, basarili_mail, alici_whatsapp, alici_mail, normal_sure, phone_number_id, wa_token, ust_uste_hata_esik)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            hata_whatsapp=%s, hata_mail=%s, basarili_mail=%s,
            alici_whatsapp=%s, alici_mail=%s, normal_sure=%s,
            phone_number_id=%s, wa_token=%s, ust_uste_hata_esik=%s
    """, (
        dataset_id,
        data.get('hata_whatsapp', False), data.get('hata_mail', False), data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''), data.get('alici_mail', ''), data.get('normal_sure', 300),
        data.get('phone_number_id', ''), data.get('wa_token', ''), data.get('ust_uste_hata_esik', 3),
        data.get('hata_whatsapp', False), data.get('hata_mail', False), data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''), data.get('alici_mail', ''), data.get('normal_sure', 300),
        data.get('phone_number_id', ''), data.get('wa_token', ''), data.get('ust_uste_hata_esik', 3)
    ))'''

patch_file(app_path, [(old_app, new_app)], "app.py")


# ---------------------------------------------------------------------------
# 3) dashboard.html - modal input + JS
# ---------------------------------------------------------------------------
dash_path = f"{BASE}/templates/dashboard.html"

old_dash_html = '''        <div class="section-sep">Performans</div>
        <div class="form-group">
            <label>Normal refresh süresi (saniye) — bu süreyi aşarsa uyarı</label>
            <input type="number" id="normalSure" placeholder="300">
        </div>'''

new_dash_html = '''        <div class="section-sep">Performans</div>
        <div class="form-group">
            <label>Normal refresh süresi (saniye) — bu süreyi aşarsa uyarı</label>
            <input type="number" id="normalSure" placeholder="300">
        </div>
        <div class="form-group">
            <label>Ardışık başarısızlık eşiği — kaç kez üst üste hata alınca kritik alarm gönderilsin</label>
            <input type="number" id="ustUsteHataEsik" placeholder="3">
        </div>'''

patch_file(dash_path, [(old_dash_html, new_dash_html)], "dashboard.html (form)")

old_dash_js1 = '''    document.getElementById('normalSure').value = ayarlar.normal_sure || 300;
    document.getElementById('ayarModal').classList.add('open');'''

new_dash_js1 = '''    document.getElementById('normalSure').value = ayarlar.normal_sure || 300;
    document.getElementById('ustUsteHataEsik').value = ayarlar.ust_uste_hata_esik || 3;
    document.getElementById('ayarModal').classList.add('open');'''

patch_file(dash_path, [(old_dash_js1, new_dash_js1)], "dashboard.html (modalAc)")

old_dash_js2 = '''        normal_sure: parseInt(document.getElementById('normalSure').value) || 300
    };'''

new_dash_js2 = '''        normal_sure: parseInt(document.getElementById('normalSure').value) || 300,
        ust_uste_hata_esik: parseInt(document.getElementById('ustUsteHataEsik').value) || 3
    };'''

patch_file(dash_path, [(old_dash_js2, new_dash_js2)], "dashboard.html (ayarlariKaydet)")

print("\\nTum dosyalar basariyla yamalandi.")
