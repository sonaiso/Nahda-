"""Bidirectional Arabic Language Engine.

Implements the formal bidirectional analysis/generation system with:
  - 9-layer type system (L0 UnicodeAtom → L8 MeaningStructure)
  - Gate algebra derived from first logical principles
  - Forward function  A: L0* → MeaningStructure  (text  → meaning)
  - Backward function G: L8  → L0*               (meaning → text)

Gate principles:
  - IdentityGate      (mabda' al-huwiyya)
  - NonContradictionGate (mabda' adam al-tanaqud)
  - LicenseGate       (mabda' al-sababiyya)
  - TemplateFillGate  (mabda' al-tarkib)
  - WellFormednessGate
  - PredicationGate
  - MeaningConsistencyGate
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.services.semantics_pipeline import run_semantics_pipeline

# ── Arabic character constants ─────────────────────────────────────────────

_SHORT_VOWELS = {"\u064E", "\u064F", "\u0650"}  # fatha, damma, kasra
_LONG_VOWELS = {"\u0627", "\u0648", "\u064A"}   # alef, waw, yeh
_SUKUN = "\u0652"
_SHADDA = "\u0651"
_ARABIC_LETTER_START = 0x0621
_ARABIC_LETTER_END = 0x064A
_AL = "ال"
_MIN_RADICALS = 2

_ARABIC_PARTICLES = frozenset({"في", "من", "الى", "على", "عن", "و", "ف", "ب", "ك", "ل", "ثم", "او"})
_VERB_PREFIXES = ("ي", "ت", "ن", "ا")

# ─────────────────────────────────────────────────────────────────────────────
# Proof trace (records gate decisions)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ProofTrace:
    steps: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    score: float = 1.0


@dataclass
class Branch:
    value: object
    trace: ProofTrace


# ─────────────────────────────────────────────────────────────────────────────
# Layer 0 – UnicodeAtom
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class UnicodeAtom:
    id: int
    codepoint: int
    category: str
    combining_class: int


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 – FunctionalUnit
# ─────────────────────────────────────────────────────────────────────────────

_UNIT_TYPES = frozenset({"LETTER", "HARAKA", "SUKUN", "SHADDA", "MADD", "BOUNDARY"})
_ROLE_TYPES = frozenset({"RADICAL", "VOCALIC", "AFFIXAL", "INFLECTIONAL", "BOUNDARY_ROLE", "PROSODIC"})


@dataclass
class FunctionalUnit:
    id: int
    atoms: list[UnicodeAtom]
    unit_type: str
    role_set: list[str]
    position: int

    def char(self) -> str:
        return "".join(chr(a.codepoint) for a in self.atoms)


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 – IntraLexemeStructure
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class IntraLexemeStructure:
    id: int
    units: list[FunctionalUnit]
    consonantal_skeleton: list[FunctionalUnit]
    vocalic_skeleton: list[FunctionalUnit]
    augmentations: list[str]
    surface_form: str


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 – SyllableCircuit
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SyllableCircuit:
    id: int
    onset: list[FunctionalUnit]
    nucleus: list[FunctionalUnit]
    coda: list[FunctionalUnit]
    weight: str  # "light" | "heavy" | "superheavy"


# ─────────────────────────────────────────────────────────────────────────────
# Layer 4 – PatternTemplate
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class PatternTemplate:
    id: int
    radical_slots: list[str]
    vowel_slots: list[str]
    affix_slots: list[str]
    pattern_name: str


# ─────────────────────────────────────────────────────────────────────────────
# Layer 5 – RootKernel
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class RootKernel:
    id: int
    radicals: list[str]
    semantic_field: str
    concept_core: str


# ─────────────────────────────────────────────────────────────────────────────
# Layer 6 – LexemeNode
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class LexemeNode:
    id: int
    root: RootKernel | None
    pattern: PatternTemplate | None
    surface_form: str
    pos: str            # noun | verb | particle | adjective
    lexeme_type: str    # JAMID | MUSHTAQ
    morph_state: str    # MABNI | MURAB
    definiteness: str   # DEFINITE | INDEFINITE | CONTEXTUAL
    universality: str   # KULLI | JUZI | MIXED
    features: dict


# ─────────────────────────────────────────────────────────────────────────────
# Layer 7 – ConstructionNetwork
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ConstructionRelation:
    relation_type: str
    source_id: int
    target_id: int


@dataclass
class ConstructionNetwork:
    id: int
    lexemes: list[LexemeNode]
    predication_relations: list[ConstructionRelation]
    inclusion_relations: list[ConstructionRelation]
    restriction_relations: list[ConstructionRelation]
    case_values: dict[int, str]  # lexeme_id → case label


# ─────────────────────────────────────────────────────────────────────────────
# Layer 8 – MeaningStructure
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Entity:
    id: int
    label: str
    lexeme_ref: int
    entity_type: str    # person | place | thing | concept


@dataclass
class Quality:
    id: int
    label: str
    target_entity_id: int


@dataclass
class EventNode:
    id: int
    label: str
    agent_id: int | None
    patient_id: int | None


@dataclass
class MeaningRelation:
    relation_type: str
    source_id: int
    target_id: int


@dataclass
class MeaningStructure:
    id: int
    entities: list[Entity]
    qualities: list[Quality]
    events: list[EventNode]
    relations: list[MeaningRelation]
    universal_meanings: list[str]
    particulars: list[str]
    entailments: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Gate algebra
# ─────────────────────────────────────────────────────────────────────────────


def _identity_gate(obj: object, trace: ProofTrace, name: str = "IdentityGate") -> bool:
    """Principle of identity: every unit must exist and be non-null."""
    if obj is None:
        trace.contradictions.append(f"{name}: null object violates identity")
        trace.score *= 0.5
        return False
    trace.steps.append(f"{name}: ok")
    return True


def _non_contradiction_gate(roles: list[str], trace: ProofTrace) -> bool:
    """Principle of non-contradiction: no unit may carry contradictory roles."""
    conflicting = [("RADICAL", "VOCALIC")]
    for a, b in conflicting:
        if a in roles and b in roles:
            trace.contradictions.append(
                f"NonContradictionGate: roles {a} and {b} cannot coexist on the same unit"
            )
            trace.score *= 0.5
            return False
    trace.steps.append("NonContradictionGate: ok")
    return True


def _license_gate(unit: FunctionalUnit, trace: ProofTrace) -> bool:
    """Principle of causality: every letter must have a licensed role."""
    if unit.unit_type == "LETTER" and not unit.role_set:
        trace.contradictions.append(
            f"LicenseGate: LETTER at position {unit.position} has no role"
        )
        trace.score *= 0.7
        return False
    trace.steps.append("LicenseGate: ok")
    return True


def _template_fill_gate(root: RootKernel, pattern: PatternTemplate, trace: ProofTrace) -> bool:
    """Principle of composition: root radicals must satisfy the pattern's radical slots."""
    if len(root.radicals) < _MIN_RADICALS:
        trace.contradictions.append(
            f"TemplateFillGate: root has fewer than {_MIN_RADICALS} radicals — cannot fill pattern"
        )
        trace.score *= 0.5
        return False
    if len(root.radicals) < len(pattern.radical_slots):
        trace.contradictions.append(
            f"TemplateFillGate: root has {len(root.radicals)} radicals "
            f"but pattern requires {len(pattern.radical_slots)}"
        )
        trace.score *= 0.7
        return False
    trace.steps.append("TemplateFillGate: ok")
    return True


