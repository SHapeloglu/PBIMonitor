# BACKLOG.md

Project roadmap & feature prioritization.

---

## ✅ Completed (Latest First)

### v1.2 — Responsive UI (2026-08-16)
- [x] Dashboard responsive design (hamburger, adaptive grid)
- [x] Mobile breakpoints (768px, 420px)
- [x] Table horizontal scroll wrapper
- [x] Modal mobile-optimized

### v1.1 — Gateway & Refresh History (2026-08-14)
- [x] Refresh history chart (Chart.js, last 20 refreshes)
- [x] Gateway health monitoring + dashboard
- [x] Gateway → Dataset relationship mapping
- [x] Gateway offline cascading alerts

### v1.0 — Core Alarms & Auth (2026-08-01)
- [x] 8 alarm conditions (Consecutive Failure, Zero Duration, Missed Refresh, Duration Anomaly, Schedule Disabled, Gateway Down, Dataset Mismatch, etc.)
- [x] Azure AD OAuth (device-code flow)
- [x] Multi-tenant support (`organizations` endpoint)
- [x] Fernet AES-128 encryption (tokens, credentials)
- [x] WhatsApp alerts (Meta Graph API)
- [x] Email alerts (SMTP per user)
- [x] Alarm log + history
- [x] Docker Compose (3 containers: web, scheduler, db)
- [x] Responsive CSS (hamburger menu, mobile-optimized)

---

## 🔨 High Priority (Next)

### Accessibility & UX Polish
- [ ] WCAG 2.1 compliance audit
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Color contrast validation
- [ ] Screen reader testing
- [ ] Mobile device testing (actual iPhone/Android)
- **Effort:** 2-3 days
- **Blocker:** None

### Dashboard UI Enhancements
- [ ] Hover states on cards & buttons
- [ ] Loading skeletons (instead of "Yükleniyor...")
- [ ] Smooth transitions & animations
- [ ] Dark mode toggle (CSS variables ready)
- [ ] Refresh stats auto-update (WebSocket optional)
- **Effort:** 1-2 days
- **Blocker:** None

### Error Handling & Edge Cases
- [ ] Network timeout recovery
- [ ] Invalid token auto-refresh
- [ ] Session expiry graceful redirect
- [ ] API error messages (user-friendly)
- [ ] Offline mode indication
- **Effort:** 1 day
- **Blocker:** None

---

## 📋 Medium Priority (Backlog)

### Additional Notification Channels
- [ ] **Teams** — Adaptive Card format
- [ ] **Slack** — Webhook integration
- [ ] **Telegram** — Bot API
- **Effort:** 2-3 days each
- **Blocker:** None (integration docs available)

### Database Flexibility
- [ ] **PostgreSQL support** — Replace PyMySQL + MySQL-specific syntax
- [ ] **Oracle support** — Connection pooling, dialect translation
- **Effort:** 2-3 days each
- **Blocker:** None (test database setup required)

### Advanced Monitoring
- [ ] **Scanner API** — Catalog scan for dataset lineage
- [ ] **Service Principal** — Token auto-renewal (instead of user refresh_token)
- [ ] **Capacity Monitoring** — Extract from Premium capacity APIs (if available)
- **Effort:** 2-4 days each
- **Blocker:** Scanner API (requires separate auth), SP (Entra setup)

### Dashboard Features
- [ ] Workspace-level aggregation (sum failures across datasets)
- [ ] Trend analysis (30-day refresh duration trend)
- [ ] Predictive alerts (ML-based anomaly detection)
- [ ] Export reports (CSV, PDF)
- [ ] Custom dashboard layouts
- **Effort:** 3-7 days
- **Blocker:** None

### Data Integration
- [ ] **DBMonitor integration** — SQL Server DMV queries
- [ ] **`.pbix` parser** — DAX anti-pattern detection
- **Effort:** 2-4 days each
- **Blocker:** `.zip` files not provided (awaiting user)

---

## 🚫 Blocked (External Dependency)

### Azure App Registration Multitenant
- **Issue:** App Registration currently set to "Single tenant"
- **Requirement:** Change to "Multitenant" in Azure Portal
- **Owner:** Azure AD admin (`powerbi@bidanismanlik.com` lacks admin rights)
- **Impact:** Non-tenant users cannot sign in
- **Status:** Deferred until admin access granted
- **Workaround:** Deploy separate single-tenant instance per customer

### Power BI REST API Limitations (Unfixable)
These alarms **technically impossible** via Power BI REST API:

1. **"Completed with Warnings"** — Power BI doesn't expose warning list in refresh API
2. **Credential/Token Expiry Detection** — No API for gateway connector credential status
3. **Capacity Overrun Alerts** — Premium capacity metrics not in standard REST API
4. **Zero-Row Detection** — No row count metadata in dataset API
5. **Data Source Connectivity** — No real-time status endpoint

**Resolution:** Requires:
- Power BI Advanced APIs (if available)
- Direct SQL Server DMV queries (requires on-prem access)
- Custom connectors (not viable at scale)

**Current:** These moved to long-term research; marked as "API-Limited" in ERRORS.md

### Missing Input Files (Awaiting User)
- **`.pbix` file** (for DAX parser development)
- **SQL Server instance** (for DMV connection testing)
- **DBMonitor zip** (for integration module)

**Status:** Feature branches blocked until files provided

---

## 📊 Roadmap Timeline

| Version | Focus | ETA | Status |
|---------|-------|-----|--------|
| v1.0 | Core alarms, auth, encryption | ✅ Done | Deployed |
| v1.1 | Gateway monitoring, refresh chart | ✅ Done | Deployed |
| v1.2 | Responsive UI, mobile | ✅ Done | Deployed |
| v1.3 | Accessibility, UX polish | 🔄 Next | In Planning |
| v2.0 | Teams/Slack, PostgreSQL, Scanner API | Q3 2026 | Research |
| v2.1 | Workspace aggregation, trend analysis | Q4 2026 | Deferred |
| v3.0 | ML anomalies, predictive alerts | 2027 | Visionary |

---

## 🎯 Success Metrics

- **Uptime:** 99.5% (SLA target)
- **Alert Latency:** <5 min (from refresh completion to user notification)
- **User Satisfaction:** >4.5/5 (in-app survey)
- **API Response Time:** <200ms (95th percentile)
- **Mobile Usability:** Pass WCAG 2.1 AA

---

## 📝 Notes

- **Blockers reviewed monthly** — Escalate if Azure admin access delays beyond 30 days
- **Community feedback** — GitHub Issues welcome for feature requests
- **Performance:** Monitor MySQL query times; add indexes if needed
- **Security:** Rotate `ENCRYPTION_KEY` quarterly; audit access logs

---

**Last Updated:** August 16, 2026
