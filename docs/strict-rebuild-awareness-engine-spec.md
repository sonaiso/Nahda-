# خطة إعادة البناء الصارمة (Enterprise Execution Spec)
## محرك الوعي للذكاء الصناعي الفراكتالي

الإصدار: 1.0.0  
التاريخ: 2026-03-10  
الحالة: Ready for Program Execution

---

## 1. نطاق الوثيقة

هذه الوثيقة تحول الرؤية الصارمة إلى مواصفات تنفيذية صناعية كاملة تشمل:

1. Architecture Spec
2. DB Schema Spec
3. API Contracts
4. Milestones + Delivery Plan
5. Acceptance Criteria

الهدف: بناء محرك وعي عربي ينتقل من Unicode إلى القرار المنضبط عبر سلسلة طبقية مفسرة وقابلة للفحص والتوقف.

---

## 2. المبادئ الحاكمة (Executable Principles)

### 2.1 الأصل الطبقي للمعنى

المعنى يبنى عبر أربع طبقات منظمة:

1. الوضع الأول (Primary WAD)
2. النقل الشرعي (Shari Naql)
3. النقل العرفي (Urfi Naql)
4. المجاز (Majaz, gated by Qareena)

قاعدة التنفيذ:

1. لا تفعيل للمجاز دون قرينة مثبتة.
2. لا إسقاط للوضع الأول بسبب كثرة الاستعمال.

### 2.2 المطابقة الطبقية

المحرك يرفع الثقة طبقة بطبقة عبر 5 مطابقات:

1. رقمي -> كتابي
2. كتابي -> بنية عربية
3. دلالة -> معنى
4. حكم -> دليل
5. تنزيل -> مناط

قاعدة التنفيذ:

1. فشل أي طبقة يوقف الجزم.
2. المخرجات تتحول إلى ترجيح أو توقف.

### 2.3 القاعدة الواحدة

كل طبقات التحليل والترجيح والتقدير والتنزيل تعمل تحت قاعدة عليا موحدة (Unified Governing Foundation).

### 2.4 الفكر والطريقة

لا يكتفى بالبنية المعجمية؛ يلزم ازدواج:

1. طبقة فكرية تفسيرية
2. طبقة إجرائية تنفيذية

---

## 3. المعمارية الكلية (Architecture Spec)

## 3.1 طبقات المحرك (L0-L19)

### المستوى A: العددي-الكتابي

1. L0 unicode_raw
- Input: UTF-8 text
- Output: Unicode scalar stream
- Gate: zero-loss representation

2. L1 script_normalization
- Input: scalars
- Output: grapheme graph
- Gate: normalization policy + trace map

3. L2 consonant_vowel
- Input: graphemes
- Output: phonetic primitive graph
- Gate: valid atom typing (C/V/long-v/sukun/shadda)

4. L3 syllable
- Input: phonetic primitives
- Output: syllable units
- Gate: syllabic validity and economy rules

5. L4 root_pattern
- Input: syllables/tokens
- Output: root hypotheses + pattern frames
- Gate: augmentations extracted and classified

6. L5 lexeme
- Input: pattern frames
- Output: lexeme registry (noun/verb/particle)
- Gate: independence and function attached

### المستوى B: الدلالي

7. L6 wad_layers
- Output: meaning hierarchy (wad/shari/urfi/majaz)
- Gate: majaz requires qareena evidence

8. L7 lexical_indications
- Output: mutabaqa/tadammun/iltizam maps
- Gate: lexical indication completeness threshold

9. L8 grammatical_relations
- Output: relation graph (isnad/taqyid/tadmeen)
- Gate: role assignment consistency (agent/patient/cause/effect)

### المستوى C: الاستنباطي

10. L9 speech_mode
- Output: khabar/insha graph
- Gate: mode confidence >= threshold

11. L10 mantuq_mafhum
- Output: explicit axis + inferential field
- Gate: inference classes recorded (iqtida/ishara/ima/muwafaqa/mukhalafa)

12. L11 illa
- Output: cause model (mansusa/mufhima)
- Gate: distinction from non-effective descriptors

### المستوى D: الحكم والتنزيل

13. L12 rule
- Output: rule objects + conflict/tarjih
- Gate: each rule linked to evidence