def _well_formedness_gate(ils: IntraLexemeStructure, trace: ProofTrace) -> bool:
    """A lexeme structure must contain at least one unit."""
    if not ils.units:
        trace.contradictions.append("WellFormednessGate: empty unit list")
        trace.score *= 0.5
        return False
    trace.steps.append("WellFormednessGate: ok")
    return True


def _predication_gate(cn: ConstructionNetwork, trace: ProofTrace) -> bool:
    """A multi-word construction should contain at least one predication link."""
    if len(cn.lexemes) > 2 and not cn.predication_relations:
        trace.contradictions.append(
            "PredicationGate: multi-lexeme construction lacks any predication relation"
        )
        trace.score *= 0.7
    trace.steps.append("PredicationGate: ok")
    return True


def _meaning_consistency_gate(m: MeaningStructure, trace: ProofTrace) -> bool:
    """A meaning structure must contain at least one entity or event."""
    if not m.entities and not m.events:
        trace.contradictions.append(
            "MeaningConsistencyGate: meaning structure has neither entities nor events"
        )
        trace.score *= 0.5
        return False
    trace.steps.append("MeaningConsistencyGate: ok")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _is_arabic_letter(ch: str) -> bool:
    code = ord(ch)
    return _ARABIC_LETTER_START <= code <= _ARABIC_LETTER_END


