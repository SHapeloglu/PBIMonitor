# TASKS.md — Görev Listesi

Son güncelleme: 2026-08-13

---

## Tamamlananlar ✅

- [x] Ayarlar modal açılmıyor (cog butonu)
      → onclick içine JSON gömülürken çift tırnak sorunu; datasetMap JS objesi ile çözüldü
- [x] Refresh token — token dolunca otomatik yenile
      → pbi.py: token_yenile() + token_yukle() içinde otomatik çağrı
- [x] Cron job — her 30 dakikada otomatik kontrol
      → scheduler.py, docker-compose da ayrı servis (pbimonitor-scheduler)
- [x] Contabo Docker deploy
      → Kendi MySQL container pbimonitor-db, init.sql ile otomatik tablo kurulumu
- [x] Alarm log sayfası — geçmiş alarmlar görünsün
      → /alarm-log route + alarm_log.html + alarm_log DB tablosu
- [x] SMTP ayarları — arayüzden girilebilsin
      → /ayarlar route + ayarlar.html; users tablosuna smtp_* kolonları eklendi
- [x] Gateway Monitoring
      → /gateway sayfası, api/gateways, api/gateway_kontrol, api/gateway_log
      → scheduler a entegre; gateway_status_log tablosu; gateway alarm ayarları
      → UYARI: Gateway.Read.All scope yeni eklendi, eski bağlantılar yeniden bağlanmalı
- [x] **#7 Ardışık Başarısızlık Alarmı**
      → dataset_config.ardisik_hata_sayisi sayaç kolonu
      → monitor.py: Failed +1, başarılı sıfırla, eşikte [KRITIK] alarm
      → app.py + dashboard.html: ust_uste_hata_esik ayarı eklendi
- [x] **Multi-tenant OAuth düzeltmesi**
      → pbi.py: sabit TENANT_ID → AUTH_ENDPOINT=organizations
      → _tid_from_access_token() ile gerçek tenant_id DB ye yazılıyor
      → BEKLEYEN: Azure Portal da App Registration Multitenant yapılacak
- [x] **#1 Kaçırılan Refresh**
      → monitor.py: son_n_saat_mi() eklendi, beklenen_refresh_saat penceresinde refresh yoksa KacirilnRefresh alarmı
      → app.py: beklenen_refresh_saat INSERT/UPDATE e eklendi
      → dashboard.html: modal a input, modalAc ve ayarlariKaydet e alan eklendi
- [x] **#2 Otomatik Duraklatma**
      → pbi.py: datasetleri_getir e refreshSchedule API çağrısı eklendi, schedule_enabled alanı dönüyor
      → monitor.py: schedule_enabled == False ise OtomatikDuraklatma alarmı (WA + mail)
      → dashboard.html: duraklatılmış datasetlerde Duraklatıldı badge i
- [x] **#8 Sıfır Süre Refresh**
      → monitor.py: sure == 0 olan başarılı refreshler için [UYARI] alarmı
      → Yeni alarm_log durumu: SifirSure
- [x] **#5 Süre Anormalliği**
      → refresh_history tablosu eklendi (dataset_id, refresh_time, duration_seconds, status)
      → dataset_config e sure_sapma_yuzdesi kolonu eklendi (varsayılan 150)
      → monitor.py: başarılı refreshleri history e kaydeder; son 10 ortalamasına göre anomali alarmı
      → pbi.py: refresh_history_kaydet() fonksiyonu eklendi
      → app.py + dashboard.html: sure_sapma_yuzdesi ayarı eklendi
- [x] **#6 Gateway → Dataset İlişkisi**
      → pbi.py: datasource_dataset_eslestir() eklendi
      → monitor.py: gateway_kontrol() datasource_esleme parametresi aldı; alarm mesajına etkilenen dataset listesi eklendi
      → scheduler.py: datasource_dataset_eslestir() çağrısı eklendi, gateway_kontrol e geçirildi
- [x] **Token / Hassas Alan Şifreleme** (2026-08-13)
      → crypto_utils.py: Fernet encrypt/decrypt helper (InvalidToken fallback ile)
      → pbi.py: token_kaydet encrypt, token_yukle decrypt, refresh_token decrypt
      → monitor.py: smtp_password + wa_token + gateway_wa_token tüm çağrılarda decrypt
      → app.py: tüm yazma noktaları encrypt, okuma noktaları decrypt
      → requirements.txt: cryptography eklendi
      → .env: ENCRYPTION_KEY eklendi
      → commit: efacb93

---

## Bekleyen: Azure Portal Adımı ⚠️

Azure Portal da App Registration Multitenant yapılmadan farklı kiracıdaki
kullanıcılar bağlanamaz. Bu adım tamamlanınca admin@skycrops.com test edilecek.

- CLIENT_ID: 14d82eec-204b-4c2f-b7e8-296a70dab67e
- Gidilecek yer: portal.azure.com → Azure Active Directory → App registrations → Authentication
- Değiştirilecek: Supported account types → Accounts in any organizational directory (Multitenant)

---

## Bekleyen: Zip Gelince Başla 🔒

### .pbix Parse + DAX Anti-Pattern Tespiti
**Bekliyor:** İlgili projenin zip i

### SQL Server DMV Bağlantısı
**Bekliyor:** DBMonitor zip i

### DBMonitor Entegrasyonu
**Bekliyor:** DBMonitor zip i — EN SONA alındı

---

## GitHub Push — TAMAMLANDI ✅ (2026-08-13)

- [x] Push başarılı → https://github.com/SHapeloglu/PBIMonitor
- [x] .env repoya girmedi

---

## Grup C — Uzun Vade / Kısıtlı API

- [ ] Completed with Warnings — API den durum string i gelmiyor (teknik olarak imkansız)
- [ ] #4 Sıfır Satır — PBI API kısıtlı destek
- [ ] #9 Credential/Token Süresi — API desteği kısıtlı
- [ ] #10 Kapasite Aşımı — Premium only, API kısıtlı

---

## Uzun Vade Backlog 📋

- [ ] PostgreSQL, Oracle desteği
- [ ] Teams, Telegram, Slack, PagerDuty entegrasyonu
- [ ] Scanner API (toplu workspace tarama)
- [ ] Service Principal desteği
- [ ] API rate limiting
- [ ] Dashboard da refresh geçmişi grafiği
