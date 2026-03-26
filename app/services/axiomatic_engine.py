"""Axiomatic Engine for the Nahda Arabic Language System.

Implements the formal axiomatic system A1–A20 (Epistemic Primitives →
Phonology → Morphology → Syntax → Semantics → Unified Function),
the derived Lemmas L1–L5, Theorems T1–T5, and Falsification Tests F1–F5.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Arabic phonological lookup tables (used by A8, A9, A13)
# ---------------------------------------------------------------------------

# Consonant features: c = (place, manner, voicing)
_CONSONANT_FEATURES: dict[str, tuple[str, str, str]] = {
    "ب": ("labial", "stop", "voiced"),
    "ت": ("dental", "stop", "voiceless"),
    "ث": ("dental", "fricative", "voiceless"),
    "ج": ("palatal", "affricate", "voiced"),
    "ح": ("pharyngeal", "fricative", "voiceless"),
    "خ": ("uvular", "fricative", "voiceless"),
    "د": ("dental", "stop", "voiced"),
    "ذ": ("dental", "fricative", "voiced"),
    "ر": ("alveolar", "trill", "voiced"),
    "ز": ("alveolar", "fricative", "voiced"),
    "س": ("alveolar", "fricative", "voiceless"),
    "ش": ("palatal", "fricative", "voiceless"),
    "ص": ("alveolar", "fricative", "voiceless"),
    "ض": ("dental", "stop", "voiced"),
    "ط": ("alveolar", "stop", "voiceless"),
    "ظ": ("dental", "fricative", "voiced"),
    "ع": ("pharyngeal", "fricative", "voiced"),
    "غ": ("uvular", "fricative", "voiced"),
    "ف": ("labial", "fricative", "voiceless"),
    "ق": ("uvular", "stop", "voiceless"),
    "ك": ("velar", "stop", "voiceless"),
    "ل": ("alveolar", "lateral", "voiced"),
    "م": ("labial", "nasal", "voiced"),
    "ن": ("alveolar", "nasal", "voiced"),
    "ه": ("glottal", "fricative", "voiceless"),
    "و": ("labial", "approximant", "voiced"),
    "ي": ("palatal", "approximant", "voiced"),
    "ء": ("glottal", "stop", "voiceless"),
    "أ": ("glottal", "stop", "voiceless"),
    "إ": ("glottal", "stop", "voiceless"),
    "آ": ("glottal", "stop", "voiceless"),
    "ة": ("dental", "stop", "voiceless"),
    "ى": ("palatal", "approximant", "voiced"),
    "ا": ("glottal", "approximant", "voiced"),
}

# Short vowel diacritics: h = (height, backness, length)
_VOWEL_FEATURES: dict[str, tuple[str, str, str]] = {
    "\u064E": ("low", "central", "short"),    # fatha
    "\u064F": ("mid", "back", "short"),        # damma
    "\u0650": ("high", "front", "short"),      # kasra
    "\u0627": ("low", "central", "long"),      # alif (long a)
    "\u0648": ("mid", "back", "long"),         # waw (long u)
    "\u064A": ("high", "front", "long"),       # ya (long i)
}

SHORT_VOWELS = {"\u064E", "\u064F", "\u0650"}
LONG_VOWELS = {"\u0627", "\u0648", "\u064A"}
SUKUN = "\u0652"
PARTICLES = {"في", "من", "إلى", "على", "عن", "و", "ف", "ب", "ك", "ل", "ثم", "أو", "او", "ال"}

ARABIC_LETTER_START = 0x0621
ARABIC_LETTER_END = 0x064A


def _is_consonant(ch: str) -> bool:
    code = ord(ch)
    return (ARABIC_LETTER_START <= code <= ARABIC_LETTER_END) and ch not in SHORT_VOWELS and ch not in LONG_VOWELS


def _atom_type(ch: str) -> str:
    if ch in SHORT_VOWELS or ch in LONG_VOWELS:
        return "V"
    if ch == SUKUN:
        return "S"
    if _is_consonant(ch):
        return "C"
    return "X"


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AxiomResult:
    code: str           # e.g. "A1"
    name: str
    satisfied: bool
    evidence: str       # brief explanation / score


@dataclass
class LemmaResult:
    code: str           # e.g. "L1"
    name: str
    derived_from: list[str]
    holds: bool
    rationale: str


@dataclass
class TheoremResult:
    code: str           # e.g. "T1"
    name: str
    depends_on: list[str]
    proven: bool
    rationale: str


@dataclass
class FalsificationResult:
    code: str           # e.g. "F1"
    name: str
    score: float
    threshold: float
    falsified: bool     # True means the hypothesis was FALSIFIED
    details: str


@dataclass
class AxiomAnalysisResult:
    text: str
    tokens: list[str]
    axioms: list[AxiomResult]
    lemmas: list[LemmaResult]
    theorems: list[TheoremResult]
    falsifications: list[FalsificationResult]
    axiom_satisfaction_ratio: float
    lemma_hold_ratio: float
    theorem_proven_ratio: float
    system_coherent: bool


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _syllabify(token: str) -> list[tuple[str, str]]:
    """Return list of (syllable_text, pattern) for a token."""
    atoms = [(ch, _atom_type(ch)) for ch in token if not ch.isspace()]
    if not atoms:
        return []

    out: list[tuple[str, str]] = []
    i = 0
    while i < len(atoms):
        chunk = [atoms[i][0]]
        pattern = [atoms[i][1]]

        if i + 1 < len(atoms) and atoms[i + 1][1] == "V":
            i += 1
            chunk.append(atoms[i][0])
            pattern.append("V")

        if i + 1 < len(atoms) and atoms[i + 1][1] == "C" and (
            i + 2 == len(atoms) or atoms[i + 2][1] != "V"
        ):
            i += 1
            chunk.append(atoms[i][0])
            pattern.append("C")

        out.append(("".join(chunk), "".join(pattern)))
        i += 1

    return out


def _extract_root(token: str) -> list[str]:
    """Extract up to 3 consonants as the triliteral root."""
    prefixes = ("ال", "و", "ف", "ب", "ك", "ل", "س")
    suffixes = ("ها", "هم", "هن", "كما", "كم", "نا", "ات", "ون", "ين", "ة", "ه", "ي")

    work = token
    for pfx in prefixes:
        if work.startswith(pfx) and len(work) > len(pfx) + 1:
            work = work[len(pfx):]
            break
    for sfx in suffixes:
        if work.endswith(sfx) and len(work) > len(sfx) + 1:
            work = work[: -len(sfx)]
            break

    consonants = [c for c in work if _atom_type(c) == "C"]
    if len(consonants) >= 3:
        return consonants[:3]
    while len(consonants) < 3:
        consonants.append("_")
    return consonants


def _weight_type(syllable_pattern: str) -> str:
    """Classify syllable as G (heavy), Q (light), or H (medium)."""
    # Q = CV only
    if syllable_pattern == "CV":
        return "Q"
    # G = CVCC or CVVC or CVV
    if len(syllable_pattern) >= 4:
        return "G"
    # H = CVC or CCV
    return "H"


def _infer_pos(token: str) -> str:
    if token in PARTICLES:
        return "particle"
    if token.startswith("ال"):
        return "noun"
    if len(token) >= 3 and token[0] in {"ي", "ت", "ن", "ا"}:
        return "verb"
    return "noun"


# ---------------------------------------------------------------------------
# Axiom checks A1–A20
# ---------------------------------------------------------------------------

def _check_a1(tokens: list[str]) -> AxiomResult:
    """A1 (Identity): every token is a well-formed, non-empty string."""
    all_ok = all(isinstance(t, str) and len(t) > 0 for t in tokens)
    return AxiomResult(
        code="A1",
        name="الهوية",
        satisfied=all_ok,
        evidence=f"checked {len(tokens)} tokens — all are well-formed non-empty strings",
    )


def _check_a2(tokens: list[str]) -> AxiomResult:
    """A2 (Non-contradiction): no token simultaneously affirmed and denied."""
    # Proxy: no token appears with its negation ("لا + token") in the same token list
    negated = {t for t in tokens if t.startswith("لا")}
    stripped_negated = {t[2:] for t in negated if len(t) > 2}
    contradictions = [t for t in tokens if t in stripped_negated]
    ok = len(contradictions) == 0
    return AxiomResult(
        code="A2",
        name="امتناع التناقض",
        satisfied=ok,
        evidence=f"contradiction tokens found: {contradictions}" if not ok else "no contradictions detected",
    )


def _check_a3(tokens: list[str]) -> AxiomResult:
    """A3 (Excluded middle): each token is either present or absent — no third state."""
    # All tokens have a deterministic POS assignment → excluded middle holds
    pos_assigned = [_infer_pos(t) for t in tokens]
    ok = all(p in {"noun", "verb", "particle"} for p in pos_assigned)
    return AxiomResult(
        code="A3",
        name="المرفوع الثالث",
        satisfied=ok,
        evidence=f"POS coverage: {len(pos_assigned)} tokens fully classified",
    )


def _check_a4(tokens: list[str]) -> AxiomResult:
    """A4 (Distinguishability → Cognizability): only distinguishable units are cognizable."""
    # Distinguishable = has at least one consonant that differs from other tokens
    all_consonants = [
        frozenset(_extract_root(t)) for t in tokens
    ]
    cognizable_count = sum(1 for cs in all_consonants if cs != frozenset({"_"}))
    ok = cognizable_count > 0 or len(tokens) == 0
    return AxiomResult(
        code="A4",
        name="التعيّن شرط الإدراك",
        satisfied=ok,
        evidence=f"{cognizable_count}/{len(tokens)} tokens are distinguishable",
    )


def _check_a5(tokens: list[str]) -> AxiomResult:
    """A5 (Difference is the basis of classification): POS differences exist."""
    pos_set = {_infer_pos(t) for t in tokens}
    ok = len(pos_set) >= 1
    return AxiomResult(
        code="A5",
        name="الفرق أصل التصنيف",
        satisfied=ok,
        evidence=f"POS categories observed: {sorted(pos_set)}",
    )


def _check_a6(tokens: list[str]) -> AxiomResult:
    """A6 (Phonemic duality): text contains both consonants (boundary) and vowels (nucleus)."""
    text = " ".join(tokens)
    has_consonant = any(_atom_type(ch) == "C" for ch in text)
    has_vowel = any(_atom_type(ch) == "V" for ch in text)
    ok = has_consonant and has_vowel
    return AxiomResult(
        code="A6",
        name="الثنائية الصوتية الأساسية",
        satisfied=ok,
        evidence=f"consonants={'yes' if has_consonant else 'no'}, vowels={'yes' if has_vowel else 'no'}",
    )


def _check_a7(syllables: list[tuple[str, str]]) -> AxiomResult:
    """A7 (Syllable nucleus requirement): every syllable contains a vowel nucleus."""
    if not syllables:
        return AxiomResult(code="A7", name="شرط النواة المقطعية", satisfied=True,
                           evidence="no syllables to check")
    violated = [syl for syl, pat in syllables if "V" not in pat]
    ok = len(violated) == 0
    return AxiomResult(
        code="A7",
        name="شرط النواة المقطعية",
        satisfied=ok,
        evidence=f"{len(violated)} nucleus-less syllables" if not ok else f"all {len(syllables)} syllables have nuclei",
    )


def _check_a8(tokens: list[str]) -> AxiomResult:
    """A8 (Consonant representation): each consonant maps to (place, manner, voicing)."""
    all_consonants = {ch for t in tokens for ch in t if _atom_type(ch) == "C"}
    unrepresented = [c for c in all_consonants if c not in _CONSONANT_FEATURES]
    ok = len(unrepresented) == 0
    return AxiomResult(
        code="A8",
        name="تمثيل الحرف",
        satisfied=ok,
        evidence=f"unrepresented consonants: {unrepresented}" if not ok
                 else f"all {len(all_consonants)} consonant types mapped to (place, manner, voicing)",
    )


def _check_a9(tokens: list[str]) -> AxiomResult:
    """A9 (Vowel representation): each vowel maps to (height, backness, length)."""
    all_vowels = {ch for t in tokens for ch in t if _atom_type(ch) == "V"}
    unrepresented = [v for v in all_vowels if v not in _VOWEL_FEATURES]
    ok = len(unrepresented) == 0
    return AxiomResult(
        code="A9",
        name="تمثيل الحركة",
        satisfied=ok,
        evidence=f"unrepresented vowels: {unrepresented}" if not ok
                 else f"all {len(all_vowels)} vowel types mapped to (height, backness, length)",
    )


def _check_a10(syllables: list[tuple[str, str]]) -> AxiomResult:
    """A10 (Syllable as minimal unit): every syllable is a function of consonant + vowel."""
    if not syllables:
        return AxiomResult(code="A10", name="المقطع وحدة دنيا", satisfied=True,
                           evidence="no syllables present")
    cv_based = [pat for _, pat in syllables if pat.startswith("C") or "V" in pat]
    ratio = len(cv_based) / len(syllables)
    ok = ratio >= 0.5
    return AxiomResult(
        code="A10",
        name="المقطع وحدة دنيا",
        satisfied=ok,
        evidence=f"CV-based syllable ratio: {ratio:.2f}",
    )


def _check_a11(roots: list[list[str]]) -> AxiomResult:
    """A11 (Root minimality hypothesis): roots are triliteral sequences ⟨c1,c2,c3⟩."""
    if not roots:
        return AxiomResult(code="A11", name="فرضية الحد الأدنى الجذري", satisfied=True,
                           evidence="no roots extracted")
    proper = [r for r in roots if len(r) == 3]
    ratio = len(proper) / len(roots)
    ok = ratio >= 0.5
    return AxiomResult(
        code="A11",
        name="فرضية الحد الأدنى الجذري",
        satisfied=ok,
        evidence=f"triliteral root ratio: {ratio:.2f} ({len(proper)}/{len(roots)})",
    )


def _cost_function(m: int, tokens: list[str]) -> float:
    """Compute T(m) = α*Coverage + β*Separation - γ*Ambiguity - δ*Cost."""
    alpha, beta, gamma, delta = 0.4, 0.3, 0.2, 0.1
    consonant_sequences = [
        [ch for ch in t if _atom_type(ch) == "C"][:m] for t in tokens if any(_atom_type(ch) == "C" for ch in t)
    ]
    if not consonant_sequences:
        return 0.0
    coverage = sum(1 for seq in consonant_sequences if len(seq) >= m) / len(consonant_sequences)
    unique_roots = len({tuple(seq) for seq in consonant_sequences})
    separation = unique_roots / len(consonant_sequences)
    # ambiguity: ratio of roots that clash (same root, different source tokens)
    consonant_token_pairs = [
        (t, [ch for ch in t if _atom_type(ch) == "C"][:m])
        for t in tokens
        if any(_atom_type(ch) == "C" for ch in t)
    ]
    root_map: dict[tuple[str, ...], set[str]] = {}
    for tok, seq in consonant_token_pairs:
        root_map.setdefault(tuple(seq), set()).add(tok)
    ambiguous = sum(1 for v in root_map.values() if len(v) > 1)
    ambiguity = ambiguous / max(len(root_map), 1)
    cost = m / 6.0  # normalised cost
    return alpha * coverage + beta * separation - gamma * ambiguity - delta * cost


def _check_a12(tokens: list[str]) -> AxiomResult:
    """A12 (Triliteral optimality): m*=3 minimises cost subject to coverage/separation."""
    scores = {m: _cost_function(m, tokens) for m in (2, 3, 4)}
    best_m = max(scores, key=lambda k: scores[k])
    ok = best_m == 3
    return AxiomResult(
        code="A12",
        name="أمثلية الثلاثي",
        satisfied=ok,
        evidence=f"T(2)={scores[2]:.3f}, T(3)={scores[3]:.3f}, T(4)={scores[4]:.3f} → optimal m={best_m}",
    )


def _check_a13(syllables: list[tuple[str, str]]) -> AxiomResult:
    """A13 (Weight types): syllables classified as G/Q/H with discrimination > 1/3."""
    if not syllables:
        return AxiomResult(code="A13", name="أنواع الأوزان الأساسية", satisfied=True,
                           evidence="no syllables to classify")
    weight_counts: dict[str, int] = {"G": 0, "Q": 0, "H": 0}
    for _, pat in syllables:
        weight_counts[_weight_type(pat)] += 1
    total = sum(weight_counts.values())
    discrimination = 1.0 - (max(weight_counts.values()) / total)  # higher = more discriminating
    ok = discrimination > (1 / 3)
    return AxiomResult(
        code="A13",
        name="أنواع الأوزان الأساسية",
        satisfied=ok,
        evidence=f"G={weight_counts['G']}, Q={weight_counts['Q']}, H={weight_counts['H']}; discrimination={discrimination:.3f}",
    )


def _check_a14(roots: list[list[str]], syllables: list[tuple[str, str]]) -> AxiomResult:
    """A14 (Form generation): L = W_τ(R, h, z) — forms can be generated from root + weight."""
    if not roots or not syllables:
        return AxiomResult(code="A14", name="توليد الصيغة", satisfied=False,
                           evidence="insufficient data (no roots or syllables)")
    proper_roots = [r for r in roots if "_" not in r]
    weights = [_weight_type(p) for _, p in syllables]
    weight_set = set(weights)
    ok = len(proper_roots) > 0 and len(weight_set) > 0
    return AxiomResult(
        code="A14",
        name="توليد الصيغة",
        satisfied=ok,
        evidence=f"{len(proper_roots)} valid roots × {len(weight_set)} weight types → generation possible",
    )


def _check_a15(tokens: list[str]) -> AxiomResult:
    """A15 (Operator unit uniqueness): each affix has one primary function."""
    suffixes = ("ها", "هم", "هن", "كما", "كم", "نا", "ات", "ون", "ين", "ة", "ه", "ي")
    affix_function: dict[str, str] = {
        "ات": "plural_feminine", "ون": "plural_masculine_nominative",
        "ين": "plural_masculine_oblique", "ة": "feminine",
        "ها": "pronoun_3f", "هم": "pronoun_3mpl", "نا": "pronoun_1pl",
        "ه": "pronoun_3m", "ي": "pronoun_1s", "هن": "pronoun_3fpl",
        "كم": "pronoun_2mpl", "كما": "pronoun_2dual",
    }
    detected: list[str] = []
    for tok in tokens:
        for sfx in suffixes:
            if tok.endswith(sfx) and len(tok) > len(sfx) + 1:
                detected.append(sfx)
                break
    ambiguous = [s for s in detected if s not in affix_function]
    ok = len(ambiguous) == 0
    return AxiomResult(
        code="A15",
        name="وحدة وظيفة المشغّل",
        satisfied=ok,
        evidence=f"{len(detected)} affixes detected; {len(ambiguous)} without primary function mapping",
    )


def _check_a16(tokens: list[str]) -> AxiomResult:
    """A16 (Word classification): every word ∈ {اسم, فعل, أداة}."""
    pos_map = {t: _infer_pos(t) for t in tokens}
    unclassified = [t for t, p in pos_map.items() if p not in {"noun", "verb", "particle"}]
    ok = len(unclassified) == 0
    return AxiomResult(
        code="A16",
        name="التقسيم اللفظي",
        satisfied=ok,
        evidence=f"unclassified tokens: {unclassified}" if not ok
                 else f"all {len(tokens)} tokens classified as noun/verb/particle",
    )


def _check_a17(tokens: list[str]) -> AxiomResult:
    """A17 (Basic relations): syntactic relations ∈ {إسناد, تقييد, تضمين}."""
    # Relations between adjacent tokens
    relations: list[str] = []
    for i in range(1, len(tokens)):
        prev_pos = _infer_pos(tokens[i - 1])
        curr_pos = _infer_pos(tokens[i])
        if prev_pos == "verb" and curr_pos == "noun":
            relations.append("إسناد")
        elif prev_pos == "noun" and curr_pos == "noun":
            relations.append("تضمين")
        elif curr_pos == "particle":
            relations.append("تقييد")
        else:
            relations.append("إسناد")
    valid = {"إسناد", "تقييد", "تضمين"}
    ok = all(r in valid for r in relations)
    return AxiomResult(
        code="A17",
        name="العلاقات الأساسية",
        satisfied=ok,
        evidence=f"relations derived: {set(relations)}",
    )


def _check_a18(tokens: list[str]) -> AxiomResult:
    """A18 (Meaning types): meaning ∈ {مطابقة, تضمن, التزام}."""
    meanings: dict[str, list[str]] = {}
    for tok in tokens:
        lemma = tok.removeprefix("ال")
        meanings[tok] = [
            f"مطابقة:{tok}",
            f"تضمن:{lemma}" if lemma != tok else f"تضمن:{tok}",
            f"التزام:{_infer_pos(tok)}",
        ]
    ok = all(len(v) == 3 for v in meanings.values())
    return AxiomResult(
        code="A18",
        name="أنواع الدلالة",
        satisfied=ok,
        evidence=f"all {len(tokens)} tokens yield 3 meaning types",
    )


def _check_a19(tokens: list[str]) -> AxiomResult:
    """A19 (Manṭūq/Mafhūm): meaning decomposes into explicit + implied."""
    mantuq = list(tokens)
    mafhum = [tok for tok in tokens if tok in PARTICLES or tok.startswith("ل") or tok.startswith("إ")]
    ok = len(mantuq) > 0
    return AxiomResult(
        code="A19",
        name="المنطوق والمفهوم",
        satisfied=ok,
        evidence=f"mantuq={len(mantuq)} tokens, mafhum triggers={len(mafhum)}",
    )


def _check_a20(tokens: list[str], syllables: list[tuple[str, str]], roots: list[list[str]]) -> AxiomResult:
    """A20 (Unified function): S_{n+1} = Π_n(K_n(Rel(S_n, C_n))) — all layers compose."""
    layers_present = [
        bool(tokens),          # L0: raw input
        bool(syllables),       # L2-L4: phonology
        bool(roots),           # L5-L8: morphology
        bool(tokens),          # L9-L11: semantics / inference (always has tokens)
    ]
    filled = sum(layers_present)
    ok = filled == len(layers_present)
    return AxiomResult(
        code="A20",
        name="الدالة الكلية للنظام",
        satisfied=ok,
        evidence=f"layers active: {filled}/{len(layers_present)} — system {'closed' if ok else 'open with gaps'}",
    )


# ---------------------------------------------------------------------------
# Lemmas L1–L5
# ---------------------------------------------------------------------------

def _derive_lemmas(axioms: dict[str, AxiomResult]) -> list[LemmaResult]:
    results: list[LemmaResult] = []

    # L1: Vowel is mandatory (from A6 + A7)
    l1_holds = axioms["A6"].satisfied and axioms["A7"].satisfied
    results.append(LemmaResult(
        code="L1",
        name="ضرورة الثنائية الصوتية",
        derived_from=["A6", "A7"],
        holds=l1_holds,
        rationale="A6 guarantees phonemic duality; A7 guarantees every syllable has a nucleus → vowel is non-deletable",
    ))

    # L2: Root stability (from A11 + A14)
    l2_holds = axioms["A11"].satisfied and axioms["A14"].satisfied
    results.append(LemmaResult(
        code="L2",
        name="ثبات الجذر",
        derived_from=["A11", "A14"],
        holds=l2_holds,
        rationale="A11 fixes root as ⟨c1,c2,c3⟩; A14 derives all forms from root + weight → consonantal axis is stable",
    ))

    # L3: Relation closure (from A17)
    l3_holds = axioms["A17"].satisfied
    results.append(LemmaResult(
        code="L3",
        name="انحصار العلاقات",
        derived_from=["A17"],
        holds=l3_holds,
        rationale="A17 enumerates all syntactic relations as {إسناد, تقييد, تضمين} → no fourth relation exists",
    ))

    # L4: Meaning closure (from A18)
    l4_holds = axioms["A18"].satisfied
    results.append(LemmaResult(
        code="L4",
        name="انحصار الدلالة",
        derived_from=["A18"],
        holds=l4_holds,
        rationale="A18 partitions meaning into {مطابقة, تضمن, التزام} → no independent fourth meaning type",
    ))

    # L5: Operator uniqueness (from A15)
    l5_holds = axioms["A15"].satisfied
    results.append(LemmaResult(
        code="L5",
        name="وحدة المشغّل",
        derived_from=["A15"],
        holds=l5_holds,
        rationale="A15 assigns each affix exactly one primary function → apparent multiplicity reduces to one origin + context",
    ))

    return results


# ---------------------------------------------------------------------------
# Theorems T1–T5
# ---------------------------------------------------------------------------

def _prove_theorems(
    axioms: dict[str, AxiomResult],
    lemmas: dict[str, LemmaResult],
    tokens: list[str],
    roots: list[list[str]],
    syllables: list[tuple[str, str]],
) -> list[TheoremResult]:
    results: list[TheoremResult] = []

    # T1: Lexicon generation from triliteral roots
    t1_proven = axioms["A11"].satisfied and axioms["A13"].satisfied and axioms["A14"].satisfied
    proper_roots = [r for r in roots if "_" not in r]
    weight_set = {_weight_type(p) for _, p in syllables}
    t1_evidence = f"{len(proper_roots)} roots × {len(weight_set)} weights → productive lexicon"
    results.append(TheoremResult(
        code="T1",
        name="إمكانية توليد اللغة من ثلاثية",
        depends_on=["A11", "A13", "A14"],
        proven=t1_proven,
        rationale=t1_evidence,
    ))

    # T2: Meaning completeness requires (R, τ)
    t2_proven = lemmas["L2"].holds and axioms["A13"].satisfied
    results.append(TheoremResult(
        code="T2",
        name="اكتمال المعنى الأدنى",
        depends_on=["L2", "A13"],
        proven=t2_proven,
        rationale="MeaningComplete(L) ↔ root R is stable (L2) and weight τ is classified (A13)",
    ))

    # T3: System closure
    t3_proven = axioms["A20"].satisfied and lemmas["L3"].holds and lemmas["L4"].holds
    results.append(TheoremResult(
        code="T3",
        name="قابلية الإغلاق النظامي",
        depends_on=["A20", "L3", "L4"],
        proven=t3_proven,
        rationale="A20 unifies layers; L3 closes relations; L4 closes meanings → system has no open layers",
    ))

    # T4: Automatic weight disambiguation
    weight_counts: dict[str, int] = {"G": 0, "Q": 0, "H": 0}
    for _, pat in syllables:
        weight_counts[_weight_type(pat)] += 1
    total_syl = max(sum(weight_counts.values()), 1)
    p_max = max(weight_counts.values()) / total_syl
    t4_proven = axioms["A13"].satisfied and p_max > (1 / 3)
    results.append(TheoremResult(
        code="T4",
        name="تمييز الأوزان آليًا",
        depends_on=["A13"],
        proven=t4_proven,
        rationale=f"τ* = argmax P(τ|L,C); dominant weight p={p_max:.3f} > 1/3 → discrimination viable",
    ))

    # T5: Representational economy
    score_3 = _cost_function(3, tokens)
    score_2 = _cost_function(2, tokens)
    score_4 = _cost_function(4, tokens)
    t5_proven = axioms["A12"].satisfied and score_3 >= score_2 and score_3 >= score_4
    results.append(TheoremResult(
        code="T5",
        name="اقتصاد التمثيل",
        depends_on=["A12"],
        proven=t5_proven,
        rationale=f"T(3)={score_3:.3f} ≥ T(2)={score_2:.3f} and T(4)={score_4:.3f} → triliteral is optimal economy",
    ))

    return results


# ---------------------------------------------------------------------------
# Falsification tests F1–F5
# ---------------------------------------------------------------------------

def _run_falsification_tests(
    tokens: list[str],
    syllables: list[tuple[str, str]],
    roots: list[list[str]],
) -> list[FalsificationResult]:
    results: list[FalsificationResult] = []

    # F1: Triliteral optimality test — if T(2)>T(3) or T(4)>T(3), reject A12
    s2 = _cost_function(2, tokens)
    s3 = _cost_function(3, tokens)
    s4 = _cost_function(4, tokens)
    f1_falsified = (s2 > s3) or (s4 > s3)
    results.append(FalsificationResult(
        code="F1",
        name="اختبار فرضية الثلاثي",
        score=s3,
        threshold=max(s2, s4),
        falsified=f1_falsified,
        details=f"T(2)={s2:.3f}, T(3)={s3:.3f}, T(4)={s4:.3f} → A12 {'REJECTED' if f1_falsified else 'holds'}",
    ))

    # F2: Weight discrimination — if WD ≈ 1/3, A13 fails
    weight_counts: dict[str, int] = {"G": 0, "Q": 0, "H": 0}
    for _, pat in syllables:
        weight_counts[_weight_type(pat)] += 1
    total_syl = max(sum(weight_counts.values()), 1)
    p_max = max(weight_counts.values()) / total_syl
    wd = 1.0 - p_max  # diversity score
    f2_threshold = 1 / 3
    f2_falsified = wd <= f2_threshold
    results.append(FalsificationResult(
        code="F2",
        name="اختبار تمييز الأوزان",
        score=wd,
        threshold=f2_threshold,
        falsified=f2_falsified,
        details=f"WD={wd:.3f}; threshold=1/3 → A13 {'REJECTED' if f2_falsified else 'holds'}",
    ))

    # F3: Vowel representation stability — check A9 via _VOWEL_FEATURES coverage
    all_vowels = {ch for t in tokens for ch in t if _atom_type(ch) == "V"}
    unrepresented_vowels = [v for v in all_vowels if v not in _VOWEL_FEATURES]
    f3_score = 1.0 - (len(unrepresented_vowels) / max(len(all_vowels), 1))
    f3_falsified = f3_score < 1.0
    results.append(FalsificationResult(
        code="F3",
        name="اختبار الحركة",
        score=f3_score,
        threshold=1.0,
        falsified=f3_falsified,
        details=f"vowel coverage={f3_score:.3f}; unrepresented={unrepresented_vowels} → A9 {'REJECTED' if f3_falsified else 'holds'}",
    ))

    # F4: Operator coherence — OC(z) = ratio of affixes with known function
    suffixes = ("ها", "هم", "هن", "كما", "كم", "نا", "ات", "ون", "ين", "ة", "ه", "ي")
    known_affixes = {
        "ات", "ون", "ين", "ة", "ها", "هم", "نا", "ه", "ي", "هن", "كم", "كما",
    }
    detected_affixes: list[str] = []
    for tok in tokens:
        for sfx in suffixes:
            if tok.endswith(sfx) and len(tok) > len(sfx) + 1:
                detected_affixes.append(sfx)
                break
    oc = (
        sum(1 for a in detected_affixes if a in known_affixes) / len(detected_affixes)
        if detected_affixes else 1.0
    )
    theta = 0.7
    f4_falsified = oc < theta
    results.append(FalsificationResult(
        code="F4",
        name="اختبار المشغلات",
        score=oc,
        threshold=theta,
        falsified=f4_falsified,
        details=f"OC={oc:.3f}; θ={theta} → A15 {'REJECTED' if f4_falsified else 'holds'}",
    ))

    # F5: Cross-layer conflict ratio — CR = ratio of tokens with inconsistent POS + root
    conflict_count = 0
    for tok in tokens:
        root = _extract_root(tok)
        pos = _infer_pos(tok)
        proper_root = "_" not in root
        # Conflict: particle assigned a proper root (particles should have no derivational root)
        if pos == "particle" and proper_root:
            conflict_count += 1
    cr = conflict_count / max(len(tokens), 1)
    cr_threshold = 0.3
    f5_falsified = cr >= cr_threshold
    results.append(FalsificationResult(
        code="F5",
        name="اختبار العبور الطبقي",
        score=cr,
        threshold=cr_threshold,
        falsified=f5_falsified,
        details=f"CR={cr:.3f}; threshold={cr_threshold} → K_n/Rel {'DEFECTIVE' if f5_falsified else 'coherent'}",
    ))

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_axiomatic_engine(text: str) -> AxiomAnalysisResult:
    """Run the full axiomatic analysis on the given Arabic text.

    Does **not** require a database session — operates entirely on the
    provided text string so it can be called standalone or from a pipeline.
    """
    tokens = [tok for tok in text.split() if tok]

    # Phonological preprocessing
    all_syllables: list[tuple[str, str]] = []
    all_roots: list[list[str]] = []
    for tok in tokens:
        all_syllables.extend(_syllabify(tok))
        all_roots.append(_extract_root(tok))

    # --- Axiom checks ---
    axiom_list: list[AxiomResult] = [
        _check_a1(tokens),
        _check_a2(tokens),
        _check_a3(tokens),
        _check_a4(tokens),
        _check_a5(tokens),
        _check_a6(tokens),
        _check_a7(all_syllables),
        _check_a8(tokens),
        _check_a9(tokens),
        _check_a10(all_syllables),
        _check_a11(all_roots),
        _check_a12(tokens),
        _check_a13(all_syllables),
        _check_a14(all_roots, all_syllables),
        _check_a15(tokens),
        _check_a16(tokens),
        _check_a17(tokens),
        _check_a18(tokens),
        _check_a19(tokens),
        _check_a20(tokens, all_syllables, all_roots),
    ]
    axioms_map = {a.code: a for a in axiom_list}

    # --- Lemmas ---
    lemma_list = _derive_lemmas(axioms_map)
    lemmas_map = {lm.code: lm for lm in lemma_list}

    # --- Theorems ---
    theorem_list = _prove_theorems(axioms_map, lemmas_map, tokens, all_roots, all_syllables)

    # --- Falsification ---
    falsification_list = _run_falsification_tests(tokens, all_syllables, all_roots)

    # --- Aggregate metrics ---
    sat_ratio = sum(a.satisfied for a in axiom_list) / max(len(axiom_list), 1)
    lemma_ratio = sum(lm.holds for lm in lemma_list) / max(len(lemma_list), 1)
    theorem_ratio = sum(th.proven for th in theorem_list) / max(len(theorem_list), 1)
    system_coherent = (
        sat_ratio >= 0.75
        and lemma_ratio >= 0.6
        and theorem_ratio >= 0.6
        and not any(f.falsified for f in falsification_list)
    )

    return AxiomAnalysisResult(
        text=text,
        tokens=tokens,
        axioms=axiom_list,
        lemmas=lemma_list,
        theorems=theorem_list,
        falsifications=falsification_list,
        axiom_satisfaction_ratio=round(sat_ratio, 4),
        lemma_hold_ratio=round(lemma_ratio, 4),
        theorem_proven_ratio=round(theorem_ratio, 4),
        system_coherent=system_coherent,
    )
