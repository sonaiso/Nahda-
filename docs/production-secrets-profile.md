# Production Secrets Profile

This profile defines enterprise production secret requirements for Nahda.

## Required Secrets

- `NAHDA_DB_PASSWORD`
- `NAHDA_AUTH_JWT_SECRET`
- `NAHDA_AUTH_BOOTSTRAP_KEY`
- `NAHDA_ALERT_WEBHOOK_URL`
- `NAHDA_ALERT_SLACK_WEBHOOK_URL`

## Recommended Management

- Use a cloud secret manager and inject secrets at runtime.
- Rotate `NAHDA_AUTH_BOOTSTRAP_KEY` on a schedule.
- Rotate `NAHDA_AUTH_JWT_SECRET` with overlap strategy.
- Restrict database credentials to application role only.

## Startup Guardrails

When `NAHDA_APP_ENV=production`, app startup fails if:

- SQLite is used.
- JWT secret is default or weak (<32 chars).
- bootstrap key is default.
- tracing is enabled but exporter is `none`.
