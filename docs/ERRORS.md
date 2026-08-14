# ERRORS.md

## Known Issues & Resolutions

### 1. Docker Network Mismatch
**Symptom:** Containers can't communicate after `docker compose down/up`
**Root Cause:** New containers on `pbimonitor_final_pbimonitor-net`, old DB on `pbimonitor_pbimonitor-net`
**Resolution:**
```bash
docker network connect pbimonitor_pbimonitor-net pbimonitor-web
docker network connect pbimonitor_pbimonitor-net pbimonitor-scheduler
docker restart pbimonitor-web pbimonitor-scheduler
```

### 2. Heredoc Failures in Bash
**Symptom:** `<< 'PYEOF'` script doesn't execute, no errors shown
**Root Cause:** Docker/VPS environment limitation
**Resolution:** Use base64-encoded one-liner or `python3 -c` with escaped strings

### 3. Sed Multi-line Replacements Fail Silently
**Symptom:** Complex `sed` commands don't work, no error message
**Root Cause:** Bash terminal limitation
**Resolution:** Write Python patch script with exact string anchors + validation

### 4. MySQL "ADD COLUMN IF NOT EXISTS" Not Supported
**Symptom:** `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` fails on MySQL 8.0
**Root Cause:** MySQL 8.0 doesn't support this syntax
**Resolution:** Use comma-separated `ADD COLUMN` statements

### 5. Encryption Key Mismatch
**Symptom:** `cryptography.fernet.InvalidToken` when decrypting
**Root Cause:** `.env` `ENCRYPTION_KEY` changed or not loaded
**Resolution:** Verify `.env` exists, verify key format, restart containers

### 6. PBI API Throttling
**Symptom:** 429 Too Many Requests from Power BI REST API
**Root Cause:** Scheduler checks too frequently
**Resolution:** Current interval is 30 min (can increase to 60 min if needed)

### 7. WhatsApp Token Expiry
**Symptom:** WhatsApp alerts stop working
**Root Cause:** Meta Graph API token expired
**Resolution:** Regenerate token in Meta Business Manager, update via dashboard

### 8. SMTP Connection Fails
**Symptom:** "Connection refused" or "Authentication failed"
**Root Cause:** Invalid credentials, port, or SMTP server offline
**Resolution:** Test via dashboard `/api/ayarlar/smtp/test`, check port 587/465

### 9. Refresh History Shows No Data
**Symptom:** Chart modal opens but shows empty graph
**Root Cause:** `refresh_history` table is empty (no refreshes recorded yet)
**Resolution:** Wait for scheduler (30 min interval), manually trigger check, verify `monitor.py`

### 10. Azure App Registration Not Multitenant
**Symptom:** Users from other tenants can't sign in
**Root Cause:** App Registration set to "Single tenant"
**Resolution:** Requires Azure AD admin access (currently unavailable)

## Rollback Procedure
1. Stop: `docker compose down`
2. Revert: `git checkout HEAD~1 app.py templates/dashboard.html`
3. Rebuild: `docker compose up -d --build`
4. Network fix: `docker network connect pbimonitor_pbimonitor-net pbimonitor-web`
5. Verify: `docker logs pbimonitor-web --tail 20`
