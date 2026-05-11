# BioLink Production Readiness Checklist

> **Status**: In Progress — Critical fixes applied April 2026

---

## 🔴 CRITICAL — Must Complete Before Production

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | **Rotate ALL secrets** | ⏳ PENDING | Azure DB password, Entra secrets, Superset key, NiFi key — all exposed in git history before purge |
| 2 | **Purge secrets from git history** | ✅ DONE | `.env.local`, `backend-py/.env`, `backend-py/.env.docker` removed via `git-filter-repo` |
| 3 | **Fix CI silent failures** | ✅ DONE | Removed all `\|\| true` fallbacks from `.github/workflows/ci.yml` |
| 4 | **Upgrade deprecated CI actions** | ✅ DONE | Codecov v3 → v4, upload-artifact v3 → v4 |
| 5 | **Switch password hashing to bcrypt** | ✅ DONE | `pbkdf2_sha256` → `bcrypt` with 12 rounds in `security.py` |
| 6 | **Add secret management** | ✅ DONE | `.env.example` template, `.gitignore` hardened, docker-compose uses `${VAR}` interpolation |
| 7 | **Add database migrations (Alembic)** | ✅ DONE | Alembic initialized with `users` + `etl_jobs` tables |
| 8 | **Add TypeScript config** | ✅ DONE | `tsconfig.json` + `tsconfig.node.json` created |
| 9 | **Add package.json scripts** | ✅ DONE | `lint`, `test:unit`, `test:e2e`, `typecheck`, `preview`, `format` |
| 10 | **Fix Python 3.9 datetime.UTC** | ✅ DONE | `datetime.UTC` → `datetime.timezone.utc` for 3.9 compatibility |

---

## 🟡 HIGH — Complete Before Public Launch

| # | Item | Status | Notes |
|---|------|--------|-------|
| 11 | **Persist ETL jobs to PostgreSQL** | ✅ DONE | `ETLJobModel` created in `app/models/etl_job.py` |
| 12 | **Add frontend unit tests** | ⏳ PENDING | Only 1 test exists; need component + hook coverage |
| 13 | **Add backend integration tests** | ⏳ PENDING | Need auth, patient, ETL route integration tests |
| 14 | **Add E2E Playwright tests** | ⏳ PENDING | Only 1 spec exists; need login, patient search, cohort flows |
| 15 | **Add health checks for all services** | ⏳ PENDING | Backend has `/health`; need NiFi, Superset, Ollama |
| 16 | **Add structured logging** | ⏳ PENDING | Need correlation IDs, JSON format, centralized aggregation |
| 17 | **Add rate limiting to all routes** | ⏳ PENDING | Some routes have `@limiter`; need full coverage |
| 18 | **Add input validation / sanitization** | ⏳ PENDING | Zod on frontend; need stricter backend validation |
| 19 | **Add backup & disaster recovery** | ⏳ PENDING | Automated DB backups, point-in-time recovery |
| 20 | **Add log aggregation (Sentry/Loki)** | ⏳ PENDING | Sentry DSN configured but not enforced |

---

## 🟢 MEDIUM — Improve Over Time

| # | Item | Status | Notes |
|---|------|--------|-------|
| 21 | **Version alignment** | ⏳ PENDING | `package.json` says 0.1.0, API says 1.2.0 |
| 22 | **Cloud-native ETL** | ⏳ PENDING | NiFi excluded from Azure; plan Azure Data Factory or Airflow |
| 23 | **Cloud-native LLM** | ⏳ PENDING | Ollama excluded from Azure; plan Azure OpenAI or managed endpoint |
| 24 | **Add pre-commit enforcement** | ⏳ PENDING | Hooks exist but may not be installed by all devs |
| 25 | **Add API versioning** | ⏳ PENDING | No `/v1/` prefix on routes |
| 26 | **Add OpenAPI documentation** | ⏳ PENDING | FastAPI auto-generates; need custom descriptions |
| 27 | **Add performance monitoring** | ⏳ PENDING | Prometheus metrics endpoint exists; need dashboards |
| 28 | **Add load testing** | ⏳ PENDING | Need k6 or Locust scripts for patient search, cohort build |
| 29 | **Add data retention policy** | ⏳ PENDING | Patient data may need GDPR/HIPAA-compliant retention |
| 30 | **Add audit logging** | ⏳ PENDING | Track all data access, exports, admin actions |

---

## 🚀 Deployment Commands

```bash
# 1. Generate secrets
openssl rand -hex 32                    # SECRET_KEY
openssl rand -hex 32                    # SUPERSET_SECRET_KEY
openssl rand -hex 32                    # NIFI_SENSITIVE_PROPS_KEY

# 2. Copy env template
cp .env.example .env
# Edit .env with real values — NEVER commit .env

# 3. Run migrations
cd backend-py
alembic upgrade head

# 4. Build & start
docker-compose up -d --build

# 5. Verify health
curl -s http://localhost:3001/health | jq .
```

---

## ⚠️ Security Reminders

1. **Never commit `.env` files** — `.gitignore` is configured but verify before each push
2. **Rotate secrets after any exposure** — even if history was purged, assume compromise
3. **Use Azure Key Vault in production** — inject secrets via managed identity, not env vars
4. **Enable Azure Entra in production** — disable local auth (`ALLOW_SELF_REGISTRATION=false`)
5. **Review NiFi flow.json** — contains hardcoded `biolink_secret`; use parameter contexts
6. **Review Superset config** — `superset_config.py` has fallback passwords
7. **Enable WAF on Azure** — protect against SQL injection, XSS, bot traffic
8. **Enable DDoS protection** — Azure DDoS Protection Standard on Container Apps
