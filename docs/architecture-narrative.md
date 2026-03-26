# Architecture Narrative — Nahda Arabic Reasoning Engine

> **محرك النهضة للاستدلال العربي — وثيقة السرد المعماري**

This document explains how a raw Arabic text travels through the Nahda
engine from the first Unicode scalar to an actionable, fully traceable
decision.  It is a narrative, human-readable companion to the
code-level specifications in `docs/fractal-arabic-engine-spec.md` and
`docs/strict-rebuild-awareness-engine-spec.md`.  JSON and schema examples
in this document are simplified for exposition; the canonical and complete
API contracts are defined by the code-level specifications.

---

## 1. System Overview in One Sentence

> Nahda is a rule-grounded, explainable Arabic linguistic reasoning framework
> that models utterance closure, claim validation, formal analogy, and fractal
> awareness across twenty layered linguistic and conceptual representations —
> every step fully traceable and suspendable.

---

## 2. Subsystems and Their Functions

The engine is composed of **seven subsystems**.  Each subsystem owns a
contiguous range of linguistic layers (L0–L19).  The subsystem boundaries
answer the question "what kind of work is being done here?" while the
layer numbers answer "at what level of abstraction?".

| # | Subsystem | Layers | One-line purpose |
|---|-----------|--------|-----------------|
| 1 | **Unicode & Orthography** | L0–L1 | Decompose raw text into Unicode scalars; normalise Arabic orthography |
| 2 | **Phonology & Morphology** | L2–L4 | Atomise phonemes, build syllabic patterns, derive triliteral roots |
| 3 | **Lexical Semantics** | L5–L8 | Form lexemes; register Wad/Naql/Majaz meanings; map indications and relations |
| 4 | **Inference (UCR closure)** | L9–L11 | Classify speech acts; extract Mantuq and Mafhum; model the effective cause (Illa) |
| 5 | **Rules & Tarjih** | L11–L12 | Synthesise legal-logical rules; detect conflicts; apply preference weighting |
| 6 | **Manat & Tanzil** | L13–L14 | Verify case features; determine applicability (true / false / suspend) |
| 7 | **Fractal Awareness** | L15–L19 | Concept → Scale → Spirit → Inclination → Will-in-act |

### Why "subsystems" ≠ "layers"

The **seven subsystems** describe *functional boundaries* — they map to
individual FastAPI route groups and Python service modules.  The
**twenty layers (L0–L19)** describe *epistemic granularity* — every layer
adds one kind of linguistic knowledge to the shared `run_id` record.
You will therefore see both numbers in the documentation; they refer to
different axes of the same system.

### Qiyas — Analogical Reasoning Subsystem

Qiyas is a cross-cutting subsystem that can be invoked after the Inference
layer (L9–L11) to transfer a known judgment from a source case (**Asl**) to
a new case (**Far**) via an effective cause (**Illa**).

```
Asl (known judgment) ──── Illa (effective cause) ────► Far (new judgment)
                               │
                          DaalType link
                    (mutabaqa / tadammun / iltizam /
                       nass / zahir / mafhum)
```

**Canonical naming rule — `DaalType`**

All code and documentation must use the single enum `DaalType` to
describe the indication mechanism.  The informal aliases **`DaalForm`**
and **`DaalFunction`** must not appear anywhere; they represent the same
concept under different informal names and are a known source of
confusion in the API surface.

---

## 3. UCR Closure vs. Fractal Awareness — Key Distinction

These two concepts are often mentioned together but they operate
differently:

| Dimension | UCR closure (L0–L14) | Fractal Awareness (L15–L19) |
|-----------|---------------------|-----------------------------|
| **Goal** | Close an utterance — assign every token a fully specified linguistic role | Transform closed utterances into an executable will-decision |
| **Failure mode** | Errors **accumulate** — all 14+ stages run; the dashboard shows which gates failed | Chain **stops** on the first `suspend` or `false` decision |
| **Output** | A structured record with quality scores per gate | A single `action ∈ {do, avoid, suspend}` with a confidence score |
| **Analogy** | Like a compiler that reports *all* warnings | Like a circuit breaker that trips on the first fault |

