# الوثيقة الهندسية الكاملة
## محرك الوعي الفراكتالي العربي

الإصدار: 1.0  
التاريخ: 2026-03-10  
الحالة: Draft for Implementation

## 1) الأهداف

### 1.1 الهدف العام

بناء محرك عربي طبقي يبدأ من تمثيل Unicode الخام وينتهي باستنباط الحكم وتنزيله على الواقعة عبر اختبار المناط، مع دورة تغذية راجعة تعيد نتيجة التنزيل إلى طبقات الدلالة والمفاهيم والمعايير.

### 1.2 الأهداف التفصيلية

1. تحويل النص العربي من تمثيل رقمي خام إلى وحدات لغوية قابلة للاستدلال.
2. بناء سلسلة تفسير محكومة: رسم -> صوت -> مقطع -> جذر/وزن -> لفظ -> دلالة -> حجة -> حكم -> مناط -> تنزيل.
3. فصل طبقات المطابقة إلى مستويات مستقلة قابلة للقياس والتحقق.
4. منع القفز من الرمز إلى الحكم دون المرور بطبقات الدلالة والاستدلال.
5. اعتماد ترجيح منضبط قائم على قوة الدليل والقرائن، لا الاحتمال الإحصائي المجرد.

### 1.3 مؤشرات النجاح (KPIs)

1. دقة التطبيع الكتابي العربي >= 99.5% على corpus معياري.
2. دقة استخراج الجذر/الوزن >= 95% على بيانات مضبوطة.
3. دقة تصنيف نوع الدلالة (حقيقة/نقل/مجاز بقرينة) >= 90%.
4. قابلية التتبع (Traceability) 100% من RuleUnit إلى EvidenceUnit.
5. زمن معالجة <= 300ms لكل فقرة قياسية بطول 120 كلمة (بدون استدعاءات خارجية).

---

## 2) المتطلبات

### 2.1 المتطلبات الوظيفية (Functional Requirements)
1. استقبال نص عربي خام UTF-8 وتفكيكه إلى Unicode Scalars.
2. تطبيق سياسة تطبيع قابلة للتكوين (Normalization Policy).
3. بناء وحدات Grapheme مع تتبع الموضع والترتيب.
4. اشتقاق طبقة صوتية (صامت/صائت/سكون/شدة/تنوين).
5. توليد المقاطع واختبار صحة البنية المقطعية.
6. تحليل صرفي لاستخراج الجذر/الوزن والزيادات ونوع البنية (جامد/مشتق).
7. إنشاء Lexeme مع وسم POS والاستقلال الدلالي.
8. إدارة سجل معاني متعدد الطبقات: وضع أصلي، نقل شرعي، نقل عرفي، مجاز بقرينة.
9. استخراج دلالات المطابقة والتضمن والالتزام.
10. بناء Relation Graph للعوامل والنسب (إسناد/تقييد/تضمين).
11. تصنيف الخطاب إلى خبر/إنشاء مع ربط السياق.
12. إنتاج InferenceUnit يتضمن منطوقًا ومفهومًا (اقتضاء/إشارة/إيماء/موافقة/مخالفة).
13. إنشاء RuleUnit يحتوي الحكم، الدليل، رتبة الدليل، وآلية الترجيح.
14. إنشاء ManatUnit لاختبار انطباق الحكم على الواقعة.
15. دعم حالات المخرجات الثلاثة للتنزيل: applies=true|false|suspend.
16. حفظ كامل أثر المعالجة (Audit Trail) عبر run_id موحد.

### 2.2 المتطلبات غير الوظيفية (Non-Functional Requirements)
1. الاتساق: كل وحدة يجب أن تكون مرتبطة بسابقتها ولاحقتها حيث يلزم.
2. القابلية للتوسع: دعم المعالجة الدفعية Batch والمعالجة اللحظية Streaming.
3. القابلية للتفسير: كل قرار استدلالي يجب أن يملك rationale قابلًا للعرض.
4. الأمان: تشفير البيانات الحساسة، وتدقيق صلاحيات الوصول.
5. الاعتمادية: idempotency على مستوى تشغيل pipeline.
6. الرصد: Metrics + Logs + Traces لكل طبقة.
7. التدويل: دعم سياسات متعددة للتطبيع دون كسر النموذج الأساسي.

