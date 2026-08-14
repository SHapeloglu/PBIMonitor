# DB_SCHEMA.md

## Database: `pbimonitor`

### Tables
1. **users** (id, email, password, smtp_host, smtp_port, smtp_username, smtp_password[encrypted])
2. **pbi_connections** (id, user_id, token[encrypted], refresh_token[encrypted])
3. **datasets** (id, user_id, name, workspace_id, workspace)
4. **dataset_config** (id, dataset_id, db_dataset_id, hata_whatsapp, hata_mail, basarili_mail, phone_number_id[encrypted], wa_token[encrypted], alici_whatsapp, alici_mail, normal_sure, ust_uste_hata_esik, beklenen_refresh_saat, sure_sapma_yuzdesi)
5. **refresh_history** (id, dataset_id, refresh_time, duration_seconds, status) — **INDEX: (dataset_id, refresh_time DESC)**
6. **alarm_log** (id, dataset_id, alarm_type, message, notification_channel) — **INDEX: (dataset_id, created_at DESC)**
7. **alarm_history** (id, dataset_id, alarm_type, message)
8. **gateway_health** (id, user_id, gateway_id, gateway_name, status, last_checked) — **INDEX: (user_id, last_checked DESC)**
9. **gateway_log** (id, user_id, gateway_id, status, message) — **INDEX: (user_id, created_at DESC)**

### Encryption (Fernet, AES-128)
- Key: `ENCRYPTION_KEY` from `.env` (base64-encoded 32-byte key)
- Fields encrypted: pbi_connections.token, pbi_connections.refresh_token, users.smtp_password, dataset_config.wa_token, dataset_config.phone_number_id
