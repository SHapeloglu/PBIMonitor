# CLAUDE.md

## Critical Environment Patterns

### Heredoc Failures
**Do NOT use:** `<< 'PYEOF'` syntax — fails silently in this Docker/Bash environment.
**Always use:** `python3 -c` with escaped strings, or base64-encode script.

### Multi-line Sed
**Do NOT use:** Complex multi-line `sed` replacements — fail silently.
**Always use:** Python patch script with exact string anchors + `count() != 1` safety guard.

### Docker Network Issues
After `docker rm -f` + recreation:
- New containers join: `pbimonitor_final_pbimonitor-net`
- Old DB container on: `pbimonitor_pbimonitor-net` (no rebuild)
- **Fix:** Always run `docker network connect pbimonitor_pbimonitor-net <container>` after restart

### MySQL 8.0 Quirks
- Does NOT support `ADD COLUMN IF NOT EXISTS`
- Use comma-separated `ADD COLUMN` statements instead
- Prepare patch script to validate before deployment

## Session Management Protocol

1. **Self-monitor:** Every ~10 messages, check if session exceeds ~15 messages or involves heavy file ops
2. **Close sequence when needed:**
   - Update SESSION.md (current status)
   - Update TASKS.md (completed/pending)
   - Update ARCHITECT.md (system design)
   - Update DB_SCHEMA.md (table structure)
   - Update ERRORS.md (known issues)
   - Git commit + push all docs
   - Instruct user to download zip

3. **Session entry (next time):**
   - Fetch user's zip with all .md files
   - Reconstruct context from CLAUDE.md + SESSION.md + ARCHITECT.md
   - Continue from exact point

## Workflow
1. Generate command
2. User runs on server, pastes terminal output
3. Claude diagnoses + responds
4. Repeat until feature complete

## User Interaction Style
- **Terse:** Minimal explanation, direct action
- **User trusts:** Frequently responds "önerin nedir" (what's your recommendation)
- **No unnecessary detail:** Just the command + expected output

## Patch-Deploy Cycle
1. Write Python patch script (exact string anchors)
2. Test on local clone (py_compile validation)
3. Base64 encode + one-liner for sunucu
4. Run on sunucu → verify output
5. Docker rebuild → network connect → restart
6. Verify logs
7. Git commit
