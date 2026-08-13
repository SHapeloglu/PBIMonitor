"""
PBI Monitor - Otomatik Kontrol Scheduler
Her 30 dakikada bir tum kullanicilarin datasetlerini kontrol eder.
Ayri bir Docker servisi olarak calisir (pbimonitor-scheduler).
"""

import time
import traceback
from datetime import datetime, timezone

from db import get_db
from pbi import token_yukle, datasetleri_getir, gatewayleri_getir, datasource_dataset_eslestir
from monitor import dataset_kontrol, gateway_kontrol

ARALIK_DAKIKA = 30


def aktif_kullanicilari_getir():
    """DB'deki, gecerli PBI baglantisi olan tum kullanicilari dondurur."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT u.id, u.email
            FROM users u
            INNER JOIN pbi_connections pc ON pc.user_id = u.id
            WHERE pc.token IS NOT NULL
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


def kullanici_kontrol(user):
    user_id = user["id"]
    email = user["email"]

    token = token_yukle(user_id)
    if not token:
        print(f"  [{email}] Token alinamadi veya suresi dolmus, refresh token da gecersiz - atlanıyor.")
        return

    try:
        datasets = datasetleri_getir(token)
    except Exception as e:
        print(f"  [{email}] Dataset listesi alinamadi: {e}")
        return

    if not datasets:
        print(f"  [{email}] Aktif dataset bulunamadi.")
        return

    try:
        sonuclar = dataset_kontrol(user_id, datasets)
        for s in sonuclar:
            alarm_str = ", ".join(s["alarm"]) if s["alarm"] else "alarm yok"
            print(f"  [{email}] {s['name']} -> {s['durum']} ({s['sure']}s) | {alarm_str}")
    except Exception as e:
        print(f"  [{email}] Kontrol sirasinda hata: {e}")
        traceback.print_exc()

    try:
        gateways = gatewayleri_getir(token)
        if gateways:
            esleme = datasource_dataset_eslestir(token, datasets)
            g_sonuclar = gateway_kontrol(user_id, gateways, esleme)
            for g in g_sonuclar:
                print(f"  [{email}] Gateway: {g['gateway']} / {g['datasource']} -> {g['durum']}")
    except Exception as e:
        print(f"  [{email}] Gateway kontrolu sirasinda hata: {e}")
        traceback.print_exc()


def kontrol_dongusu():
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] Kontrol basladi")
    try:
        kullanicilar = aktif_kullanicilari_getir()
        print(f"  Aktif kullanici: {len(kullanicilar)}")
        for user in kullanicilar:
            kullanici_kontrol(user)
    except Exception as e:
        print(f"  Genel hata: {e}")
        traceback.print_exc()
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] Kontrol tamamlandi")


if __name__ == "__main__":
    print(f"PBI Monitor Scheduler baslatildi. Aralik: {ARALIK_DAKIKA} dakika")

    # Ilk calistirmada kisa bir bekleme - web ve db servisleri tam ayaga kalksın
    time.sleep(15)

    while True:
        kontrol_dongusu()
        print(f"  Bir sonraki kontrol {ARALIK_DAKIKA} dakika sonra...")
        time.sleep(ARALIK_DAKIKA * 60)
