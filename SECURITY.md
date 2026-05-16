# ShadowSync Security & Compliance Reference

## SOC 2 Audit Readiness Checklist

### ✅ Authentication & Access Control
- [x] All API endpoints require JWT session cookie (`ss_token`)
- [x] Session TTL enforced — tokens expire after configurable hours
- [x] RBAC implemented — `admin`, `analyst`, `auditor` roles with permission matrix
- [x] Admin-only endpoints (retrain, purge) gated by `require_permission()`
- [ ] **TODO**: Switch from cookie-based to OAuth 2.0 / SAML for enterprise SSO

### ✅ Secrets Management
- [x] All API keys loaded from `.env` / environment variables — never hardcoded
- [x] `.env` excluded from git via `.gitignore`
- [x] `.env.example` documents all required variables with placeholder values
- [ ] **TODO**: Migrate to AWS Secrets Manager or HashiCorp Vault for production

### ✅ Data Encryption
- [x] `FIELD_ENCRYPTION_KEY` env var enables Fernet field-level encryption
- [x] `encrypt()` / `decrypt()` helpers available in `app.py`
- [ ] **TODO**: Apply encryption to `card_holder`, `contract_text` fields at rest
- [ ] **TODO**: Enable TLS/HTTPS via reverse proxy (nginx/Caddy) in production

### ✅ Audit Trail
- [x] All human actions logged to `audit_logs` table with timestamp, user, details
- [x] Actions: RECTIFY, DISMISS, FEEDBACK, MODEL_RETRAIN, DATA_PURGE, VENDOR_JUSTIFICATION_SUBMITTED
- [x] Repeat bypass escalation auto-logged (`REPEAT_BYPASS_ESCALATION`)
- [ ] **TODO**: Add IP address logging per request (via `request.client.host`)

### ✅ Data Retention
- [x] `purge_old_records()` deletes resolved shadows older than 7 years
- [x] Monthly auto-scheduler via APScheduler triggers purge automatically
- [x] `POST /api/admin/purge-old-records` for manual trigger with audit log entry
- [ ] **TODO**: Add configurable retention period via env var `DATA_RETENTION_DAYS`

### ✅ API Security
- [x] CORS restricted to `ALLOWED_ORIGINS` env var
- [x] Rate limiting recommended on `/api/ai/chat` (not yet implemented)
- [ ] **TODO**: Add `slowapi` rate limiting middleware
- [ ] **TODO**: Add `Strict-Transport-Security`, `X-Content-Type-Options` headers

### ✅ Dependency Security
- [x] No known CVEs in current dependency set (validate with `pip audit`)
- [ ] **TODO**: Add `pip audit` to CI/CD pipeline
- [ ] **TODO**: Pin all dependency versions in `requirements.txt`

---

## Production Deployment Security Checklist

Before deploying to production:

```bash
# 1. Generate a Fernet encryption key (do this once, store securely)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# → Set as FIELD_ENCRYPTION_KEY in your production environment

# 2. Generate a strong admin password
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → Set as ADMIN_PASSWORD

# 3. Audit dependencies for known CVEs
pip install pip-audit && pip-audit

# 4. Run with HTTPS reverse proxy
# nginx/Caddy in front of uvicorn — never expose port 8000 directly

# 5. Enable HTTPS redirect (uncomment in app.py)
# from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
# app.add_middleware(HTTPSRedirectMiddleware)
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ADMIN_USERNAME` | Yes | Dashboard login username |
| `ADMIN_PASSWORD` | Yes | Dashboard login password (use strong random value) |
| `GROQ_API_KEY` | Yes | Groq LLM API key for AI Copilot |
| `COHERE_API_KEY` | Yes | Cohere API key for semantic analysis |
| `DATABASE_URL` | No | PostgreSQL URL (defaults to SQLite) |
| `FIELD_ENCRYPTION_KEY` | Recommended | Fernet key for field-level encryption |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for critical alerts |
| `ALERT_EMAIL_USER` | No | SMTP email for critical alerts |
| `ALERT_EMAIL_PASS` | No | SMTP password |
| `ALERT_EMAIL_TO` | No | Recipient email for alerts |
| `FIREBASE_CREDENTIALS_PATH` | No | Path to Firebase service account JSON |
| `SAP_HOST` / `SAP_USER` / etc. | No | SAP connector credentials |

---

## Incident Response

If a shadow purchase is flagged as critical:
1. **Immediate**: Email + Slack alerts fire automatically (if configured)
2. **Within 1 hour**: Analyst reviews via Priority Queue
3. **Within 4 hours**: Vendor contacted via portal or direct call
4. **Resolution**: Mark as Resolved or Dismissed with audit log note
5. **Post-incident**: Run `/api/admin/retrain` to update ML model with feedback

---

*Last updated: 2026-05-08*
*Maintained by: ShadowSync Engineering Team*