### 2.3 القيود (Constraints)
1. لا يسمح باستنتاج حكم نهائي دون EvidenceUnit صالح.
2. لا يسمح بتفعيل المجاز دون qareena مثبتة.
3. لا يسمح بالتنزيل دون اختبار شرط/مانع/وصف مؤثر.
4. لا يسمح بإخفاء التعارضات؛ يجب تسجيلها مع نتيجة الترجيح.

### 2.4 الافتراضات (Assumptions)
1. الإدخال عربي فصيح أو قريب منه.
2. يوجد معجم أساس قابل للإثراء.
3. تتوفر قاعدة قرائن (Qareena KB) قابلة للتحديث.

---

## 3) المعمارية

### 3.1 النظرة العامة
المعمارية طبقية فراكتالية من 13 طبقة (0-12). كل طبقة:
1. تقرأ مخرجات الطبقة الأدنى.
2. تنتج تمثيلًا وسيطًا موحدًا.
3. تمرر الناتج للطبقة الأعلى.
4. تسجل جودة المطابقة الخاصة بها.

### 3.2 الطبقات التشغيلية
1. L0 Unicode Raw Layer
2. L1 Orthographic Normalization Layer
3. L2 Phonetic Atomization Layer
4. L3 Syllabification Layer
5. L4 Root-Pattern Derivation Layer
6. L5 Lexeme Formation Layer
7. L6 WAD/Naql/Majaz Layer
8. L7 Lexical Indication Layer
9. L8 Relation & Roles Layer
10. L9 Speech Act Layer (Khabar/Insha)
11. L10 Inference Layer (Mantuq/Mafhum)
12. L11 Rule Synthesis Layer
13. L12 Manat & Tanzil Layer

### 3.3 المكونات التطبيقية (Services)
1. Ingestion Service: إدخال النص والتحقق من الترميز.
2. Normalization Service: تطبيق سياسات التطبيع.
3. Morpho-Phonology Service: طبقات 2-4.
4. Lexicon Service: إدارة Lexeme وMeaning Registry.
5. Semantics Service: دلالات اللفظ والنسب.
6. Inference Service: الاستدلال النصي وإنتاج الحجج.
7. Rule Engine: بناء الحكم وإدارة التعارض/الترجيح.
8. Manat Engine: اختبار الانطباق والتنزيل.
9. Evidence Store: إدارة الأدلة والقرائن.
10. Explainability API: عرض سلسلة التعليل end-to-end.

### 3.4 تدفق البيانات (High-Level Flow)
1. Text Input -> L0 Scalars
2. Scalars -> L1 Graphemes
3. Graphemes -> L2 Atoms -> L3 Syllables
4. Syllables -> L4 Pattern Units -> L5 Lexeme Units
5. Lexemes -> L6 Meaning Registry -> L7 Indication Units
6. Indications + Syntax -> L8 Relations -> L9 Speech Units
7. Speech Units + Evidence -> L10 Inference Units
8. Inference -> L11 Rule Units
9. Rule + Case Facts -> L12 Manat Units -> Tanzil Decision
10. Tanzil Feedback -> تحديث الثقة والمعجم والقرائن

### 3.5 واجهات برمجة التطبيقات (API Contracts)
1. POST /v1/analyze/unicode
2. POST /v1/analyze/morphology
3. POST /v1/analyze/semantics
4. POST /v1/infer
5. POST /v1/rule/evaluate
6. POST /v1/manat/apply
7. GET /v1/explain/{run_id}
8. GET /v1/trace/{run_id}