def _classify_unit_type(ch: str) -> str:
    if ch in _SHORT_VOWELS:
        return "HARAKA"
    if ch == _SUKUN:
        return "SUKUN"
    if ch == _SHADDA:
        return "SHADDA"
    if ch in _LONG_VOWELS and _is_arabic_letter(ch):
        return "MADD"
    if _is_arabic_letter(ch):
        return "LETTER"
    return "BOUNDARY"


def _initial_roles(unit_type: str) -> list[str]:
    if unit_type == "LETTER":
        return ["RADICAL"]
    if unit_type in {"HARAKA", "SUKUN", "SHADDA", "MADD"}:
        return ["VOCALIC"]
    return ["BOUNDARY_ROLE"]


def _syllable_weight(onset: list, nucleus: list, coda: list) -> str:
    if len(nucleus) > 0 and len(coda) > 1:
        return "superheavy"
    if len(nucleus) > 0 and len(coda) == 1:
        return "heavy"
    return "light"


def _normalize_arabic(text: str) -> str:
    alef_variants = {"\u0623", "\u0625", "\u0622", "\u0671"}
    result = []
    for ch in text:
        if ch in alef_variants:
            ch = "\u0627"
        elif ch == "\u0649":
            ch = "\u064A"
        elif ch == "\u06A9":
            ch = "\u0643"
        elif ch == "\u0640":
            continue
        ch = unicodedata.normalize("NFC", ch)
        result.append(ch)
    return "".join(result)


# ─────────────────────────────────────────────────────────────────────────────
# Layer builders
# ─────────────────────────────────────────────────────────────────────────────


def _build_unicode_atoms(text: str) -> list[UnicodeAtom]:
    normalized = _normalize_arabic(text)
    atoms = []
    for i, ch in enumerate(normalized):
        cp = ord(ch)
        atoms.append(
            UnicodeAtom(
                id=i,
                codepoint=cp,
                category=unicodedata.category(ch),
                combining_class=unicodedata.combining(ch),
            )
        )
    return atoms


def _build_functional_units(atoms: list[UnicodeAtom], trace: ProofTrace) -> list[FunctionalUnit]:
    units = []
    pos = 0
    for atom in atoms:
        ch = chr(atom.codepoint)
        if ch.isspace():
            unit = FunctionalUnit(
                id=atom.id,
                atoms=[atom],
                unit_type="BOUNDARY",
                role_set=["BOUNDARY_ROLE"],
                position=pos,
            )
        else:
            ut = _classify_unit_type(ch)
            roles = _initial_roles(ut)
            unit = FunctionalUnit(
                id=atom.id,
                atoms=[atom],
                unit_type=ut,
                role_set=roles,
                position=pos,
            )

        if not _identity_gate(unit, trace, "IdentityGate"):
            pos += 1
            continue
        if not _non_contradiction_gate(unit.role_set, trace):
            pos += 1
            continue
        _license_gate(unit, trace)
        units.append(unit)
        pos += 1
    return units


def _build_ils_for_token(token_units: list[FunctionalUnit], token_id: int, trace: ProofTrace) -> IntraLexemeStructure | None:
    consonants = [u for u in token_units if u.unit_type in {"LETTER", "MADD"}]
    vowels = [u for u in token_units if u.unit_type in {"HARAKA", "SUKUN", "SHADDA"}]
    surface = "".join(u.char() for u in token_units)

    augmentations: list[str] = []
    work = surface
    if work.startswith(_AL):
        work = work[2:]
        augmentations.append("prefix:ال")

    ils = IntraLexemeStructure(
        id=token_id,
        units=token_units,
        consonantal_skeleton=consonants,
        vocalic_skeleton=vowels,
        augmentations=augmentations,
        surface_form=surface,
    )
    if not _well_formedness_gate(ils, trace):
        return None
    return ils


