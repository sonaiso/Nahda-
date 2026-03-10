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

- `POST /analyze/unicode`
- `POST /analyze/morphology`
- `POST /analyze/semantics`
- `POST /v1/analyze/unicode`
- `POST /v1/analyze/morphology`
- `POST /v1/analyze/semantics`

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

## Run Locally

```bash
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI:

- `http://localhost:8000/docs`

## Tests

```bash
python -m pytest -q
```
