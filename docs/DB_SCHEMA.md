# DB_SCHEMA.md — Veritabanı Şeması

---

## Bağlantı Bilgileri

Container: pbimonitor-db
DB Adı: pbimonitor
Kullanıcı: pbimonitor
Şifre: BirNisan82
Port: 3306

DB'ye bağlan:
  docker exec -it pbimonitor-db mysql -u pbimonitor -pBirNisan82 pbimonitor

---

## Güncel Şema

users — id, email, password, plan
  smtp_host, smtp_port, smtp_user, smtp_password (şifreli)
  gateway_alarm_mail, gateway_alarm_whatsapp
  gateway_alici_mail, gateway_alici_whatsapp
  gateway_phone_number_id, gateway_wa_token (şifreli)

pbi_connections — user başına 1 kayıt (UNIQUE user_id)
  id, user_id, tenant_id
  token (şifreli), token_expires_at, refresh_token (şifreli)

datasets — user'ın izlediği datasetler
  id, user_id, pbi_dataset_id
  workspace_id, workspace_name, name, is_active

dataset_config — dataset başına alarm ayarları
  id, dataset_id (UNIQUE)
  hata_whatsapp, hata_mail, basarili_mail
  alici_whatsapp, alici_mail
  normal_sure (saniye), phone_number_id
  wa_token (şifreli)
  ust_uste_hata_esik (varsayılan 3)
  ardisik_hata_sayisi (sayaç)
  beklenen_refresh_saat (varsayılan 24)
  sure_sapma_yuzdesi (varsayılan 150)

alarm_log — dataset alarm geçmişi
  id, dataset_id, durum, mesaj, kanal, created_at
  durum: Failed, Yavas, OK, OtomatikDuraklatma, KacirilnRefresh, ArdisikHata, SifirSure, SureAnomali

gateway_status_log — gateway alarm geçmişi
  id, user_id, gateway_id, gateway_name
  datasource_id, datasource_name
  durum, mesaj, created_at

refresh_history — süre anormalliği için
  id, dataset_id, refresh_time, duration_seconds, status, created_at

---

## Migrasyonlar

2026-07-29 — SMTP + Refresh Token
  ALTER TABLE pbi_connections ADD COLUMN refresh_token MEDIUMTEXT
  ALTER TABLE users ADD COLUMN smtp_host, smtp_port, smtp_user, smtp_password

2026-08-06 — Gateway Monitoring
  ALTER TABLE users ADD COLUMN gateway_alarm_mail, gateway_alarm_whatsapp, etc.
  CREATE TABLE gateway_status_log

2026-08-11 — Ardışık Başarısızlık
  ALTER TABLE dataset_config ADD COLUMN ardisik_hata_sayisi INT DEFAULT 0

2026-08-12 — Süre Anormalliği
  CREATE TABLE refresh_history
  ALTER TABLE dataset_config ADD COLUMN sure_sapma_yuzdesi INT DEFAULT 150

2026-08-13 — Token Şifreleme
  Şema değişikliği yok. TEXT/MEDIUMTEXT kolonları artık Fernet şifreli:
  pbi_connections.token, pbi_connections.refresh_token
  users.smtp_password, users.gateway_wa_token
  dataset_config.wa_token
