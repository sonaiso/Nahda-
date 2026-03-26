# Nahda-

محرك عربي متعدد الطبقات لتحويل المنطوق إلى بنية مغلقة قابلة للتحقق، ثم إلى استدلال منضبط وقرار قابل للتفسير الكامل.

> **Nahda** is a rule-grounded, explainable Arabic linguistic reasoning framework that models
> utterance closure, claim validation, formal analogy (Qiyas), and fractal awareness across
> twenty layered linguistic and conceptual representations — every step fully traceable.

## Documentation

- [**Architecture Narrative** — رحلة النص الكاملة + مصطلحات + مثال end-to-end](docs/architecture-narrative.md)
- [الوثيقة الهندسية الكاملة لمحرك الوعي الفراكتالي العربي](docs/fractal-arabic-engine-spec.md)
- [خطة إعادة البناء الصارمة - المواصفة التنفيذية الصناعية](docs/strict-rebuild-awareness-engine-spec.md)
- [PRD + Technical Design - المواصفة التنفيذية الكاملة](docs/prd-technical-design-awareness-engine.md)

## System Architecture

### Seven Subsystems — Seven Functional Boundaries

The engine is organised into **seven subsystems** that each own a range of **linguistic layers (L0–L19)**.

| Subsystem | Layers | Purpose |
|-----------|--------|---------|
| Unicode & Orthography | L0–L1 | Decompose raw text; normalise Arabic orthography |
| Phonology & Morphology | L2–L4 | Phoneme atoms; syllabic patterns; triliteral root derivation |
| Lexical Semantics | L5–L8 | Lexeme formation; Wad/Naql/Majaz meaning registry; indications & relations |
| Inference (UCR closure) | L9–L11 | Speech-act classification; Mantuq/Mafhum extraction; Illa modelling |
| Rules & Tarjih | L11–L12 | Rule synthesis; conflict detection; preference weighting |
| Manat & Tanzil | L13–L14 | Case-feature verification; applicability decision (true/false/suspend) |
| Fractal Awareness | L15–L19 | Concept → Scale → Spirit → Inclination → Will-in-act |

> **Note — Subsystems ≠ Layers.**  The **seven subsystems** describe *functional boundaries*
> (FastAPI route groups, Python service modules).  The **twenty layers (L0–L19)** describe
> *epistemic granularity* — each layer adds one kind of linguistic knowledge to the shared
> `run_id` record.  The two counts refer to different axes of the same system.

### UCR (Utterance Closure) vs. Fractal Awareness

These two concepts are often mentioned together but they behave differently:

| | UCR closure (L0–L14) | Fractal Awareness (L15–L19) |
|---|---|---|
| **Goal** | Fully assign every token a linguistic role | Transform closed utterances into an executable decision |
| **Failure mode** | Errors **accumulate** — all gates run; dashboard shows which failed | Chain **stops** on first `suspend` or `false` |
| **Output** | Structured record with quality scores per gate | Single `action ∈ {do, avoid, suspend}` |
| **Analogy** | Compiler that reports *all* warnings | Circuit breaker that trips on first fault |

### Qiyas — Analogical Reasoning

Qiyas transfers a known judgment (**Hukm**) from a source case (**Asl**) to a new case (**Far**)
when they share an effective cause (**Illa**).  The indication type is described by the
canonical `DaalType` enum:

`mutabaqa` · `tadammun` · `iltizam` · `nass` · `zahir` · `mafhum`

> **Naming rule:** always use `DaalType`.  The informal aliases `DaalForm` and `DaalFunction`
> must not appear in code or documentation — they were identified as a source of ambiguity.

### AQL — Arabic Query Layer

**AQL (Arabic Query Layer)** is the cross-system schema vocabulary that makes every artifact
produced by the pipeline addressable and queryable regardless of which layer produced it.

- **Node types:** `GToken`, `Morpheme`, `Root`, `Lexeme`, `Sense`, `Rule`, `ManatUnit`,
  `QiyasUnit`, `ConceptUnit`, and more.
- **Edge types:** `DERIVES_FROM`, `HAS_SENSE`, `GOVERNED_BY`, `TRANSFERS_TO`, `SCALES_TO`, etc.
- **AQL Matrix:** a tabular view of which node types are present/absent for a given `run_id`,
  visualised in the Web Dashboard as the **AQL layer matrix**.

Endpoints: `GET /graph/schema` · `GET /graph/templates` · `POST /graph/analyze`

## Layers (L0–L19)

- L0 Unicode Raw: تفكيك النص إلى Unicode Scalars مع تتبع المواضع.
- L1 Orthographic Normalization: تطبيع إملائي عربي مع قياس نسبة التغيير.
- L2 Phonetic Atomization: تحويل كل حرف إلى Atom نوعه `C/V/S/X`.
- L3 Syllabification: توليد مقاطع عربية هيوريستيكية وأنماطها (`CV`, `CVC`, ...).
- L4 Root-Pattern Derivation: اشتقاق جذور ثلاثية هيوريستيكية + اسم وزن وصيغ الزيادات.
- L5 Lexeme Formation: تشكيل الوحدات المعجمية مع تصنيف الأجزاء النحوية.
- L6–L8 Meaning Registry: تسجيل المعاني بطبقاتها الثلاث (وضع / نقل / مجاز) + دلالة + علاقات.
- L9–L11 Inference: تصنيف الكلام (خبر/إنشاء) + منطوق + مفهوم + علّة.
- L11–L12 Rules & Tarjih: تركيب الأحكام + رصد التعارضات + الترجيح.
- L13–L14 Manat & Tanzil: التحقق من المناط + التنزيل (ينطبق/لا ينطبق/تعليق).
- L15–L19 Fractal Awareness: مفهوم → ميزان → روح → ميل → إرادة فعلية.

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
- `POST /awareness/apply`
- `POST /qiyas/transfer`
- `GET /explain/{run_id}`
- `GET /trace/{run_id}`
- `POST /v1/analyze/unicode`
- `POST /v1/analyze/morphology`
- `POST /v1/analyze/semantics`
- `POST /v1/infer`
- `POST /v1/rule/evaluate`
- `POST /v1/manat/apply`
- `POST /v1/awareness/apply`
- `POST /v1/qiyas/transfer`
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

### Qiyas Tables

- `qiyas_units`
- `qiyas_daal_links`

Phase 2 migration: `migrations/002_semantic_core.sql`

Phase 3 migration: `migrations/003_inference_core.sql`

Phase 4 migration: `migrations/004_manat_tanzil_core.sql`

Phase 5 migration: `migrations/005_explainability_observability.sql`

Phase 6 migration: `migrations/006_awareness_layer.sql`

Graph schema migration: `migrations/007_graph_schema.sql`

Qiyas core migration: `migrations/008_qiyas_core.sql`

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
