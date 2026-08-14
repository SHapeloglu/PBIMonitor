# ARCHITECT.md

## System Overview

PBIMonitor — Multi-tenant Power BI monitoring SaaS on Contabo VPS (95.111.242.96:8003)

**Stack:** Flask + PyMySQL + MySQL 8.0 + Docker Compose
**Auth:** Azure AD OAuth (device-code flow)
**Alerts:** WhatsApp (Meta Graph API) + Email (SMTP)
**Encryption:** Fernet (AES-128)

## Deployment
- **Server:** Contabo VPS (95.111.242.96:8003)
- **Containers:** 3 (web, scheduler, db)
- **Network:** `pbimonitor_pbimonitor-net` (bridge)

## Key Routes
- `/` — dashboard (stats, datasets)
- `/api/datasets` — list user's datasets (PBI API)
- `/api/kontrol` — run immediate refresh check
- `/api/ayarlar` — save dataset thresholds
- `/api/alarm_log` — fetch alarm history
- `/api/refresh_history/<dataset_id>` — fetch last 20 refreshes
- `/api/gateway_log` — gateway health history

## Database (MySQL 8.0)
**9 Tables:**
- users, pbi_connections, datasets, dataset_config
- refresh_history, alarm_log, alarm_history
- gateway_health, gateway_log

## Alarms (8 conditions)
1. Ardışık Başarısızlık (counter-based)
2. Sıfır Süre Refresh (0 seconds = no data)
3. Kaçırılan Refresh (expected time passed)
4. Duration Anomaly (rolling 10-refresh avg)
5. Schedule Disabled
6. Gateway Down
7. Dataset Count Mismatch
8. (Attempted: Completed with Warnings — API impossible)

## Data Flow
1. Scheduler (30 min interval) calls PBI API
2. Compare against `dataset_config` thresholds
3. Evaluate alarm conditions
4. Send WhatsApp + Email alerts
5. Log to `alarm_log`
6. Record `refresh_history`

## Encryption (Fernet)
- Key: `ENCRYPTION_KEY` from `.env`
- Fields: token, refresh_token, smtp_password, wa_token

## Known Limitations
- API gaps: "Completed with Warnings", capacity metrics, row counts, credential expiry
- Single dataset checks only
- Only WhatsApp + SMTP (no Teams/Slack yet)