### 3.6 الحوكمة المنهجية
1. قاعدة الأصل: الحقيقة مقدمة على المجاز.
2. النقل المعتمد يقدم على الاشتراك عند تحقق شروطه.
3. الحكم لا يثبت بلا دليل معتبر.
4. التنزيل لا يثبت بلا تحقق المناط.
5. عند عدم اكتمال الشروط: suspend وليس جزمًا كاذبًا.

---

## 4) الـ Schema (منطقي + تبادلي)

### 4.1 نموذج الكيانات والعلاقات (Logical ER)
1. Document يمتلك Segments.
2. Segment يمتلك UnicodeScalars.
3. UnicodeScalar يرتبط بـ GraphemeUnit.
4. GraphemeUnit يرتبط بـ PhoneticAtom.
5. PhoneticAtom يرتبط بـ SyllableUnit.
6. SyllableUnit يرتبط بـ PatternUnit.
7. PatternUnit يرتبط بـ LexemeUnit.
8. LexemeUnit يرتبط بـ MeaningRegistry.
9. MeaningRegistry يرتبط بـ IndicationUnit.
10. Lexeme/Syntax ينتج RelationUnit.
11. RelationUnit + Context ينتج SpeechUnit.
12. SpeechUnit + Evidence ينتج InferenceUnit.
13. InferenceUnit ينتج RuleUnit.
14. RuleUnit + CaseProfile ينتج ManatUnit.

### 4.2 مخطط JSON تبادلي (Canonical Payload)
```json
{
  "run_id": "uuid",
  "document_id": "uuid",
  "layers": {
    "unicode": [{"idx": 0, "value": 1576}],
    "graphemes": [{"id": "g1", "base": 1576, "marks": []}],
    "phonetic_atoms": [{"id": "p1", "type": "C", "prev": null, "next": "p2"}],
    "syllables": [{"id": "s1", "pattern": "CV", "atoms": ["p1", "p2"]}],
    "patterns": [{"id": "pt1", "root": ["f", "3", "l"], "class": "mushtaq"}],
    "lexemes": [{"id": "lx1", "pos": "noun", "independence": true, "pattern_ref": "pt1"}],
    "meaning_registry": [{"id": "m1", "wad_original": ["L0"], "naql_shari": [], "naql_urfi": [], "majaz_candidates": [], "qareena_required": true}],
    "indications": [{"id": "i1", "mutabaqa": ["x"], "tadammun": ["y"], "iltizam": ["z"]}],
    "relations": [{"id": "r1", "type": "isnadi", "roles": {"agent": "lx1", "patient": null, "cause": null, "effect": null}}],
    "speech": [{"id": "sp1", "type": "khabar"}],
    "inference": [{"id": "inf1", "mantuq": ["..."], "mafhum": {"iqtida": [], "ishara": [], "ima": [], "muwafaqa": [], "mukhalafa": []}}],
    "rules": [{"id": "ru1", "hukm": "...", "evidence_rank": "qat_i|zanni", "tarjih_basis": "strength_of_evidence"}],
    "manat": [{"id": "mn1", "applies": "true|false|suspend", "verified_features": [], "missing_features": []}]
  }
}
```

### 4.3 قواعد التحقق (Validation Rules)
1. كل عنصر يملك معرفًا فريدًا (UUID أو Snowflake ID).
2. لا يجوز وجود RuleUnit دون مرجع InferenceUnit واحد على الأقل.
3. لا يجوز applies=true في ManatUnit مع missing_features غير فارغة.
4. إذا كان المجاز مفعّلًا فلابد من qareena_id صالح.
5. كل Verdict يجب أن يحمل confidence_score ضمن [0,1].

### 4.4 نسخ المخطط (Schema Versioning)
1. النسخة بصيغة semver: MAJOR.MINOR.PATCH.
2. كسر التوافق يتم فقط في MAJOR.
3. يجب دعم قراءتين متزامنتين: current و previous.

---

## 5) قائمة الجداول المطلوبة في قاعدة البيانات