def _build_syllable_circuits(ils: IntraLexemeStructure, trace: ProofTrace) -> list[SyllableCircuit]:
    units = ils.units
    syllables: list[SyllableCircuit] = []
    i = 0
    syll_id = 0
    while i < len(units):
        u = units[i]
        if u.unit_type == "BOUNDARY":
            i += 1
            continue
        onset = []
        nucleus = []
        coda = []

        if u.unit_type in {"LETTER", "MADD"}:
            onset.append(u)
            i += 1

        while i < len(units) and units[i].unit_type in {"HARAKA", "SUKUN", "SHADDA", "MADD"}:
            nucleus.append(units[i])
            i += 1

        if i < len(units) and units[i].unit_type in {"LETTER"} and (
            i + 1 >= len(units) or units[i + 1].unit_type not in {"HARAKA"}
        ):
            coda.append(units[i])
            i += 1

        if onset or nucleus:
            syllables.append(
                SyllableCircuit(
                    id=syll_id,
                    onset=onset,
                    nucleus=nucleus,
                    coda=coda,
                    weight=_syllable_weight(onset, nucleus, coda),
                )
            )
            syll_id += 1
        else:
            i += 1

    trace.steps.append(f"SyllableBuilder: produced {len(syllables)} syllables for '{ils.surface_form}'")
    return syllables


def _infer_root_and_pattern(ils: IntraLexemeStructure, ils_id: int, trace: ProofTrace) -> tuple[RootKernel, PatternTemplate]:
    consonants = [u.char() for u in ils.consonantal_skeleton if u.unit_type == "LETTER"]

    if len(consonants) >= 3:
        radicals = consonants[:3]
    elif len(consonants) == 2:
        radicals = consonants + ["_"]
    else:
        radicals = (consonants + ["_", "_", "_"])[:3]

    work = ils.surface_form
    if work.startswith(_AL):
        work = work[2:]

    pattern_name = f"w{len(work)}_c{len(consonants)}"
    radical_slots = ["C1", "C2", "C3"][: len(radicals)]

    root = RootKernel(
        id=ils_id,
        radicals=radicals,
        semantic_field="general",
        concept_core="-".join(r for r in radicals if r != "_"),
    )
    pattern = PatternTemplate(
        id=ils_id,
        radical_slots=radical_slots,
        vowel_slots=["V1"],
        affix_slots=list(ils.augmentations),
        pattern_name=pattern_name,
    )
    _template_fill_gate(root, pattern, trace)
    return root, pattern


def _build_lexeme(ils: IntraLexemeStructure, root: RootKernel, pattern: PatternTemplate, lex_id: int, trace: ProofTrace) -> LexemeNode:
    surface = ils.surface_form
    pos = "particle"

    if surface in _ARABIC_PARTICLES:
        pos = "particle"
    elif surface.startswith(_AL):
        pos = "noun"
    elif len(surface) >= 3 and surface[0] in _VERB_PREFIXES:
        pos = "verb"
    else:
        pos = "noun"

    lexeme_type = "JAMID" if pos == "particle" else "MUSHTAQ"
    morph_state = "MABNI" if pos == "particle" else "MURAB"
    definiteness = "DEFINITE" if surface.startswith(_AL) else "INDEFINITE"

    lex = LexemeNode(
        id=lex_id,
        root=root,
        pattern=pattern,
        surface_form=surface,
        pos=pos,
        lexeme_type=lexeme_type,
        morph_state=morph_state,
        definiteness=definiteness,
        universality="KULLI" if pos in {"noun", "verb"} else "MIXED",
        features={"augmentations": ils.augmentations},
    )
    trace.steps.append(f"LexemeNode: built '{surface}' pos={pos}")
    return lex


def _build_construction_network(lexemes: list[LexemeNode], cn_id: int, trace: ProofTrace) -> ConstructionNetwork:
    pred_rels: list[ConstructionRelation] = []
    incl_rels: list[ConstructionRelation] = []
    restr_rels: list[ConstructionRelation] = []
    case_values: dict[int, str] = {}

    nouns = [lx for lx in lexemes if lx.pos == "noun"]
    verbs = [lx for lx in lexemes if lx.pos == "verb"]
    particles = [lx for lx in lexemes if lx.pos == "particle"]

    # Simple predication: verb → noun (subject)
    if verbs and nouns:
        pred_rels.append(ConstructionRelation("predication", verbs[0].id, nouns[0].id))
        case_values[nouns[0].id] = "nominative"

    # Restriction: particle → subsequent noun
    for part in particles:
        for n in nouns[1:]:
            restr_rels.append(ConstructionRelation("restriction", part.id, n.id))
            case_values[n.id] = "genitive"
            break

    # Inclusion: definite nouns
    for n in nouns:
        if n.definiteness == "DEFINITE":
            incl_rels.append(ConstructionRelation("inclusion", n.id, n.id))

    cn = ConstructionNetwork(
        id=cn_id,
        lexemes=lexemes,
        predication_relations=pred_rels,
        inclusion_relations=incl_rels,
        restriction_relations=restr_rels,
        case_values=case_values,
    )
    _predication_gate(cn, trace)
    return cn


