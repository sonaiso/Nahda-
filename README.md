# Nahda-

MVP صناعي لتنفيذ المرحلة الأولى من محرك الوعي الفراكتالي العربي (L0-L4) مع API جاهز للتشغيل.

## Documentation

- [الوثيقة الهندسية الكاملة لمحرك الوعي الفراكتالي العربي](docs/fractal-arabic-engine-spec.md)

## MVP Scope (L0-L4)

- L0 Unicode Raw: تفكيك النص إلى Unicode Scalars مع تتبع المواضع.
- L1 Orthographic Normalization: تطبيع إملائي عربي مع قياس نسبة التغيير.
- L2 Phonetic Atomization: تحويل كل حرف إلى Atom نوعه `C/V/S/X`.
- L3 Syllabification: توليد مقاطع عربية هيوريستيكية وأنماطها (`CV`, `CVC`, ...).
- L4 Root-Pattern Derivation: اشتقاق جذور ثلاثية هيوريستيكية + اسم وزن وصيغ الزيادات.

## API Endpoints

Public endpoints:

- `POST /auth/token`
- `GET /health/live`
- `GET /health/ready`
- `GET /health/metrics`
- `GET /health/metrics/prometheus`

Protected endpoints (Bearer token required):

- `POST /analyze/unicode`
- `POST /analyze/morphology`
- `POST /analyze/semantics`
- `POST /infer`
- `POST /rule/evaluate`
- `POST /manat/apply`
- `GET /explain/{run_id}`
- `GET /trace/{run_id}`
- `POST /v1/analyze/unicode`
- `POST /v1/analyze/morphology`
- `POST /v1/analyze/semantics`
- `POST /v1/infer`
- `POST /v1/rule/evaluate`
- `POST /v1/manat/apply`
- `GET /v1/explain/{run_id}`
- `GET /v1/trace/{run_id}`

### Auth Token Request

```json
{
	"subject": "dev-user",
	"role": "service",
	"bootstrap_key": "local-dev-bootstrap-key"
}
```

Use token as `Authorization: Bearer <access_token>`.

### Request Body

```json
{
	"text": "إِنَّ الكِتَاب"
}
```

### Unicode Metrics

- `input_length`
- `normalized_length`
- `changed_characters`
- `normalization_ratio`

### Morphology Metrics

- `token_count`
- `syllable_count`
- `avg_syllables_per_token`
- `valid_syllable_ratio`
- `triliteral_root_ratio`

### Semantics Metrics

- `lexeme_count`
- `independent_lexeme_ratio`
- `indication_coverage_ratio`
- `relation_count`

## Database Tables (MVP)

### Core Runtime

- `documents`
- `document_segments`
- `pipeline_runs`
- `layer_executions`
- `processing_errors`

### L0-L4 Tables

- `unicode_scalars`
- `grapheme_units`
- `phonetic_atoms`
- `syllable_units`
- `pattern_units`

Migration SQL: `migrations/001_mvp_l0_l4.sql`

Phase 2 migration: `migrations/002_semantic_core.sql`

Phase 3 migration: `migrations/003_inference_core.sql`

Phase 4 migration: `migrations/004_manat_tanzil_core.sql`

Phase 5 migration: `migrations/005_explainability_observability.sql`

## Run Locally

```bash
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

With PostgreSQL (recommended):

```bash
cp .env.example .env
docker compose up -d db
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app will use `NAHDA_DATABASE_URL` from `.env`.

Production profile template:

- `.env.production.example`
- `docs/production-secrets-profile.md`

## Run With Docker Compose

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Health endpoints:

- `GET /health/live`
- `GET /health/ready`
- `GET /health/metrics`

Rate limiting is enabled by default and configurable through `.env`.

Observability defaults:

- every response includes `X-Request-ID`
- every response includes `X-Trace-ID`
- structured access logs are emitted per request
- in-memory operational metrics are exposed via `GET /health/metrics`
- Prometheus-formatted metrics are exposed via `GET /health/metrics/prometheus`

OpenTelemetry tracing:

- request span is created per HTTP call (`http.request`)
- deep pipeline spans are created in API layers (unicode/morphology/semantics/inference/rule/manat/explain/trace)
- exporter mode is controlled by `.env`: `NAHDA_OTEL_EXPORTER=none|console|otlp`

OTLP collector profile:

- `docker-compose.otlp.yml`
- `ops/observability/otel-collector.yml`

Swagger UI:

- `http://localhost:8000/docs`

## Tests

```bash
python -m pytest -q
```

CI quality gate runs:

- `ruff check .`
- `mypy`
- `bandit -q -r app`
- `pip-audit`
- `pytest -q` with coverage fail-under `85%`

## Dashboards And Alerts Baseline

Start stack (API + DB + Prometheus + Grafana + Alertmanager):

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up --build
```

Start stack with OTLP collector + Jaeger:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml -f docker-compose.otlp.yml up --build
```

Services:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)
- Alertmanager: `http://localhost:9093`
- Jaeger UI (with OTLP profile): `http://localhost:16686`

Provisioned assets:

- Prometheus scrape + alert rules: `ops/observability/prometheus.yml`, `ops/observability/alert_rules.yml`
- Alertmanager baseline config: `ops/observability/alertmanager.yml`
- Grafana datasource + dashboard provisioning under `ops/observability/grafana/`

## Enterprise Governance

Branch protection policy and automation:

- `ops/github/branch_protection.md`
- `ops/github/apply_branch_protection.sh`

Apply policy (example):

```bash
bash ops/github/apply_branch_protection.sh sonaiso Nahda- main
```
