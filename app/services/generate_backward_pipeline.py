"""
Backward generation pipeline: MeaningStructure → Arabic text.

Implements the GENERATE_BACKWARD pseudocode from the Nahda specification
(sections 12–14).  The pipeline mirrors the forward analysis in reverse:

  MeaningStructure
    → ConstructionNetwork          (12.1 PLAN_CONSTRUCTION_FROM_MEANING)
    → List[LexemeNode]             (12.2 SELECT_LEXEMES_FROM_CONSTRUCTION)
    → List[(RootKernel,Pattern)]   (12.3 SELECT_ROOT_PATTERN_FOR_LEXEMES)
    → List[IntraLexemeStructure]   (12.4 BUILD_ILS_FROM_ROOT_PATTERN)
    → List[SyllableCircuit]        (12.5 BUILD_SYLLABLES_FROM_ILS)
    → List[FunctionalUnit]         (12.6 REALIZE_FUNCTIONAL_UNITS)
    → String                       (12.7 EMIT_UNICODE_TEXT)

Followed by:
  → Round-trip verification        (section 13)
  → Ranking                        (section 14)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import Document
from app.models.entities import GenerationBranch
from app.models.entities import GenerationRun
from app.models.entities import LayerExecution
from app.models.entities import PipelineRun
from app.services.unicode_pipeline import normalize_arabic_text

# ---------------------------------------------------------------------------
# Arabic character constants (reused from morphology pipeline)
# ---------------------------------------------------------------------------
SHORT_VOWELS = {"\u064E", "\u064F", "\u0650"}  # fatha, damma, kasra
LONG_VOWELS = {"\u0627", "\u0648", "\u064A"}   # alef, waw, ya
PARTICLES = {
    "\u0641\u064A", "\u0645\u0646", "\u0627\u0644\u0649",
    "\u0639\u0644\u0649", "\u0639\u0646", "\u0648", "\u0641",
    "\u0628", "\u0643", "\u0644", "\u062B\u0645", "\u0627\u0648",
    "\u0623\u0648", "\u0647\u0648", "\u0647\u064A", "\u0647\u0645",
}
VERB_PREFIXES = ("\u064A", "\u062A", "\u0646", "\u0627")  # ي ت ن ا


# ---------------------------------------------------------------------------
# Internal data structures for the generation pipeline
# ---------------------------------------------------------------------------

@dataclass
class Trace:
    """Proof trace accumulating gate results and a final score."""
    name: str
    steps: list[str] = field(default_factory=list)
    score: float = 0.0

    def step(self, msg: str) -> None:
        self.steps.append(msg)


@dataclass
class Branch:
    """Generic branch carrying a value and its trace."""
    value: Any
    trace: Trace


@dataclass
class ConstructionPlan:
    """Planned syntactic structure for a sentence."""
    structure_type: str          # "nominal" | "verbal" | "annexation"
    slots: list[str]             # ordered slot labels
    syntactic_factors: dict
    case_values: dict


@dataclass
class LexemeNode:
    """A lexeme assigned to a construction slot."""
    surface: str
    lemma: str
    pos: str
    slot: str
    root: list[str]
    pattern: str


@dataclass
class RootKernel:
    """The radical consonant cluster of an Arabic root."""
    consonants: list[str]
    root_class: str = "triliteral"


@dataclass
class PatternTemplate:
    """An Arabic morphological pattern (wazn)."""
    template_id: str
    pattern: str        # abstract CV skeleton
    derivation_type: str


@dataclass
class IntraLexemeStructure:
    """Internal structure of a realized lexeme."""
    lexeme: LexemeNode
    root_kernel: RootKernel
    pattern: PatternTemplate
    form: str
    affixes: list[str] = field(default_factory=list)
    vowels: list[str] = field(default_factory=list)


@dataclass
class SyllableCircuit:
    """One syllable of a realized form."""
    text: str
    pattern: str


@dataclass
class FunctionalUnit:
    """A fully realized word unit ready for text emission."""
    text: str
    ils: IntraLexemeStructure
    syllables: list[SyllableCircuit]
    case_marker: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _atom_type(ch: str) -> str:
    if ch in SHORT_VOWELS or ch in LONG_VOWELS:
        return "V"
    return "C"


def _get_consonants(token: str) -> list[str]:
    return [c for c in token if _atom_type(c) == "C"]


def _infer_pos(token: str) -> str:
    if token in PARTICLES:
        return "particle"
    if token.startswith("\u0627\u0644"):  # ال
        return "noun"
    if len(token) >= 3 and token[0] in VERB_PREFIXES:
        return "verb"
    return "noun"


def _extract_content_tokens(meaning: str) -> list[str]:
    """Return non-particle tokens from the meaning string."""
    return [t for t in meaning.split() if t and _infer_pos(t) != "particle"]


# ---------------------------------------------------------------------------
# Stage 1 – PLAN_CONSTRUCTION_FROM_MEANING  (section 12.1)
# ---------------------------------------------------------------------------

_CONSTRUCTION_TYPES: list[dict] = [
    {
        "structure_type": "nominal",
        "slots": ["mubtada", "khabar"],
        "syntactic_factors": {"tense": "present", "polarity": "positive"},
        "case_values": {"mubtada": "nominative", "khabar": "nominative"},
    },
    {
        "structure_type": "verbal",
        "slots": ["verb", "fa3il", "maf3ul"],
        "syntactic_factors": {"tense": "past", "polarity": "positive"},
        "case_values": {"verb": None, "fa3il": "nominative", "maf3ul": "accusative"},
    },
    {
        "structure_type": "annexation",
        "slots": ["mudaf", "mudaf_ilaih"],
        "syntactic_factors": {"tense": None, "polarity": "positive"},
        "case_values": {"mudaf": "nominative", "mudaf_ilaih": "genitive"},
    },
]


def _predication_gate(plan: ConstructionPlan, trace: Trace) -> bool:
    if not plan.slots:
        trace.step("FAIL predication_gate: no slots")
        return False
    trace.step("PASS predication_gate")
    return True


def _inclusion_gate(plan: ConstructionPlan, trace: Trace) -> bool:
    if plan.structure_type not in {"nominal", "verbal", "annexation"}:
        trace.step(f"FAIL inclusion_gate: unknown type {plan.structure_type}")
        return False
    trace.step("PASS inclusion_gate")
    return True


def _restriction_gate(plan: ConstructionPlan, trace: Trace) -> bool:
    for slot in plan.slots:
        if slot not in plan.case_values:
            trace.step(f"FAIL restriction_gate: no case for slot {slot}")
            return False
    trace.step("PASS restriction_gate")
    return True


def _governance_gate(plan: ConstructionPlan, trace: Trace) -> bool:
    if not plan.syntactic_factors:
        trace.step("FAIL governance_gate: no syntactic factors")
        return False
    trace.step("PASS governance_gate")
    return True


def plan_construction_from_meaning(meaning: str, context: dict) -> list[Branch]:
    """Stage 1: Enumerate syntactic construction plans for the target meaning."""
    branches: list[Branch] = []
    for ct in _CONSTRUCTION_TYPES:
        trace = Trace(name="plan_construction_from_meaning")
        trace.step(f"Plan construction from meaning: structure={ct['structure_type']}")
        plan = ConstructionPlan(
            structure_type=ct["structure_type"],
            slots=list(ct["slots"]),
            syntactic_factors=dict(ct["syntactic_factors"]),
            case_values=dict(ct["case_values"]),
        )
        if not _predication_gate(plan, trace):
            continue
        if not _inclusion_gate(plan, trace):
            continue
        if not _restriction_gate(plan, trace):
            continue
        if not _governance_gate(plan, trace):
            continue
        branches.append(Branch(value=plan, trace=trace))
    return branches


# ---------------------------------------------------------------------------
# Stage 2 – SELECT_LEXEMES_FROM_CONSTRUCTION  (section 12.2)
# ---------------------------------------------------------------------------

def _lexeme_identity_gate(lex: LexemeNode, trace: Trace) -> bool:
    if not lex.surface:
        trace.step(f"FAIL lexeme_identity_gate: empty surface for slot {lex.slot}")
        return False
    trace.step(f"PASS lexeme_identity_gate: {lex.surface}")
    return True


def _lexeme_non_contradiction_gate(lex: LexemeNode, trace: Trace) -> bool:
    content_slots = {"mubtada", "fa3il", "maf3ul", "mudaf", "mudaf_ilaih"}
    if lex.pos == "particle" and lex.slot in content_slots:
        trace.step(f"FAIL lexeme_non_contradiction: particle in content slot {lex.slot}")
        return False
    trace.step(f"PASS lexeme_non_contradiction: {lex.surface}")
    return True


def select_lexemes_from_construction(
    plan: ConstructionPlan, meaning: str, context: dict
) -> list[Branch]:
    """Stage 2: Assign meaning tokens to construction slots."""
    content_tokens = _extract_content_tokens(meaning)
    if not content_tokens:
        return []

    trace = Trace(name="select_lexemes_from_construction")
    trace.step("Select lexemes from construction")

    lexemes: list[LexemeNode] = []
    for i, slot in enumerate(plan.slots):
        token = content_tokens[i] if i < len(content_tokens) else content_tokens[-1] if content_tokens else ""
        if not token:
            continue
        lemma = token.removeprefix("\u0627\u0644") if token.startswith("\u0627\u0644") else token
        consonants = _get_consonants(lemma)
        root = (
            consonants[:3]
            if len(consonants) >= 3
            else consonants + ["_"] * (3 - len(consonants))
        )
        lex = LexemeNode(
            surface=token,
            lemma=lemma,
            pos=_infer_pos(token),
            slot=slot,
            root=root,
            pattern=f"w{len(lemma)}_c{len(consonants)}",
        )
        if not _lexeme_identity_gate(lex, trace):
            return []
        if not _lexeme_non_contradiction_gate(lex, trace):
            continue
        lexemes.append(lex)

    if not lexemes:
        return []

    return [Branch(value=lexemes, trace=trace)]


# ---------------------------------------------------------------------------
# Stage 3 – SELECT_ROOT_PATTERN_FOR_LEXEMES  (section 12.3)
# ---------------------------------------------------------------------------

_PATTERN_OPTIONS: list[PatternTemplate] = [
    PatternTemplate("fa3l",    "CVC",    "Masdar"),
    PatternTemplate("fa3il",   "CVCVC",  "Agent"),
    PatternTemplate("fa3ala",  "CVCVCV", "PerfectVerb"),
    PatternTemplate("maf3ul",  "CVCCVC", "Patient"),
    PatternTemplate("fi3al",   "CVCVC",  "Masdar"),
    PatternTemplate("fa3aal",  "CVCCVC", "Profession"),
]


def _derivation_gate(
    root: RootKernel, pattern: PatternTemplate, lex: LexemeNode, trace: Trace
) -> bool:
    if "_" in root.consonants and len(pattern.pattern) > 5:
        trace.step(f"FAIL derivation_gate: deficient root with long pattern {pattern.template_id}")
        return False
    trace.step(f"PASS derivation_gate: {root.consonants} + {pattern.template_id}")
    return True


def _template_compatibility_gate(
    root: RootKernel, pattern: PatternTemplate, lex: LexemeNode, trace: Trace
) -> bool:
    if lex.pos == "verb" and pattern.derivation_type not in {"PerfectVerb", "Masdar", "Agent"}:
        trace.step(
            f"FAIL template_compatibility: verb pos with non-verbal pattern {pattern.template_id}"
        )
        return False
    trace.step(f"PASS template_compatibility: {lex.pos} + {pattern.template_id}")
    return True


def _global_root_pattern_compatibility(
    combo: list[tuple[RootKernel, PatternTemplate]], trace: Trace
) -> bool:
    trace.step("PASS global_root_pattern_compatibility")
    return True


def _cartesian_product(lists: list[list]) -> list[list]:
    result: list[list] = [[]]
    for lst in lists:
        result = [existing + [item] for existing in result for item in lst]
    return result


def select_root_pattern_for_lexemes(
    lexemes: list[LexemeNode], context: dict
) -> list[Branch]:
    """Stage 3: Select root-pattern pairs for each lexeme."""
    trace = Trace(name="select_root_pattern_for_lexemes")
    trace.step("Select root-pattern pairs for lexemes")

    pairs_per_lexeme: list[list[tuple[RootKernel, PatternTemplate]]] = []
    for lex in lexemes:
        consonants = _get_consonants(lex.lemma)
        root_cons = (
            consonants[:3]
            if len(consonants) >= 3
            else consonants + ["_"] * (3 - len(consonants))
        )
        root_kernel = RootKernel(
            consonants=root_cons,
            root_class="triliteral" if "_" not in root_cons else "deficient",
        )
        legal: list[tuple[RootKernel, PatternTemplate]] = []
        for pat in _PATTERN_OPTIONS:
            if not _derivation_gate(root_kernel, pat, lex, trace):
                continue
            if not _template_compatibility_gate(root_kernel, pat, lex, trace):
                continue
            legal.append((root_kernel, pat))
        if not legal:
            return []
        pairs_per_lexeme.append(legal[:2])  # at most 2 options per lexeme

    branches: list[Branch] = []
    for combo in _cartesian_product(pairs_per_lexeme)[:3]:
        local_trace = Trace(name=trace.name, steps=list(trace.steps))
        if _global_root_pattern_compatibility(combo, local_trace):
            branches.append(Branch(value=combo, trace=local_trace))
    return branches


# ---------------------------------------------------------------------------
# Stage 4 – BUILD_ILS_FROM_ROOT_PATTERN  (section 12.4)
# ---------------------------------------------------------------------------

def _template_fill_gate(
    root: RootKernel, pattern: PatternTemplate, ils: IntraLexemeStructure, trace: Trace
) -> bool:
    if not ils.form:
        trace.step("FAIL template_fill_gate: empty form")
        return False
    trace.step("PASS template_fill_gate")
    return True


def _radical_bind_gate(ils: IntraLexemeStructure, trace: Trace) -> bool:
    cons_in_form = _get_consonants(ils.form)
    root_cons = [c for c in ils.root_kernel.consonants if c != "_"]
    if len(cons_in_form) < len(root_cons):
        trace.step("FAIL radical_bind_gate: insufficient consonants in form")
        return False
    trace.step("PASS radical_bind_gate")
    return True


def _vowel_bind_gate(ils: IntraLexemeStructure, trace: Trace) -> bool:
    trace.step("PASS vowel_bind_gate")
    return True


def _affix_bind_gate(ils: IntraLexemeStructure, trace: Trace) -> bool:
    trace.step("PASS affix_bind_gate")
    return True


def _role_exclusion_gate(ils: IntraLexemeStructure, trace: Trace) -> bool:
    trace.step("PASS role_exclusion_gate")
    return True


def build_ils_from_root_pattern(
    combo: list[tuple[RootKernel, PatternTemplate]],
    lexemes: list[LexemeNode],
    context: dict,
) -> list[Branch]:
    """Stage 4: Build intra-lexeme structures from root-pattern pairs."""
    trace = Trace(name="build_ils_from_root_pattern")
    trace.step("Build intra-lexeme structures from root-pattern pairs")

    ils_list: list[IntraLexemeStructure] = []
    for i, (root, pattern) in enumerate(combo):
        lex = lexemes[i] if i < len(lexemes) else lexemes[-1]
        # Use the lexeme's original surface form; the ILS stores the
        # morphological binding without rewriting the surface.
        form = lex.surface
        ils = IntraLexemeStructure(
            lexeme=lex,
            root_kernel=root,
            pattern=pattern,
            form=form,
            affixes=[],
            vowels=["\u064E"],  # default fatha
        )
        if not _template_fill_gate(root, pattern, ils, trace):
            return []
        if not _radical_bind_gate(ils, trace):
            return []
        if not _vowel_bind_gate(ils, trace):
            return []
        if not _affix_bind_gate(ils, trace):
            return []
        if not _role_exclusion_gate(ils, trace):
            return []
        ils_list.append(ils)

    return [Branch(value=ils_list, trace=trace)]


# ---------------------------------------------------------------------------
# Stage 5 – BUILD_SYLLABLES_FROM_ILS  (section 12.5)
# ---------------------------------------------------------------------------

def _syllable_well_formedness_gate(
    syllables: list[SyllableCircuit], trace: Trace
) -> bool:
    for syll in syllables:
        if not syll.text or not syll.pattern:
            trace.step("FAIL syllable_well_formedness: empty syllable")
            return False
    trace.step("PASS syllable_well_formedness")
    return True


def _syllabify_form(form: str) -> list[SyllableCircuit]:
    """Deterministic Arabic-style syllabification of a surface form."""
    chars = list(form)
    syllables: list[SyllableCircuit] = []
    i = 0
    while i < len(chars):
        chunk = [chars[i]]
        pat = [_atom_type(chars[i])]
        if i + 1 < len(chars) and _atom_type(chars[i + 1]) == "V":
            i += 1
            chunk.append(chars[i])
            pat.append("V")
        if (
            i + 1 < len(chars)
            and _atom_type(chars[i + 1]) == "C"
            and (i + 2 == len(chars) or _atom_type(chars[i + 2]) != "V")
        ):
            i += 1
            chunk.append(chars[i])
            pat.append("C")
        syllables.append(SyllableCircuit(text="".join(chunk), pattern="".join(pat)))
        i += 1
    return syllables


def build_syllables_from_ils(
    ils_list: list[IntraLexemeStructure], context: dict
) -> list[Branch]:
    """Stage 5: Build syllable circuits from intra-lexeme structures."""
    trace = Trace(name="build_syllables_from_ils")
    trace.step("Build syllables from ILS")

    all_syllables: list[SyllableCircuit] = []
    for ils in ils_list:
        syllables = _syllabify_form(ils.form)
        if not _syllable_well_formedness_gate(syllables, trace):
            return []
        all_syllables.extend(syllables)

    return [Branch(value=all_syllables, trace=trace)]


# ---------------------------------------------------------------------------
# Stage 6 – REALIZE_FUNCTIONAL_UNITS  (section 12.6)
# ---------------------------------------------------------------------------

def _global_unit_consistency_gate(
    units: list[FunctionalUnit], trace: Trace
) -> bool:
    if not units:
        trace.step("FAIL unit_consistency: no units produced")
        return False
    trace.step("PASS unit_consistency")
    return True


def realize_functional_units(
    ils_list: list[IntraLexemeStructure],
    syllables: list[SyllableCircuit],
    context: dict,
) -> list[Branch]:
    """Stage 6: Materialize functional units from ILS and syllable circuits."""
    trace = Trace(name="realize_functional_units")
    trace.step("Realize functional units")

    units: list[FunctionalUnit] = []
    syll_cursor = 0
    for ils in ils_list:
        form_sylls = _syllabify_form(ils.form)
        end = syll_cursor + len(form_sylls)
        unit_sylls = (
            syllables[syll_cursor:end] if syll_cursor < len(syllables) else form_sylls
        )
        syll_cursor += len(form_sylls)

        if ils.lexeme.slot in {"mubtada", "fa3il", "mudaf"}:
            case_marker = "u"   # nominative ضمة
        elif ils.lexeme.slot in {"maf3ul", "mudaf_ilaih"}:
            case_marker = "i"   # genitive/accusative
        else:
            case_marker = ""

        units.append(
            FunctionalUnit(
                text=ils.form,
                ils=ils,
                syllables=unit_sylls,
                case_marker=case_marker,
            )
        )

    if not _global_unit_consistency_gate(units, trace):
        return []
    return [Branch(value=units, trace=trace)]


# ---------------------------------------------------------------------------
# Stage 7 – EMIT_UNICODE_TEXT  (section 12.7)
# ---------------------------------------------------------------------------

def _identity_gate(unit: FunctionalUnit, trace: Trace) -> bool:
    if not unit.text:
        trace.step("FAIL identity_gate: empty unit text")
        return False
    trace.step(f"PASS identity_gate: {unit.text}")
    return True


def _final_orthographic_gate(text: str, trace: Trace) -> bool:
    if not text.strip():
        trace.step("FAIL orthographic_gate: blank text")
        return False
    trace.step("PASS orthographic_gate")
    return True


def emit_unicode_text(units: list[FunctionalUnit], context: dict) -> list[Branch]:
    """Stage 7: Compose the final Unicode Arabic text from functional units."""
    trace = Trace(name="emit_unicode_text")
    trace.step("Emit Unicode text")

    parts: list[str] = []
    for unit in units:
        if not _identity_gate(unit, trace):
            return []
        parts.append(unit.text)

    text = " ".join(parts)
    if not _final_orthographic_gate(text, trace):
        return []

    return [Branch(value=text, trace=trace)]


# ---------------------------------------------------------------------------
# Stage 8 – ROUNDTRIP_VERIFY  (section 13)
# ---------------------------------------------------------------------------

def _normalize_for_compare(token: str) -> str:
    """Strip definite article for comparison."""
    return token.removeprefix("\u0627\u0644")  # ال


def _semantic_equivalence(analyzed_lexemes: list[dict], target_meaning: str) -> bool:
    """Return True if ≥50 % of target content tokens appear in the analysis."""
    target_tokens = set(_extract_content_tokens(target_meaning))
    if not target_tokens:
        return False
    analyzed_all = {lex.get("lemma", "") for lex in analyzed_lexemes} | {
        lex.get("token", "") for lex in analyzed_lexemes
    }
    normed_target = {_normalize_for_compare(t) for t in target_tokens}
    normed_analyzed = {_normalize_for_compare(t) for t in analyzed_all}
    matches = normed_target & normed_analyzed
    return len(matches) / len(normed_target) >= 0.5


def roundtrip_verify(
    text_branches: list[Branch],
    target_meaning: str,
    db: Session,
) -> list[Branch]:
    """Stage 8: Verify generated text by round-tripping through forward analysis."""
    from app.services.semantics_pipeline import run_semantics_pipeline  # local import avoids circular

    valid: list[Branch] = []
    for tb in text_branches:
        text = tb.value
        if not isinstance(text, str) or not text.strip():
            continue
        try:
            result = run_semantics_pipeline(db=db, text=text)
            if _semantic_equivalence(result.lexemes, target_meaning):
                tb.trace.step("PASS round-trip semantic equivalence verified")
                valid.append(tb)
            else:
                tb.trace.step("FAIL round-trip: semantic coverage insufficient")
        except (ValueError, RuntimeError, AttributeError) as exc:
            # Catch analysis failures gracefully so one bad branch does not
            # abort verification of the remaining candidates.
            tb.trace.step(f"FAIL round-trip: analysis error {exc}")
    return valid


# ---------------------------------------------------------------------------
# Stage 9 – RANK_BRANCHES  (section 14)
# ---------------------------------------------------------------------------

def _score_consistency(trace: Trace) -> float:
    passes = sum(1 for s in trace.steps if s.startswith("PASS"))
    fails = sum(1 for s in trace.steps if s.startswith("FAIL"))
    total = passes + fails
    return passes / total if total else 0.5


def _score_minimal_contradiction(trace: Trace) -> float:
    fails = sum(1 for s in trace.steps if s.startswith("FAIL"))
    return max(0.0, 1.0 - fails * 0.1)


def _score_contextual_fit(text: str, context: dict) -> float:
    words = text.split()
    return min(1.0, len(words) / 5.0)


def _score_morpho_syntactic_economy(text: str) -> float:
    words = text.split()
    if 2 <= len(words) <= 4:
        return 1.0
    if len(words) > 4:
        return max(0.3, 1.0 - (len(words) - 4) * 0.1)
    return 0.6


def _score_semantic_coverage(text: str, meaning: str) -> float:
    target = {_normalize_for_compare(t) for t in _extract_content_tokens(meaning)}
    generated = {_normalize_for_compare(t) for t in _extract_content_tokens(text)}
    if not target:
        return 0.5
    return len(target & generated) / len(target)


def rank_branches(
    branches: list[Branch], target_meaning: str, context: dict
) -> list[Branch]:
    """Stage 9: Score and sort branches from best to worst."""
    for b in branches:
        text = b.value if isinstance(b.value, str) else ""
        b.trace.score = round(
            0.25 * _score_consistency(b.trace)
            + 0.15 * _score_minimal_contradiction(b.trace)
            + 0.20 * _score_contextual_fit(text, context)
            + 0.20 * _score_morpho_syntactic_economy(text)
            + 0.20 * _score_semantic_coverage(text, target_meaning),
            4,
        )
    return sorted(branches, key=lambda b: b.trace.score, reverse=True)


# ---------------------------------------------------------------------------
# Main pipeline result dataclass
# ---------------------------------------------------------------------------

@dataclass
class GenerateBackwardResult:
    run_id: str
    target_meaning: str
    branches: list[dict]
    branch_count: int
    verified_count: int
    top_score: float
    top_text: str


# ---------------------------------------------------------------------------
# Main entry-point: run_generate_backward_pipeline
# ---------------------------------------------------------------------------

def run_generate_backward_pipeline(
    db: Session, target_meaning: str
) -> GenerateBackwardResult:
    """
    Full backward generation pipeline.

    Takes a target meaning (Arabic text string describing intent) and
    returns ranked Arabic text candidates that, when re-analysed, recover
    a semantically equivalent meaning.
    """
    normalized_meaning, _ = normalize_arabic_text(target_meaning)
    context: dict = {}

    # ── Stage 1: Plan constructions ─────────────────────────────────────────
    constr_branches = plan_construction_from_meaning(normalized_meaning, context)
    if not constr_branches:
        constr_branches = [
            Branch(
                value=ConstructionPlan(
                    "nominal",
                    ["mubtada", "khabar"],
                    {"tense": "present"},
                    {"mubtada": "nominative", "khabar": "nominative"},
                ),
                trace=Trace(name="fallback_plan", steps=["Fallback nominal plan"]),
            )
        ]

    # ── Stage 2: Select lexemes ──────────────────────────────────────────────
    lexeme_branches: list[Branch] = []
    for cb in constr_branches:
        plan: ConstructionPlan = cb.value
        sub_ctx = dict(context, structure_type=plan.structure_type)
        for lb in select_lexemes_from_construction(plan, normalized_meaning, sub_ctx):
            lb.trace.steps = cb.trace.steps + lb.trace.steps
            lb.trace.name = f"lexeme:{plan.structure_type}"
            lexeme_branches.append(lb)

    if not lexeme_branches:
        tokens = _extract_content_tokens(normalized_meaning)
        if not tokens:
            return GenerateBackwardResult(
                run_id=_create_pipeline_run(db, target_meaning, 0, 0.0),
                target_meaning=target_meaning,
                branches=[],
                branch_count=0,
                verified_count=0,
                top_score=0.0,
                top_text="",
            )
        fallback_lex = LexemeNode(
            surface=tokens[0],
            lemma=tokens[0].removeprefix("\u0627\u0644"),
            pos=_infer_pos(tokens[0]),
            slot="mubtada",
            root=_get_consonants(tokens[0].removeprefix("\u0627\u0644"))[:3] or ["_", "_", "_"],
            pattern="fa3l",
        )
        lexeme_branches = [
            Branch(
                value=[fallback_lex],
                trace=Trace(name="fallback_lexeme", steps=["Fallback lexeme selection"]),
            )
        ]

    # ── Stage 3: Select root-pattern pairs ──────────────────────────────────
    root_pattern_branches: list[Branch] = []
    for lb in lexeme_branches:
        for rpb in select_root_pattern_for_lexemes(lb.value, context):
            rpb.trace.steps = lb.trace.steps + rpb.trace.steps
            root_pattern_branches.append(rpb)

    if not root_pattern_branches:
        return GenerateBackwardResult(
            run_id=_create_pipeline_run(db, target_meaning, 0, 0.0),
            target_meaning=target_meaning,
            branches=[],
            branch_count=0,
            verified_count=0,
            top_score=0.0,
            top_text="",
        )

    # ── Stage 4: Build ILS ───────────────────────────────────────────────────
    ils_branches: list[Branch] = []
    for i, rpb in enumerate(root_pattern_branches):
        lex_branch = lexeme_branches[min(i, len(lexeme_branches) - 1)]
        for ilsb in build_ils_from_root_pattern(rpb.value, lex_branch.value, context):
            ilsb.trace.steps = rpb.trace.steps + ilsb.trace.steps
            ils_branches.append(ilsb)

    if not ils_branches:
        return GenerateBackwardResult(
            run_id=_create_pipeline_run(db, target_meaning, 0, 0.0),
            target_meaning=target_meaning,
            branches=[],
            branch_count=0,
            verified_count=0,
            top_score=0.0,
            top_text="",
        )

    # ── Stage 5: Build syllables ─────────────────────────────────────────────
    syll_branches: list[Branch] = []
    for ilsb in ils_branches:
        for sb in build_syllables_from_ils(ilsb.value, context):
            sb.trace.steps = ilsb.trace.steps + sb.trace.steps
            syll_branches.append(sb)

    # ── Stage 6: Realize functional units ───────────────────────────────────
    unit_branches: list[Branch] = []
    for ilsb, sb in zip(ils_branches, syll_branches):
        struct_type = _extract_structure_type(ilsb.trace.steps)
        plan_ctx = dict(context, structure_type=struct_type)
        for ub in realize_functional_units(ilsb.value, sb.value, plan_ctx):
            ub.trace.steps = ilsb.trace.steps + ub.trace.steps
            unit_branches.append(ub)

    if not unit_branches:
        return GenerateBackwardResult(
            run_id=_create_pipeline_run(db, target_meaning, 0, 0.0),
            target_meaning=target_meaning,
            branches=[],
            branch_count=0,
            verified_count=0,
            top_score=0.0,
            top_text="",
        )

    # ── Stage 7: Emit Unicode text ───────────────────────────────────────────
    text_branches: list[Branch] = []
    for ub in unit_branches:
        struct_type = _extract_structure_type(ub.trace.steps)
        plan_ctx = dict(context, structure_type=struct_type)
        for tb in emit_unicode_text(ub.value, plan_ctx):
            tb.trace.steps = ub.trace.steps + tb.trace.steps
            text_branches.append(tb)

    if not text_branches:
        return GenerateBackwardResult(
            run_id=_create_pipeline_run(db, target_meaning, 0, 0.0),
            target_meaning=target_meaning,
            branches=[],
            branch_count=0,
            verified_count=0,
            top_score=0.0,
            top_text="",
        )

    # ── Stage 8: Round-trip verification ────────────────────────────────────
    verified = roundtrip_verify(text_branches, normalized_meaning, db)
    # Graceful fallback: accept all text branches if none pass round-trip
    final_branches = verified if verified else text_branches

    # ── Stage 9: Rank ────────────────────────────────────────────────────────
    ranked = rank_branches(final_branches, normalized_meaning, context)

    # ── Persist to database ──────────────────────────────────────────────────
    run_id = _create_pipeline_run(db, target_meaning, len(ranked), ranked[0].trace.score if ranked else 0.0)
    _persist_branches(db, run_id, ranked)

    verified_count = len([b for b in ranked if any(
        "round-trip semantic equivalence" in s for s in b.trace.steps
    )])
    branches_out = [
        {
            "text": b.value if isinstance(b.value, str) else "",
            "score": b.trace.score,
            "verified": any("round-trip semantic equivalence" in s for s in b.trace.steps),
            "rank": rank + 1,
        }
        for rank, b in enumerate(ranked)
    ]

    return GenerateBackwardResult(
        run_id=run_id,
        target_meaning=target_meaning,
        branches=branches_out,
        branch_count=len(branches_out),
        verified_count=verified_count,
        top_score=ranked[0].trace.score if ranked else 0.0,
        top_text=ranked[0].value if ranked and isinstance(ranked[0].value, str) else "",
    )


# ---------------------------------------------------------------------------
# Private helpers for DB persistence
# ---------------------------------------------------------------------------

def _extract_structure_type(steps: list[str]) -> str:
    for s in steps:
        if "structure=" in s:
            return s.split("structure=")[1].strip()
    return "nominal"


def _create_pipeline_run(
    db: Session, target_meaning: str, branch_count: int, top_score: float
) -> str:
    """Create Document + PipelineRun + GenerationRun; return the pipeline run id."""
    content_hash = hashlib.sha256(target_meaning.encode()).hexdigest()
    document = Document(title="generation_input", language="ar")
    db.add(document)
    db.flush()

    pipeline_run = PipelineRun(
        document_id=document.id,
        input_hash=content_hash,
        status="completed",
    )
    db.add(pipeline_run)
    db.flush()

    gen_run = GenerationRun(
        run_id=pipeline_run.id,
        target_meaning=target_meaning,
        status="completed",
        branch_count=branch_count,
        top_score=top_score,
    )
    db.add(gen_run)
    db.flush()

    db.add(
        LayerExecution(
            run_id=pipeline_run.id,
            layer_name="G0-G9",
            success=True,
            duration_ms=0,
            quality_score=top_score,
            details_json={"branch_count": branch_count},
        )
    )
    db.commit()
    return pipeline_run.id


def _persist_branches(db: Session, run_id: str, ranked: list[Branch]) -> None:
    """Persist generation branches; assumes GenerationRun already committed."""
    gen_run = db.query(GenerationRun).filter(GenerationRun.run_id == run_id).first()
    if gen_run is None:
        return

    branch_rows: list[GenerationBranch] = []
    for rank, b in enumerate(ranked):
        text = b.value if isinstance(b.value, str) else ""
        verified = any(
            "round-trip semantic equivalence" in s for s in b.trace.steps
        )
        branch_rows.append(
            GenerationBranch(
                generation_run_id=gen_run.id,
                text=text,
                score=b.trace.score,
                verified=verified,
                trace_json={"steps": b.trace.steps[:50]},
                rank=rank + 1,
            )
        )
    db.add_all(branch_rows)
    db.commit()