### 5.1 جداول التشغيل الأساسية
1. documents
2. document_segments
3. pipeline_runs
4. layer_executions
5. processing_errors

### 5.2 جداول الطبقات اللغوية
1. unicode_scalars
2. grapheme_units
3. phonetic_atoms
4. syllable_units
5. pattern_units
6. lexeme_units

### 5.3 جداول الدلالة والاستدلال
1. meaning_registries
2. meaning_senses
3. indication_units
4. relation_units
5. relation_roles
6. speech_units
7. inference_units
8. inference_mafhum_items
9. rule_units
10. rule_conflicts
11. tarjih_decisions

### 5.4 جداول المناط والتنزيل
1. case_profiles
2. case_features
3. manat_units
4. tanzil_decisions
5. applicability_checks

### 5.5 جداول الأدلة والقرائن
1. evidence_units
2. evidence_links
3. qareena_registry
4. source_texts
5. citations

### 5.6 جداول الحوكمة والضبط
1. normalization_policies
2. lexical_policies
3. inference_policies
4. ranking_policies
5. audit_events
6. explainability_traces

### 5.7 تعريف حقول الحد الأدنى لكل جدول (Minimum Columns)

#### documents
- id (PK)
- title
- language
- created_at

#### pipeline_runs
- id (PK)
- document_id (FK -> documents.id)
- input_hash
- status
- started_at
- finished_at

#### unicode_scalars
- id (PK)
- run_id (FK -> pipeline_runs.id)
- segment_id (FK -> document_segments.id)
- scalar_value
- position_index
- prev_scalar_id (nullable)
- next_scalar_id (nullable)

#### grapheme_units
- id (PK)
- run_id (FK)
- base_scalar_id (FK -> unicode_scalars.id)
- marks_json
- norm_class
- token_index
- char_index

#### phonetic_atoms
- id (PK)
- run_id (FK)
- grapheme_id (FK)
- atom_type
- lower_features_json
- prev_atom_id (nullable)
- next_atom_id (nullable)

#### syllable_units
- id (PK)
- run_id (FK)
- pattern
- atoms_json
- prev_syllable_id (nullable)
- next_syllable_id (nullable)

#### pattern_units
- id (PK)
- run_id (FK)
- root_c1
- root_c2
- root_c3
- pattern_name
- class_type
- augmentations_json
- semantic_shift_json

#### lexeme_units
- id (PK)
- run_id (FK)
- surface_form
- pos
- independence
- pattern_id (FK -> pattern_units.id)
- lemma

#### meaning_registries
- id (PK)
- run_id (FK)
- lexeme_id (FK -> lexeme_units.id)
- qareena_required
- notes

#### meaning_senses
- id (PK)
- registry_id (FK -> meaning_registries.id)
- sense_type (wad_original|naql_shari|naql_urfi|majaz)
- gloss
- priority_rank

#### indication_units
- id (PK)
- run_id (FK)
- lexeme_id (FK)
- mutabaqa_json
- tadammun_json
- iltizam_json

#### relation_units
- id (PK)
- run_id (FK)
- relation_type
- source_ref
- target_ref

#### speech_units
- id (PK)
- run_id (FK)
- segment_id (FK -> document_segments.id)
- speech_type (khabar|insha)
- prev_speech_id (nullable)
- next_speech_id (nullable)

#### inference_units
- id (PK)
- run_id (FK)
- speech_id (FK -> speech_units.id)
- mantuq_json
- illa_explicit_json
- illa_implied_json
- confidence_score

#### inference_mafhum_items
- id (PK)
- inference_id (FK -> inference_units.id)
- mafhum_type (iqtida|ishara|ima|muwafaqa|mukhalafa)
- content

#### rule_units
- id (PK)
- run_id (FK)
- inference_id (FK -> inference_units.id)
- hukm_text
- evidence_rank
- tarjih_basis
- confidence_score

#### case_profiles
- id (PK)
- external_case_id
- description
- created_at

