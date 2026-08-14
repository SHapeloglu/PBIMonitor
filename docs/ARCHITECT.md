# ARCHITECT.md — Sistem Mimarisi

---

## Genel Bakış

PBIMonitor, kullanıcı başına Power BI bağlantısı yönetimi yapan
multi-tenant bir SaaS izleme platformudur. Her kullanıcı kendi
Power BI hesabını OAuth ile bağlar; kendi dataset ve gatewaylerinizleri izler;
kendi alarm alıcılarını (WA/mail) tanımlar.

---

## Mimari Katmanlar

\`\`\`
┌─────────────────────────────────────────────────────────┐
│                    Tarayıcı (Kullanıcı)                 │
│         Vanilla JS + Fetch API + Jinja2 Template        │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (port 8003)
┌──────────────────────────▼──────────────────────────────┐
│              pbimonitor-web (Flask/Gunicorn)             │
│                                                         │
│  app.py          → Tüm routelar                         │
│  auth.py         → Login/register Blueprint             │
│  pbi.py          → Power BI API istemcisi               │
│  monitor.py      → Alarm motoru                         │
│  db.py           → MySQL bağlantı yöneticisi            │
│  crypto_utils.py → Fernet şifreleme                     │
└────────────┬─────────────────────────┬──────────────────┘
             │                         │
┌────────────▼──────────┐  ┌──────────▼──────────────────┐
│  pbimonitor-db        │  │  Dış Servisler               │
│  MySQL 8.0            │  │                              │
│                       │  │  Power BI REST API           │
│  users                │  │  api.powerbi.com             │
│  pbi_connections      │  │                              │
│  datasets             │  │  Microsoft OAuth             │
│  dataset_config       │  │  login.microsoftonline.com   │
│  alarm_log            │  │                              │
│  gateway_status_log   │  │  Meta Graph API (WhatsApp)   │
│  refresh_history      │  │  graph.facebook.com          │
│                       │  │                              │
└───────────────────────┘  │  SMTP (mail)                 │
                           └─────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│         pbimonitor-scheduler (Python daemon)             │
│                                                         │
│  Her 30 dakikada:                                       │
│  1. Aktif kullanıcıları DB den çek                      │
│  2. Her kullanıcı için token_yukle()                    │
│  3. datasetleri_getir() → dataset_kontrol()             │
│  4. datasource_dataset_eslestir()                       │
│  5. gatewayleri_getir() → gateway_kontrol()             │
│  6. Alarm gerekiyorsa WA/mail gönder + log kaydet       │
└─────────────────────────────────────────────────────────┘
\`\`\`

---

## Veri Akışı

### 1. Kullanıcı Power BI Bağlantısı (Device Code Flow)

\`\`\`
Kullanıcı                Flask                 Microsoft
    │                      │                       │
    │── "Bağlan" tıkla ───▶│                       │
    │                      │── /devicecode ────────▶│
    │                      │◀── device_code, URL ──│
    │◀── Kod göster ───────│                       │
    │                      │                       │
    │── microsoft.com da kod girer ────────────────▶│
    │                      │                       │
    │── "Tamamla" tıkla ──▶│                       │
    │                      │── /token (polling) ───▶│
    │                      │◀── access+refresh ────│
    │                      │── DB ye kaydet        │
    │◀── "Bağlandı" ───────│                       │
\`\`\`

### 2. Scheduler Kontrol Döngüsü

\`\`\`
Scheduler (30 dk)
    │
    ├── aktif_kullanicilari_getir() → [user1, user2, ...]
    │
    └── Her kullanıcı için:
         │
         ├── token_yukle(user_id)
         │    ├── Geçerliyse: decrypt et, token döndür
         │    └── Süresi dolmuşsa: refresh_token ile yenile → encrypt → kaydet → döndür
         │
         ├── datasetleri_getir(token)
         │    └── PBI API: groups → datasets → refreshes + refreshSchedule
         │
         ├── dataset_kontrol(user_id, datasets)
         │    ├── schedule_enabled == False → OtomatikDuraklatma alarmı
         │    ├── Son N saatte refresh yok → KacirilnRefresh alarmı
         │    ├── Durum == Failed → Failed alarmı + ardisik sayaç
         │    ├── Ardışık sayaç == eşik → [KRITIK] ArdisikHata alarmı
         │    ├── sure == 0 → SifirSure alarmı
         │    ├── sure > normal_sure → Yavas alarmı
         │    ├── sure > ortalama * sapma_esik/100 → SureAnomali alarmı
         │    └── Başarılı + basarili_mail → OK rapor maili
         │
         ├── datasource_dataset_eslestir(token, datasets)
         │    └── PBI API: her dataset için /datasources → {src_id: [ds_name,...]}
         │
         ├── gatewayleri_getir(token)
         │    └── PBI API: gateways → datasources → status
         │
         └── gateway_kontrol(user_id, gateways, datasource_esleme)
              ├── Datasource == Offline → alarm (etkilenen datasetler ile)
              └── gateway_status_log a kaydet
\`\`\`

### 3. Alarm Gönderme Zinciri

\`\`\`
Alarm tetiklendi
    │
    ├── WhatsApp (Meta Graph API)
    │    ├── phone_number_id + wa_token (decrypt) → dataset_config tablosundan
    │    └── alıcı: alici_whatsapp
    │
    ├── E-posta (SMTP)
    │    ├── smtp_host/port/user/password (decrypt) → users tablosundan
    │    └── alıcı: alici_mail
    │
    └── Log
         └── alarm_log tablosuna INSERT
\`\`\`

---

## Veritabanı Şeması

\`\`\`sql
users
  id, email, password, plan
  smtp_host, smtp_port, smtp_user, smtp_password (şifreli)
  gateway_alarm_mail, gateway_alarm_whatsapp
  gateway_alici_mail, gateway_alici_whatsapp
  gateway_phone_number_id, gateway_wa_token (şifreli)

pbi_connections                    ← user başına 1 kayıt (UNIQUE user_id)
  id, user_id, tenant_id
  token (MEDIUMTEXT, şifreli)
  token_expires_at (BIGINT/Unix timestamp)
  refresh_token (MEDIUMTEXT, şifreli)

datasets                           ← user ın izlediği datasetler
  id, user_id, pbi_dataset_id
  workspace_id, workspace_name, name
  is_active

dataset_config                     ← dataset başına alarm ayarları (UNIQUE dataset_id)
  id, dataset_id
  hata_whatsapp, hata_mail, basarili_mail
  alici_whatsapp, alici_mail
  normal_sure (INT, saniye)
  phone_number_id, wa_token (şifreli)
  ust_uste_hata_esik (INT, varsayılan 3)
  ardisik_hata_sayisi (INT, sayaç)
  beklenen_refresh_saat (INT, varsayılan 24)
  sure_sapma_yuzdesi (INT, varsayılan 150)

alarm_log                          ← dataset alarm geçmişi
  id, dataset_id, durum, mesaj, kanal, created_at
  -- durum değerleri: Failed, Yavas, OK, OtomatikDuraklatma,
  --                  KacirilnRefresh, ArdisikHata, SifirSure, SureAnomali

gateway_status_log                 ← gateway alarm geçmişi
  id, user_id, gateway_id, gateway_name
  datasource_id, datasource_name
  durum, mesaj, created_at

refresh_history                    ← Süre anormalliği için refresh geçmişi
  id, dataset_id, refresh_time, duration_seconds, status, created_at
\`\`\`

---

## API Endpoint Kataloğu

### Sayfa Routeları
| Method | Path | Açıklama |
|---|---|---|
| GET | / | Dashboard |
| GET | /alarm-log | Alarm geçmişi |
| GET | /ayarlar | Ayarlar sayfası |
| GET | /gateway | Gateway izleme |

### Power BI API Routeları
| Method | Path | Açıklama |
|---|---|---|
| GET | /api/pbi/baglant_baslat | Device code başlat |
| POST | /api/pbi/baglanti_tamamla | Token al + kaydet |
| GET | /api/pbi/durum | Token geçerli mi? |
| POST | /api/pbi/baglanti_sifirla | Token sil |

### Dataset Routeları
| Method | Path | Açıklama |
|---|---|---|
| GET | /api/datasets | Dataset listesi (PBI API den) |
| POST | /api/ayarlar | Dataset alarm ayarları kaydet |
| GET | /api/kontrol | Manuel dataset kontrol + alarm |
| GET | /api/alarm_log | Son 50 dataset alarm kaydı |

### Gateway Routeları
| Method | Path | Açıklama |
|---|---|---|
| GET | /api/gateways | Gateway + datasource listesi |
| GET | /api/gateway_kontrol | Manuel gateway kontrol + alarm |
| GET | /api/gateway_log | Son 50 gateway alarm kaydı |
| GET/POST | /api/ayarlar/gateway | Gateway alarm ayarları |

### Ayarlar Routeları
| Method | Path | Açıklama |
|---|---|---|
| GET/POST | /api/ayarlar/smtp | SMTP ayarları |
| POST | /api/ayarlar/smtp/test | Test maili gönder |

---

## Güvenlik Modeli

- **Session:** Flask server-side session (secret key .env de)
- **Şifre:** Werkzeug generate_password_hash / check_password_hash
- **Token/Şifre:** Fernet (symmetric) ile şifrelenmiş — pbi_connections.token, refresh_token, users.smtp_password, gateway_wa_token, dataset_config.wa_token. ENCRYPTION_KEY .env de.
- **Tenant izolasyonu:** Tüm sorgularda WHERE user_id = session[user_id]
- **Auth decorator:** @giris_gerekli — tüm korumalı routelarda zorunlu

---

## Bilinen Teknik Borçlar

1. **Rate limiting yok** — Scheduler tüm kullanıcıları ardışık kontrol ediyor; çok kullanıcıda PBI API limite takılabilir
2. **Azure Multitenant** — App Registration henüz Multitenant değil; farklı tenant kullanıcıları bağlanamıyor

---

## Gelecek Mimari Genişleme (Planlanan)

\`\`\`
PBIMonitor
    ├── Mevcut: Dataset refresh + Gateway monitoring (tüm alarm kuralları aktif)
    ├── Sprint 3: .pbix parse + DAX anti-pattern tespiti
    └── Sprint 4: DBMonitor entegrasyonu (ortak alarm altyapısı)

DBMonitor (ayrı proje, ortak altyapı)
    ├── MySQL / PostgreSQL / SQL Server / Oracle bağlantısı
    ├── DMV / pg_stat / information_schema sorgu izleme
    ├── Blocking, deadlock, yavaş sorgu alarmları
    └── PBIMonitor ile ortak: WA + mail alarm motoru, multi-tenant, Docker
\`\`\`