This asymmetry is intentional: UCR gives you a diagnostic dashboard for
every layer of the text; Fractal gives you a safe binary decision.

---

## 4. AQL — Arabic Query Layer

**AQL (Arabic Query Layer)** is the cross-system schema vocabulary that
makes every artifact produced by the pipeline addressable and queryable
regardless of which layer produced it.

AQL defines:

* **Node types** — `GToken`, `Morpheme`, `Root`, `Lexeme`, `Sense`,
  `Rule`, `ManatUnit`, `QiyasUnit`, `ConceptUnit`, and more.
* **Edge types** — `DERIVES_FROM`, `HAS_SENSE`, `GOVERNED_BY`,
  `TRANSFERS_TO`, `SCALES_TO`, etc.
* **AQL Matrix** — a tabular view of which node types are present or
  absent for a given `run_id`, used in the Web Dashboard to visualise
  coverage across all 20 layers.

The `GET /graph/schema` endpoint returns the full AQL node/edge catalogue.
The `POST /graph/analyze` endpoint builds an in-memory AQL graph for any
input text, which the dashboard visualises as the **AQL layer matrix**.

---

## 5. End-to-End Example — رحلة النص الكاملة

Input text: **`"لا كتاب في البيت"`**

### Step 1 — Unicode & Orthography (L0–L1)

```http
POST /analyze/unicode
{ "text": "لا كتاب في البيت" }
```

```json
{
  "run_id": "run-001",
  "normalized_text": "لا كتاب في البيت",
  "metrics": { "input_length": 16, "normalization_ratio": 1.0 }
}
```

All Unicode scalars are decoded; orthographic normalisation confirms no
alef-wasla/hamza collisions.  Gate L0 ✓, Gate L1 ✓.

### Step 2 — Phonology & Morphology (L2–L4)

```http
POST /analyze/morphology
{ "text": "لا كتاب في البيت" }
```

```json
{
  "run_id": "run-001",
  "patterns": [
    { "token": "كتاب", "root": ["ك","ت","ب"], "pattern_name": "فِعَال" },
    { "token": "البيت", "root": ["ب","ي","ت"], "pattern_name": "فَيْعَل" }
  ],
  "metrics": { "triliteral_root_ratio": 0.67 }
}
```

Gates L2–L4 ✓.

### Step 3 — Lexical Semantics (L5–L8)

```http
POST /analyze/semantics
{ "text": "لا كتاب في البيت" }
```

```json
{
  "run_id": "run-001",
  "lexemes": [
    { "token": "كتاب", "lemma": "كتاب", "pos": "noun", "independence": true },
    { "token": "البيت", "lemma": "بيت", "pos": "noun", "independence": true }
  ],
  "metrics": { "lexeme_count": 4, "independent_lexeme_ratio": 0.5 }
}
```

Wad meaning registered for كتاب and بيت.  Gates L5–L8 ✓.

### Step 4 — Inference / UCR Closure (L9–L11)

```http
POST /infer
{ "text": "لا كتاب في البيت" }
```

```json
{
  "run_id": "run-001",
  "inference": [{
    "speech_type": "khabar",
    "mantuq": ["لا","كتاب","في","البيت"],
    "mafhum": { "mukhalafa": ["negation_implies_opposite"] },
    "confidence_score": 0.8
  }],
  "metrics": { "inference_count": 1, "avg_inference_confidence": 0.8 }
}
```

Mantuq: explicit negation of a book's presence.
Mafhum mukhalafa: the opposite (a book *is* present elsewhere) is implied.
Gate L9–L11 ✓.

### Step 5 — Rules & Tarjih (L11–L12)

```http
POST /rule/evaluate
{ "text": "لا كتاب في البيت" }
```

```json
{
  "run_id": "run-001",
  "rules": [
    { "hukm_text": "prohibit:كتاب", "evidence_rank": "qat_i", "confidence_score": 0.9 }
  ],
  "metrics": { "rule_count": 1, "conflict_count": 0 }
}
```

The `لا` before كتاب triggers a prohibit rule at qat'i (certain) strength.
Gate L12 ✓.

### Step 6 — Manat & Tanzil (L13–L14)