#### case_features
- id (PK)
- case_id (FK -> case_profiles.id)
- feature_key
- feature_value
- verification_state

#### manat_units
- id (PK)
- run_id (FK)
- rule_id (FK -> rule_units.id)
- case_id (FK -> case_profiles.id)
- verified_features_json
- missing_features_json
- applies_state (true|false|suspend)

#### tanzil_decisions
- id (PK)
- manat_id (FK -> manat_units.id)
- final_decision
- rationale
- decided_at

### 5.8 الفهارس المقترحة (Indexes)
1. idx_unicode_run_pos on unicode_scalars(run_id, position_index)
2. idx_grapheme_run_token on grapheme_units(run_id, token_index)
3. idx_lexeme_run_pos on lexeme_units(run_id, pos)
4. idx_sense_registry_type on meaning_senses(registry_id, sense_type)
5. idx_rule_run_conf on rule_units(run_id, confidence_score)
6. idx_manat_rule_case on manat_units(rule_id, case_id)
7. idx_tanzil_manat on tanzil_decisions(manat_id)

### 5.9 القيود المرجعية (FK/Checks)
1. ON DELETE CASCADE بين pipeline_runs وكل جداول المخرجات التابعة.
2. CHECK(applies_state IN ('true','false','suspend')) في manat_units.
3. CHECK(confidence_score >= 0 AND confidence_score <= 1) في inference_units وrule_units.
4. UNIQUE(run_id, position_index) في unicode_scalars.

---

## 6) سياسة المطابقة الأربع (Quality Gates)

1. Gate A: مطابقة التمثيل الرقمي للرسم.
2. Gate B: مطابقة الرسم للبنية العربية.
3. Gate C: مطابقة الدلالة للمعنى.
4. Gate D: مطابقة الحكم للدليل.
5. Gate E: مطابقة التنزيل للمناط.

أي فشل في Gate من A-E ينتج:
1. تخفيض الثقة.
2. تسجيل سبب الفشل.
3. إما إعادة المعالجة أو تعليق النتيجة (suspend).

---

## 7) خارطة تنفيذ مرحلية

### المرحلة 1 (MVP-Text Core)
1. L0-L4 + جداولها.
2. API: /analyze/unicode و /analyze/morphology.
3. قياسات التطبيع والمقاطع والجذر/الوزن.

### المرحلة 2 (Semantic Core)
1. L5-L8 + المعجم متعدد الطبقات.
2. API: /analyze/semantics.
3. تفعيل دلالات المطابقة/التضمن/الالتزام.

### المرحلة 3 (Inference Core)
1. L9-L11.
2. API: /infer و /rule/evaluate.
3. دعم إدارة التعارض والترجيح.

### المرحلة 4 (Manat & Tanzil)
1. L12 + case profiling.
2. API: /manat/apply.
3. تفعيل قرارات applies/suspend مع rationale كامل.

### المرحلة 5 (Production Readiness)

1. Explainability API + Observability كاملة.
2. اختبارات ضغط وأمن واتساق مرجعي.
3. توثيق واجهات الإنتاج وسياسات الحوكمة.

---

## 8) مخرجات التسليم المطلوبة

1. وثيقة المتطلبات المعتمدة (هذه الوثيقة).
2. مخطط ERD فعلي.
3. ملفات migration SQL لكل الجداول.
4. OpenAPI Spec للإجراءات الأساسية.
5. مجموعة بيانات اختبار معيارية لكل طبقة.
6. لوحة قياسات KPI وربطها بـ pipeline_runs.

---

## 9) قرار هندسي مركزي

المحرك لا يتعامل مع Unicode كمعنى، بل كطبقة قياس أولى. المعنى والحكم والمناط لا ينتجون إلا عبر طبقات وسيطة موثقة وقابلة للتدقيق. بذلك يصبح الانتقال من الرمز إلى القرار انتقالًا مفسرًا لا قفزة غير منضبطة.