def _interpret_meaning(cn: ConstructionNetwork, ms_id: int, trace: ProofTrace) -> MeaningStructure | None:
    entities: list[Entity] = []
    events: list[EventNode] = []
    qualities: list[Quality] = []
    relations: list[MeaningRelation] = []

    for lex in cn.lexemes:
        if lex.pos == "noun":
            entities.append(
                Entity(
                    id=lex.id,
                    label=lex.surface_form,
                    lexeme_ref=lex.id,
                    entity_type="thing",
                )
            )
        elif lex.pos == "verb":
            agent_id = None
            patient_id = None
            for rel in cn.predication_relations:
                if rel.source_id == lex.id:
                    agent_id = rel.target_id
                    break
            events.append(
                EventNode(
                    id=lex.id,
                    label=lex.surface_form,
                    agent_id=agent_id,
                    patient_id=patient_id,
                )
            )

    for rel in cn.predication_relations:
        relations.append(MeaningRelation("predication", rel.source_id, rel.target_id))
    for rel in cn.restriction_relations:
        relations.append(MeaningRelation("restriction", rel.source_id, rel.target_id))

    noun_labels = [e.label for e in entities]
    ms = MeaningStructure(
        id=ms_id,
        entities=entities,
        qualities=qualities,
        events=events,
        relations=relations,
        universal_meanings=[f"concept:{lbl}" for lbl in noun_labels[:2]],
        particulars=[e.label for e in entities],
        entailments=["entails:existence"] if entities else [],
    )
    if not _meaning_consistency_gate(ms, trace):
        return None
    return ms


# ─────────────────────────────────────────────────────────────────────────────
# Forward result dataclass
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class AnalyzeForwardResult:
    run_id: str
    normalized_text: str
    # Layer outputs (as serializable dicts)
    unicode_atoms: list[dict]
    functional_units: list[dict]
    intra_lexeme_structures: list[dict]
    syllable_circuits: list[dict]
    root_patterns: list[dict]
    lexemes: list[dict]
    construction_network: dict
    meaning_structure: dict
    # Gate trace
    trace: dict
    valid: bool


@dataclass
class GenerateBackwardResult:
    generated_text: str
    candidate_forms: list[str]
    trace: dict
    valid: bool


# ─────────────────────────────────────────────────────────────────────────────
# Forward function  A: text → meaning
# ─────────────────────────────────────────────────────────────────────────────


