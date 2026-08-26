# PBIMonitor

A multi-tenant **Power BI monitoring SaaS platform** that detects and alerts on dataset refresh failures, gateway issues, and anomalies that Power BI's native tooling doesn't surface.

**Live:** https://95.111.242.96:8003

---

## Features

### 8 Alarm Conditions
- **Consecutive Failures** — Track failed refresh attempts counter
- **Zero Duration Refresh** — Detect incomplete/phantom refreshes (0 seconds = no data)
- **Missed Refresh** — Alert when refresh doesn't occur at expected time
- **Refresh Duration Anomaly** — Detect unusual slowdowns (rolling 10-refresh average)
- **Schedule Disabled** — Catch dataset schedule toggle-offs
- **Gateway Down** — Monitor Power BI gateway health
- **Dataset Count Mismatch** — Track import mode dataset changes
- (Attempted: *Completed with Warnings* — blocked by Power BI API limitations)

### Infrastructure
- **Multi-tenant** — Azure AD OAuth (`organizations` endpoint)
- **Encryption** — Fernet AES-128 for sensitive fields (tokens, credentials)
- **Alerts** — WhatsApp (Meta Graph API) + Email (SMTP per user)
- **Responsive UI** — Mobile-first design (hamburger menu, adaptive grid)
- **Refresh History** — 20-refresh chart per dataset via Chart.js
- **Docker Compose** — 3 containers (web, scheduler, database)

---

## Tech Stack

- **Backend:** Flask + PyMySQL + MySQL 8.0
- **Frontend:** Vanilla JS, Chart.js (CDN), responsive CSS
- **Auth:** Azure AD OAuth (device-code flow)
- **Scheduler:** Python daemon (30 min interval)
- **Alerts:** Meta Graph API (WhatsApp), SMTP (Email)
- **Encryption:** Python \`cryptography\` (Fernet)
- **Deployment:** Docker Compose on Ubuntu 24

---

## Quick Start

### Prerequisites
- Python 3.13+, Docker, MySQL 8.0
- Azure AD App Registration
- Meta Business Account (WhatsApp)

### Installation

\`\`\`bash
git clone https://github.com/SHapeloglu/PBIMonitor.git
cd PBIMonitor
cp .env.example .env
# Edit .env with credentials
docker compose up -d
\`\`\`

Access: http://localhost:8003

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | \`/\` | Dashboard |
| GET | \`/api/datasets\` | List datasets |
| POST | \`/api/kontrol\` | Refresh check |
| GET | \`/api/alarm_log\` | Alarm history |
| GET | \`/api/refresh_history/<id>\` | Chart data |

---

## Database

**9 Tables:** users, pbi_connections, datasets, dataset_config, refresh_history, alarm_log, alarm_history, gateway_health, gateway_log

Encrypted fields: tokens, credentials (Fernet AES-128)

---

## Responsive Design

| Screen | Layout | Sidebar | Grid |
|--------|--------|---------|------|
| Desktop (≥769px) | Fixed 240px | Fixed | 4 col |
| Tablet (≤768px) | Slide-in | Hamburger | 2 col |
| Mobile (≤420px) | Full-width | Hamburger | 1 col |

---

## Known Limitations

### API-Blocked
- "Completed with Warnings" — No Power BI REST API support
- Credential expiry — Limited metadata
- Capacity overrun — Premium-only
- Zero-row detection — No row count API

### Channels
- ✅ WhatsApp, Email
- ⏸ Teams, Slack, Telegram

---

## Development

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py  # http://localhost:5000
\`\`\`

---

## Docs

- [SESSION.md](docs/SESSION.md) — Current status
- [ARCHITECT.md](docs/ARCHITECT.md) — System design
- [CLAUDE.md](docs/CLAUDE.md) — Dev patterns
- [ERRORS.md](docs/ERRORS.md) — Known issues

---

## License

MIT

**Last Updated:** August 16, 2026  
**Status:** ✅ Responsive UI Complete
