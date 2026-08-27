# TASKS.md

## ✅ Completed

### Alarms (Feat. #1–#8)
- [x] #1 Ardışık Başarısızlık (Consecutive Failure) — counter-based tracking
- [x] #2 Schedule Disabled
- [x] #3 Gateway Health Down
- [x] #4 Dataset Count Mismatch (basic)
- [x] #5 Kaçırılan Refresh (Missed Refresh)
- [x] #6 Gateway → Dataset Relationship Mapping
- [x] #7 Sıfır Süre Refresh
- [x] #8 Refresh Duration Anomaly (rolling 10-refresh avg)

### Infrastructure
- [x] Encryption (Fernet) — all sensitive fields
- [x] Docker Compose (Flask + PyMySQL + MySQL 8.0 + Scheduler daemon)
- [x] GitHub (public repo, `.env` excluded)
- [x] Refresh History Chart (Chart.js, `/api/refresh_history` endpoint)
- [x] Dashboard Responsive UI (hamburger menu, adaptive grid, mobile-optimized)

## ⏸ Blocked (Awaiting Admin or External)

- **Azure App Registration → Multitenant** (Feat. #Pre-req)
  - Requires "Supported account types" change in Azure Portal
  - Current user: `powerbi@bidanismanlik.com` (no admin)
  - Status: Deferred until admin access available

## 📋 Long-term Backlog (Grouped by Constraint)

### Grup C — API Limited (No Public API Support)
1. **Completed with Warnings** — technically impossible via REST API
2. **#9 Credential/Token Expiry** — limited API support
3. **#10 Kapasite Aşımı** — Premium-only, minimal API info
4. **Sıfır Satır** — limited dataset metadata via REST API

### Blocked (Awaiting .pbix Zip Files)
- `.pbix` parser + DAX anti-pattern detection
- SQL Server DMV connection integration
- DBMonitor integration

### Future (Deferred)
- Teams, Telegram, Slack notifications
- PostgreSQL/Oracle support
- Scanner API integration
- Service Principal token renewal automation