def run_analyze_forward(db: Session, text: str) -> AnalyzeForwardResult:
    """Forward analysis: text (L0) → MeaningStructure (L8).

    Also persists data through the existing semantics pipeline for DB consistency.
    """
    semantics_result = run_semantics_pipeline(db=db, text=text)

    trace = ProofTrace()
    normalized = _normalize_arabic(text)

    # L0 – Unicode atoms
    atoms = _build_unicode_atoms(normalized)

    # L1 – Functional units
    func_units = _build_functional_units(atoms, trace)

    # Segment into tokens (split on BOUNDARY units)
    token_groups: list[list[FunctionalUnit]] = []
    current: list[FunctionalUnit] = []
    for u in func_units:
        if u.unit_type == "BOUNDARY":
            if current:
                token_groups.append(current)
                current = []
        else:
            current.append(u)
    if current:
        token_groups.append(current)

    # L2 – IntraLexemeStructures
    ils_list: list[IntraLexemeStructure] = []
    for i, tg in enumerate(token_groups):
        ils = _build_ils_for_token(tg, i, trace)
        if ils:
            ils_list.append(ils)

    # L3 – SyllableCircuits
    all_syllables: list[SyllableCircuit] = []
    for ils in ils_list:
        all_syllables.extend(_build_syllable_circuits(ils, trace))

    # L4/L5 – PatternTemplates + RootKernels
    root_pattern_pairs: list[tuple[RootKernel, PatternTemplate]] = []
    for i, ils in enumerate(ils_list):
        rp = _infer_root_and_pattern(ils, i, trace)
        root_pattern_pairs.append(rp)

    # L6 – LexemeNodes
    lexeme_nodes: list[LexemeNode] = []
    for i, (ils, (root, pattern)) in enumerate(zip(ils_list, root_pattern_pairs)):
        lex = _build_lexeme(ils, root, pattern, i, trace)
        lexeme_nodes.append(lex)

    # L7 – ConstructionNetwork
    cn = _build_construction_network(lexeme_nodes, 0, trace)

    # L8 – MeaningStructure
    ms = _interpret_meaning(cn, 0, trace)
    valid = ms is not None

    # Serialize outputs
    def _atom_dict(a: UnicodeAtom) -> dict:
        return {"id": a.id, "codepoint": a.codepoint, "category": a.category, "combining_class": a.combining_class}

    def _unit_dict(u: FunctionalUnit) -> dict:
        return {"id": u.id, "char": u.char(), "unit_type": u.unit_type, "role_set": u.role_set, "position": u.position}

    def _ils_dict(ils: IntraLexemeStructure) -> dict:
        return {
            "id": ils.id,
            "surface_form": ils.surface_form,
            "consonantal_skeleton": [u.char() for u in ils.consonantal_skeleton],
            "vocalic_skeleton": [u.char() for u in ils.vocalic_skeleton],
            "augmentations": ils.augmentations,
        }

    def _syll_dict(s: SyllableCircuit) -> dict:
        return {
            "id": s.id,
            "onset": [u.char() for u in s.onset],
            "nucleus": [u.char() for u in s.nucleus],
            "coda": [u.char() for u in s.coda],
            "weight": s.weight,
        }

    def _rp_dict(r: RootKernel, p: PatternTemplate) -> dict:
        return {
            "root": {"id": r.id, "radicals": r.radicals, "semantic_field": r.semantic_field, "concept_core": r.concept_core},
            "pattern": {"id": p.id, "pattern_name": p.pattern_name, "radical_slots": p.radical_slots, "vowel_slots": p.vowel_slots, "affix_slots": p.affix_slots},
        }

    def _lex_dict(lex: LexemeNode) -> dict:
        return {
            "id": lex.id,
            "surface_form": lex.surface_form,
            "pos": lex.pos,
            "lexeme_type": lex.lexeme_type,
            "morph_state": lex.morph_state,
            "definiteness": lex.definiteness,
            "universality": lex.universality,
            "root_radicals": lex.root.radicals if lex.root else [],
        }

    def _cn_dict(cn: ConstructionNetwork) -> dict:
        return {
            "id": cn.id,
            "lexeme_count": len(cn.lexemes),
            "predication_relations": [
                {"type": r.relation_type, "source": r.source_id, "target": r.target_id}
                for r in cn.predication_relations
            ],
            "inclusion_relations": [
                {"type": r.relation_type, "source": r.source_id, "target": r.target_id}
                for r in cn.inclusion_relations
            ],
            "restriction_relations": [
                {"type": r.relation_type, "source": r.source_id, "target": r.target_id}
                for r in cn.restriction_relations
            ],
            "case_values": {str(k): v for k, v in cn.case_values.items()},
        }

    def _ms_dict(ms: MeaningStructure | None) -> dict:
        if ms is None:
            return {}
        return {
            "id": ms.id,
            "entities": [{"id": e.id, "label": e.label, "entity_type": e.entity_type} for e in ms.entities],
            "events": [{"id": ev.id, "label": ev.label, "agent_id": ev.agent_id, "patient_id": ev.patient_id} for ev in ms.events],
            "qualities": [{"id": q.id, "label": q.label, "target_entity_id": q.target_entity_id} for q in ms.qualities],
            "relations": [{"type": r.relation_type, "source": r.source_id, "target": r.target_id} for r in ms.relations],
            "universal_meanings": ms.universal_meanings,
            "particulars": ms.particulars,
            "entailments": ms.entailments,
        }

    return AnalyzeForwardResult(
        run_id=semantics_result.run_id,
        normalized_text=normalized,
        unicode_atoms=[_atom_dict(a) for a in atoms],
        functional_units=[_unit_dict(u) for u in func_units],
        intra_lexeme_structures=[_ils_dict(ils) for ils in ils_list],
        syllable_circuits=[_syll_dict(s) for s in all_syllables],
        root_patterns=[_rp_dict(r, p) for r, p in root_pattern_pairs],
        lexemes=[_lex_dict(lx) for lx in lexeme_nodes],
        construction_network=_cn_dict(cn),
        meaning_structure=_ms_dict(ms),
        trace={
            "steps": trace.steps,
            "contradictions": trace.contradictions,
            "score": round(trace.score, 4),
        },
        valid=valid,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Backward function  G: meaning → text
# ─────────────────────────────────────────────────────────────────────────────

# Simple Arabic particles used in generation
_LOCATIVE_PARTICLE = "في"
_COORDINATION_PARTICLE = "و"


def run_generate_backward(meaning_input: dict) -> GenerateBackwardResult:
    """Backward generation: MeaningStructure (L8) → Arabic text (L0).

    Implements the inverse function G: L8 → P(Branch(L0*)).
    Returns the best candidate form plus alternatives.

    The generation follows the gate chain in reverse:
    MeaningStructure → ConstructionNetwork → LexemeNodes → Surface form
    """
    trace = ProofTrace()

    entities: list[dict] = meaning_input.get("entities", [])
    events: list[dict] = meaning_input.get("events", [])
    qualities: list[dict] = meaning_input.get("qualities", [])
    relations: list[dict] = meaning_input.get("relations", [])

    if not entities and not events:
        trace.contradictions.append("GenerateBackward: no entities or events in meaning input")
        return GenerateBackwardResult(
            generated_text="",
            candidate_forms=[],
            trace={"steps": trace.steps, "contradictions": trace.contradictions, "score": 0.0},
            valid=False,
        )

    trace.steps.append("GenerateBackward: meaning input validated")

    # Build entity map for lookup
    entity_map: dict[int, str] = {e["id"]: e["label"] for e in entities}

    # Identify restriction relations (particle + noun)
    restriction_targets: set[int] = set()
    for r in relations:
        if r.get("type") == "restriction":
            restriction_targets.add(r["target"])

    # ── Candidate 1: Verb-initial (VSO) if events present ──────────────────
    candidates: list[str] = []

    if events:
        for ev in events:
            verb_label = ev.get("label", "")
            agent_id = ev.get("agent_id")
            patient_id = ev.get("patient_id")
            parts = [verb_label]
            if agent_id is not None:
                parts.append(entity_map.get(agent_id, ""))
            if patient_id is not None:
                parts.append(entity_map.get(patient_id, ""))

            # Append remaining entities that are restriction targets
            for e in entities:
                if e["id"] in restriction_targets:
                    parts.append(_LOCATIVE_PARTICLE)
                    parts.append(e["label"])
                    break

            candidate = " ".join(p for p in parts if p)
            if candidate:
                candidates.append(candidate)

    # ── Candidate 2: Nominal sentence (subject + predicate) ────────────────
    noun_labels = [e["label"] for e in entities if e["id"] not in restriction_targets]
    restrict_labels = [e["label"] for e in entities if e["id"] in restriction_targets]

    if len(noun_labels) >= 1:
        nominal = noun_labels[0]
        if len(noun_labels) >= 2:
            nominal = f"{noun_labels[0]} {noun_labels[1]}"
        elif restrict_labels:
            nominal = f"{noun_labels[0]} {_LOCATIVE_PARTICLE} {restrict_labels[0]}"

        if qualities:
            q_labels = [q["label"] for q in qualities]
            nominal = f"{nominal} {' '.join(q_labels)}"

        if nominal not in candidates:
            candidates.append(nominal)

    # ── Candidate 3: Coordinated entity list ───────────────────────────────
    if len(noun_labels) > 2:
        coordinated = f" {_COORDINATION_PARTICLE}".join(noun_labels)
        candidates.append(coordinated)

    # ── Gate check on best candidate ──────────────────────────────────────
    best = candidates[0] if candidates else ""
    trace.steps.append(f"GenerateBackward: {len(candidates)} candidate(s) produced")

    if best:
        trace.steps.append(f"GenerateBackward: best candidate = '{best}'")
        # Verify the generated text re-parses to a non-empty structure
        atoms = _build_unicode_atoms(best)
        if atoms:
            trace.steps.append("GenerateBackward: surface form passes Unicode atom check")

    return GenerateBackwardResult(
        generated_text=best,
        candidate_forms=candidates,
        trace={
            "steps": trace.steps,
            "contradictions": trace.contradictions,
            "score": round(trace.score, 4),
        },
        valid=bool(best),
    )