```http
POST /manat/apply
{
  "text": "لا كتاب في البيت",
  "case_features": [{"feature_key": "كتاب", "feature_value": "present", "verification_state": "verified"}]
}
```

```json
{
  "run_id": "run-001",
  "manat": [{
    "hukm_text": "prohibit:كتاب",
    "applies_state": "true",
    "confidence_score": 0.9,
    "rationale": "rule prohibit evaluated with feature كتاب=present"
  }]
}
```

The prohibition applies because كتاب is present in the case.  Gates L13–L14 ✓.

### Step 7 — Qiyas Analogical Transfer

Now apply the same prohibition to an analogous case (مجلة = magazine):

```http
POST /qiyas/transfer
{
  "text": "لا كتاب في البيت",
  "transfers": [{
    "asl_text": "لا كتاب في البيت",
    "asl_judgment": "prohibit:كتاب",
    "far_text": "لا مجلة في البيت",
    "illa_description": "المطبوع الورقي",
    "daal_type": "mutabaqa",
    "evidence": [{"text": "الكتاب والمجلة كلاهما مطبوع ورقي", "source": "nass", "strength": "zanni"}]
  }]
}
```

```json
{
  "run_id": "run-001",
  "transfers": [{
    "asl_judgment": "prohibit:كتاب",
    "far_text": "لا مجلة في البيت",
    "transferred_judgment": "prohibit:كتاب",
    "transfer_state": "valid",
    "daal_type": "mutabaqa",
    "confidence_score": 0.75
  }]
}
```

The Illa (printed paper object) links كتاب to مجلة; the prohibition transfers.

### Step 8 — Fractal Awareness (L15–L19)

```http
POST /awareness/apply
{ "run_id": "run-001" }
```

```json
{
  "run_id": "run-001",
  "concept": { "concept_key": "post_tanzil_awareness", "confidence_score": 0.82 },
  "scale":   { "scale_name": "sharia_value", "value_score": 0.74 },
  "spirit":  { "alignment_score": 0.71, "remembrance_level": "moderate" },
  "inclination": { "tendency": "engage", "intensity_score": 0.9 },
  "will":    { "action": "do", "confidence_score": 0.75 }
}
```

The Fractal Awareness chain confirms: engage → do.  Full pipeline complete.

### Step 9 — Full Trace

```http
GET /explain/run-001
```

Returns a complete audit trail linking every decision back to the original
Unicode scalars through all 20 layers.

---

## 6. Quality Gates Summary

| Gate | Covers | Failure action |
|------|--------|----------------|
| G1 Numeric→Graphic | L0–L1 | Report normalisation error; continue |
| G2 Graphic→Structure | L2–L4 | Flag invalid syllable; continue |
| G3 Meaning | L5–L8 | Suspend Majaz without qareena |
| G4 Judgment | L9–L12 | Record conflict; apply tarjih |
| G5 Application | L13–L14 | Suspend if features missing |
| G6 Awareness | L15–L19 | `will.action = suspend` if inclination = suspend |

---

## 7. Terminology Quick-Reference

| Term | Arabic | Meaning in this system |
|------|--------|----------------------|
| Asl | أصل | Source case with a known judgment |
| CCR | — | Constrained Claims Record — inference units with evidence contracts |
| DaalType | دلالة | Canonical enum for indication type (replaces DaalForm / DaalFunction) |
| Far | فرع | Target case seeking a transferred judgment |
| Fractal | فراكتال | The L15–L19 awareness chain (stops on first suspend) |
| Hukm | حكم | Legal-logical judgment |
| Illa | علة | Effective cause linking Asl to Far in Qiyas |
| Mafhum | مفهوم | Implicit meaning (mukhalafa, muwafaqa, …) |
| Manat | مناط | The case feature to which a rule is tethered |
| Mantuq | منطوق | Explicit meaning of an utterance |
| Qiyas | قياس | Analogical reasoning — transfers Hukm from Asl to Far |
| Tanzil | تنزيل | Application of a rule to a concrete case |
| Tarjih | ترجيح | Preference-weighting for conflicting rules |
| UCR | — | Utterance Closure Record — the full L0–L14 pipeline (accumulates all gate results) |
| WAD | وضع | Primary (positional) meaning of a word |