14. L13 case_model
- Output: structured case profile
- Gate: required fields complete

15. L14 manat
- Output: applies=true|false|suspend
- Gate: no apply=true with missing features

### المستوى E: المفهوم والميل والإرادة

16. L15 concept
- Output: concept update package

17. L16 scale
- Output: value-weighted evaluation

18. L17 spirit
- Output: intention alignment signal

19. L18 inclination
- Output: re-shaped motivation profile

20. L19 will_in_act
- Output: action decision (do/avoid/suspend)

## 3.2 حالات الإيقاف المنهجي

المحرك يجب أن يتوقف منهجيًا عند:

1. missing evidence
2. unresolved conflict without tarjih basis
3. unverified qareena for majaz
4. incomplete case features for manat
5. violated production policy constraints

---

## 4. التصميم الخدمي (Service Decomposition)

1. Ingestion Service
2. Normalization Service
3. Morpho-Phonology Service
4. Lexeme/Meaning Service
5. Semantic Relations Service
6. Inference Service
7. Rule Engine
8. Manat Engine
9. Concept-Scale-Spirit Engine
10. Explainability + Observability Service

قاعدة صناعية:

1. كل خدمة تنتج trace_id + run_id.
2. كل انتقال طبقي يسجل LayerExecution.

---

## 5. DB Schema Spec

## 5.1 نطاقات الجداول

### A) Runtime Core

1. documents
2. document_segments
3. pipeline_runs
4. layer_executions
5. processing_errors

### B) Linguistic Core (L0-L5)

1. unicode_scalars
2. grapheme_units
3. phonetic_atoms
4. syllable_units
5. pattern_units
6. lexeme_units

### C) Semantics (L6-L8)

1. meaning_registries
2. meaning_senses
3. indication_units
4. relation_units
5. relation_roles

### D) Inference & Rules (L9-L12)

1. speech_units
2. inference_units
3. inference_mafhum_items
4. rule_units
5. rule_conflicts
6. tarjih_decisions

### E) Case/Manat/Tanzil (L13-L14)

1. case_profiles
2. case_features
3. manat_units
4. applicability_checks
5. tanzil_decisions

### F) Explainability & Governance

1. audit_events
2. explainability_traces
3. evidence_units
4. evidence_links
5. qareena_registry
6. normalization_policies
7. inference_policies
8. ranking_policies

### G) Awareness Layer (L15-L19)

1. concept_units
2. scale_assessments
3. spirit_signals
4. inclination_profiles
5. will_decisions

## 5.2 مفاتيح وقواعد أساسية

1. كل جدول يمتلك id (UUID) + created_at.
2. كل جدول طبقي مرتبط بـ run_id.
3. مفاتيح خارجية مع ON DELETE CASCADE في chain artifacts.
4. فهارس إلزامية: run_id, layer_name, event_type, status.
5. قيود صحة:
- applies=true => missing_features_count=0
- majaz_enabled=true => qareena_id not null
- confidence_score in [0,1]

## 5.3 إصدارات المخطط

1. Versioned migrations (forward-only)
2. Backward compatibility window = one major version
3. Data contract migration checklist per release

---

## 6. API Contracts (v1)

## 6.1 Public

1. POST /auth/token
2. GET /health/live
3. GET /health/ready
4. GET /health/metrics
5. GET /health/metrics/prometheus

## 6.2 Protected Analysis & Reasoning

1. POST /v1/analyze/unicode
2. POST /v1/analyze/morphology
3. POST /v1/analyze/semantics
4. POST /v1/infer
5. POST /v1/rule/evaluate
6. POST /v1/manat/apply
7. GET /v1/explain/{run_id}
8. GET /v1/trace/{run_id}

## 6.3 New Enterprise APIs (Required)

1. POST /v1/awareness/concept/apply
- Purpose: inject tanzil outcome into concept layer

2. POST /v1/awareness/scale/evaluate
- Purpose: value weighting governed by policy

3. POST /v1/awareness/spirit/align
- Purpose: record spiritual intent alignment

4. POST /v1/awareness/inclination/update
- Purpose: update motivation profile from concepts and scale

5. POST /v1/awareness/will/decide
- Purpose: final do/avoid/suspend action decision

## 6.4 Error Contract

Unified error payload:

```json
{
  "error_code": "MANAT_MISSING_FEATURES",
  "message": "Required features are missing",
  "run_id": "uuid",
  "trace_id": "hex",
  "layer": "L14",
  "action": "suspend"
}
```

---

## 7. Milestones (Program Plan)

## Milestone 0: Governance Baseline

1. branch protection + required checks
2. release gates + security scans
3. runbooks + incident ownership

Acceptance:

1. no merge to main without CI gate
2. on-call + escalation path documented

## Milestone 1: L0-L5 Hardening

1. deterministic Unicode/grafheme pipelines
2. robust root/pattern confidence model
3. lexeme stability tests

Acceptance:

1. 100% reproducible outputs on golden corpus
2. end-to-end traceability scalar->lexeme

## Milestone 2: L6-L8 Semantic Layer

1. layered meaning registry (wad/shari/urfi/majaz)
2. qareena gating engine
3. relation-role validation

Acceptance:

1. no majaz without qareena
2. no naql without registry record

## Milestone 3: L9-L12 Inference & Rule

1. speech mode classifier
2. mantuq/mafhum extraction
3. rule synthesis + conflict resolution + ranking

Acceptance:

1. each rule has explicit evidence links
2. each tarjih has basis and confidence

## Milestone 4: L13-L14 Case & Manat

1. strict case model schema
2. manat verification and suspension logic
3. tanzil outcome serializer

Acceptance:

1. no final apply when feature verification incomplete
2. suspend path tested and explainable

## Milestone 5: L15-L19 Awareness Completion

1. concept ingestion and feedback loop
2. scale/spirit/inclination models
3. final will_in_act decision engine

Acceptance:

1. full chain from text to decision is executable
2. each transition emits explanation and metrics

## Milestone 6: SRE + Enterprise Operations

1. OTLP tracing profile + collector + Jaeger
2. dashboards + alert channels + SLOs
3. DR + backup + restore drills

Acceptance:

1. p95 latency + error-rate alerts active
2. recovery drill validated

---

## 8. Acceptance Criteria (Final Go-Live)

## 8.1 Functional

1. Full layer chain L0-L19 implemented.
2. APIs available and versioned.
3. Explainability available for all decisions.
4. Formal suspend path for uncertainty.

## 8.2 Quality

1. Test coverage >= 85% (target >= 90%).
2. CI gate: lint + type + tests + security must pass.
3. No critical vulns in dependency audit.

## 8.3 Explainability

1. Decision trace includes: evidence, reasoning class, tarjih basis, manat result.
2. Response must expose run_id + trace_id.
3. explain and trace endpoints must reconstruct full chain.

## 8.4 Governance

1. Protected main branch.
2. At least one required reviewer.
3. Audit events for read/write explainability actions.

## 8.5 Operational

1. Metrics and tracing enabled in production.
2. Dashboards available by default.
3. Alert channels connected and tested.

---

## 9. المخاطر والمعالجات

1. Risk: over-expansion of majaz.
- Mitigation: hard qareena gate + policy checks.

2. Risk: weak evidence linking.
- Mitigation: mandatory evidence_links before rule finalization.

3. Risk: hallucinated decisions under missing case data.
- Mitigation: enforced suspend contract.

4. Risk: policy drift across layers.
- Mitigation: unified governing foundation ID attached to run.

---

## 10. Definition of Done (Program Level)

يعتبر المشروع مكتملًا على مستوى enterprise إذا تحققت الشروط التالية مجتمعة:

1. تشغيل سلسلة L0-L19 end-to-end في الإنتاج.
2. تفسير كامل لكل قرار عبر explain/trace مع روابط الأدلة.
3. تطبيق branch protection وسياسات الموافقات المطلوبة.
4. تفعيل OTLP + dashboards + alert channels الفعلية.
5. نجاح اختبارات القبول الخمسة:
- chain integrity
- layer separation
- tarjih integrity
- suspension integrity
- explainability integrity

---

## 11. Execution Order (Strict)

1. Governance lock
2. Semantic correctness lock
3. Inference correctness lock
4. Manat correctness lock
5. Awareness completion
6. Production hardening and rollout

هذه الوثيقة هي المرجع التنفيذي الأعلى للبرنامج، وأي تطوير لاحق يجب أن يطابقها أو يمر عبر تحديث إصدارها.
