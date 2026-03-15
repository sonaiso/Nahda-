"""
Standard Arabic morphological templates.

Each entry represents a Template node in the graph schema.
Coverage:
  - Verb forms I–X (triliteral) with masdar variants
  - Common noun patterns (ism fa'il, ism maf'ul, sifa mushabbaha, etc.)
  - Time/place noun (ism zaman/makan)
  - Instrument noun (ism ala)
  - Quadriliteral forms I–II
  - Diminutive (tashghir)

For each Template:
  - template_id    : stable machine-readable key
  - surface_pattern: Arabic surface form with F/A/L slots (or ف/ع/ل)
  - slots          : consonant slot labels
  - level          : triliteral / quadriliteral
  - verb_form      : I..X for verbs (None for nouns)
  - derivation_type: primary semantic derivation type
  - op_hooks       : list of Op ids that may fire on this template
  - constraints    : list of Constraint feature/required_value pairs
  - example        : (optional) worked example in Arabic

The templates are returned as plain dicts so they are JSON-serialisable
and can be seeded into the database or exported to Neo4j without any
additional transformation.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_T = dict[str, Any]


def _tmpl(
    template_id: str,
    surface_pattern: str,
    slots: str,
    level: str,
    verb_form: str | None,
    derivation_type: str,
    op_hooks: list[str],
    constraints: list[dict[str, str]],
    example: str = "",
) -> _T:
    return {
        "template_id": template_id,
        "surface_pattern": surface_pattern,
        "slots": slots,
        "level": level,
        "verb_form": verb_form,
        "derivation_type": derivation_type,
        "op_hooks": op_hooks,
        "constraints": constraints,
        "example": example,
    }


# ---------------------------------------------------------------------------
# Root classes referenced in op_hooks
# ---------------------------------------------------------------------------

ROOT_CLASSES: list[_T] = [
    {"class_name": "sound", "description": "جذر صحيح سالم"},
    {"class_name": "hamzated_f", "description": "مهموز الفاء"},
    {"class_name": "hamzated_a", "description": "مهموز العين"},
    {"class_name": "hamzated_l", "description": "مهموز اللام"},
    {"class_name": "weak_f_w", "description": "مثال واوي (الفاء واو)"},
    {"class_name": "weak_f_y", "description": "مثال يائي (الفاء ياء)"},
    {"class_name": "weak_a_w", "description": "أجوف واوي (العين واو)"},
    {"class_name": "weak_a_y", "description": "أجوف يائي (العين ياء)"},
    {"class_name": "weak_l_w", "description": "ناقص واوي (اللام واو)"},
    {"class_name": "weak_l_y", "description": "ناقص يائي (اللام ياء)"},
    {"class_name": "doubled", "description": "مضاعف (العين = اللام)"},
    {"class_name": "weak_fa_l", "description": "لفيف مفروق"},
    {"class_name": "weak_fa_la", "description": "لفيف مقرون"},
]

# ---------------------------------------------------------------------------
# Phonological Ops
# ---------------------------------------------------------------------------

OPS: list[_T] = [
    {
        "op_id": "op_i3lal_qalb",
        "op_type": "i3lal",
        "priority": 10,
        "applies_to_classes": ["weak_a_w", "weak_a_y", "weak_l_w", "weak_l_y"],
        "description": "إعلال بالقلب: قلب حرف العلة",
    },
    {
        "op_id": "op_i3lal_hathf",
        "op_type": "i3lal",
        "priority": 9,
        "applies_to_classes": ["weak_f_w", "weak_f_y", "weak_l_w", "weak_l_y"],
        "description": "إعلال بالحذف: حذف حرف العلة",
    },
    {
        "op_id": "op_i3lal_taskeen",
        "op_type": "i3lal",
        "priority": 8,
        "applies_to_classes": ["weak_a_w", "weak_a_y"],
        "description": "إعلال بالتسكين: نقل الحركة من حرف العلة إلى ما قبله",
    },
    {
        "op_id": "op_idgham_doubled",
        "op_type": "idgham",
        "priority": 7,
        "applies_to_classes": ["doubled"],
        "description": "إدغام المثلين في المضاعف",
    },
    {
        "op_id": "op_hamza_wasl",
        "op_type": "hamza",
        "priority": 6,
        "applies_to_classes": ["hamzated_f", "hamzated_a", "hamzated_l"],
        "description": "تخفيف الهمزة أو إبدالها حسب الموضع",
    },
    {
        "op_id": "op_hamza_kat3",
        "op_type": "hamza",
        "priority": 5,
        "applies_to_classes": ["hamzated_f"],
        "description": "همزة القطع في أوزان الإفعال",
    },
    {
        "op_id": "op_ibdal_ta_taa",
        "op_type": "ibdal",
        "priority": 4,
        "applies_to_classes": ["weak_f_w"],
        "description": "إبدال تاء الافتعال طاءً بعد الواو والزاي",
    },
    {
        "op_id": "op_ibdal_ta_dal",
        "op_type": "ibdal",
        "priority": 4,
        "applies_to_classes": ["weak_f_w"],
        "description": "إبدال تاء الافتعال دالاً بعد الدال والذال",
    },
    {
        "op_id": "op_tashghir_wuqays",
        "op_type": "ibdal",
        "priority": 2,
        "applies_to_classes": ["sound"],
        "description": "تصغير: تحويل فَعَل → فُعَيْل",
    },
]

# ---------------------------------------------------------------------------
# Standard Arabic Templates
# ---------------------------------------------------------------------------

TEMPLATES: list[_T] = [
    # ════════════════════════════════════════════════════════
    # FORM I — Verbs (past/present/masdar variants)
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fi_past_a",
        "فَعَلَ",
        "F,A,L",
        "triliteral",
        "I",
        "Verb",
        ["op_i3lal_qalb", "op_i3lal_hathf", "op_idgham_doubled", "op_hamza_kat3"],
        [{"feature": "vowel_pattern_past", "required_value": "a-a"}],
        "كَتَبَ",
    ),
    _tmpl(
        "fi_past_i",
        "فَعِلَ",
        "F,A,L",
        "triliteral",
        "I",
        "Verb",
        ["op_i3lal_qalb", "op_i3lal_taskeen"],
        [{"feature": "vowel_pattern_past", "required_value": "a-i"}],
        "عَلِمَ",
    ),
    _tmpl(
        "fi_past_u",
        "فَعُلَ",
        "F,A,L",
        "triliteral",
        "I",
        "Verb",
        [],
        [
            {"feature": "vowel_pattern_past", "required_value": "a-u"},
            {"feature": "verb_type", "required_value": "intransitive"},
        ],
        "حَسُنَ",
    ),
    _tmpl(
        "fi_pres_a",
        "يَفْعَلُ",
        "F,A,L",
        "triliteral",
        "I",
        "Verb",
        ["op_i3lal_qalb", "op_i3lal_hathf"],
        [{"feature": "vowel_pattern_pres", "required_value": "a"}],
        "يَكْتُبُ",
    ),
    _tmpl(
        "fi_pres_i",
        "يَفْعِلُ",
        "F,A,L",
        "triliteral",
        "I",
        "Verb",
        ["op_i3lal_taskeen"],
        [{"feature": "vowel_pattern_pres", "required_value": "i"}],
        "يَضْرِبُ",
    ),
    _tmpl(
        "fi_pres_u",
        "يَفْعُلُ",
        "F,A,L",
        "triliteral",
        "I",
        "Verb",
        [],
        [{"feature": "vowel_pattern_pres", "required_value": "u"}],
        "يَنْصُرُ",
    ),
    _tmpl(
        "fi_masdar_f3l",
        "فَعْل",
        "F,A,L",
        "triliteral",
        "I",
        "Masdar",
        [],
        [{"feature": "masdar_type", "required_value": "plain"}],
        "ضَرْب",
    ),
    _tmpl(
        "fi_masdar_fi3al",
        "فِعَال",
        "F,A,L",
        "triliteral",
        "I",
        "Masdar",
        [],
        [{"feature": "masdar_type", "required_value": "intensified"}],
        "جِهَاد",
    ),
    _tmpl(
        "fi_masdar_fu3ul",
        "فُعُول",
        "F,A,L",
        "triliteral",
        "I",
        "Masdar",
        [],
        [{"feature": "masdar_type", "required_value": "motion"}],
        "دُخُول",
    ),
    _tmpl(
        "fi_masdar_fa3ala",
        "فَعَالَة",
        "F,A,L",
        "triliteral",
        "I",
        "Masdar",
        [],
        [{"feature": "masdar_type", "required_value": "profession"}],
        "تِجَارَة",
    ),
    _tmpl(
        "fi_masdar_fi3la",
        "فِعْلَة",
        "F,A,L",
        "triliteral",
        "I",
        "Masdar",
        [],
        [{"feature": "masdar_type", "required_value": "single_occurrence"}],
        "ضِحْكَة",
    ),
    # ════════════════════════════════════════════════════════
    # FORM II — تَفْعِيل / فَعَّلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fii_past",
        "فَعَّلَ",
        "F,A,L",
        "triliteral",
        "II",
        "Verb",
        ["op_hamza_kat3"],
        [{"feature": "shadda", "required_value": "ain"}],
        "كَسَّرَ",
    ),
    _tmpl(
        "fii_masdar",
        "تَفْعِيل",
        "F,A,L",
        "triliteral",
        "II",
        "Masdar",
        [],
        [],
        "تَكْسِير",
    ),
    _tmpl(
        "fii_ism_fa3il",
        "مُفَعِّل",
        "F,A,L",
        "triliteral",
        "II",
        "Agent",
        [],
        [],
        "مُكَسِّر",
    ),
    _tmpl(
        "fii_ism_maf3ul",
        "مُفَعَّل",
        "F,A,L",
        "triliteral",
        "II",
        "Patient",
        [],
        [],
        "مُكَسَّر",
    ),
    # ════════════════════════════════════════════════════════
    # FORM III — مُفَاعَلَة / فَاعَلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fiii_past",
        "فَاعَلَ",
        "F,A,L",
        "triliteral",
        "III",
        "Verb",
        ["op_i3lal_qalb"],
        [],
        "قَاتَلَ",
    ),
    _tmpl(
        "fiii_masdar",
        "مُفَاعَلَة",
        "F,A,L",
        "triliteral",
        "III",
        "Masdar",
        [],
        [],
        "مُقَاتَلَة",
    ),
    _tmpl(
        "fiii_masdar_fi3al",
        "فِعَال",
        "F,A,L",
        "triliteral",
        "III",
        "Masdar",
        [],
        [],
        "قِتَال",
    ),
    # ════════════════════════════════════════════════════════
    # FORM IV — إِفْعَال / أَفْعَلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fiv_past",
        "أَفْعَلَ",
        "F,A,L",
        "triliteral",
        "IV",
        "Verb",
        ["op_hamza_kat3", "op_i3lal_qalb"],
        [],
        "أَكْرَمَ",
    ),
    _tmpl(
        "fiv_masdar",
        "إِفْعَال",
        "F,A,L",
        "triliteral",
        "IV",
        "Masdar",
        ["op_hamza_wasl"],
        [],
        "إِكْرَام",
    ),
    _tmpl(
        "fiv_ism_fa3il",
        "مُفْعِل",
        "F,A,L",
        "triliteral",
        "IV",
        "Agent",
        [],
        [],
        "مُكْرِم",
    ),
    _tmpl(
        "fiv_ism_maf3ul",
        "مُفْعَل",
        "F,A,L",
        "triliteral",
        "IV",
        "Patient",
        [],
        [],
        "مُكْرَم",
    ),
    # ════════════════════════════════════════════════════════
    # FORM V — تَفَعُّل / تَفَعَّلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fv_past",
        "تَفَعَّلَ",
        "F,A,L",
        "triliteral",
        "V",
        "Verb",
        [],
        [{"feature": "prefix", "required_value": "ta"}],
        "تَكَسَّرَ",
    ),
    _tmpl(
        "fv_masdar",
        "تَفَعُّل",
        "F,A,L",
        "triliteral",
        "V",
        "Masdar",
        [],
        [],
        "تَكَسُّر",
    ),
    # ════════════════════════════════════════════════════════
    # FORM VI — تَفَاعُل / تَفَاعَلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fvi_past",
        "تَفَاعَلَ",
        "F,A,L",
        "triliteral",
        "VI",
        "Verb",
        ["op_i3lal_qalb"],
        [],
        "تَقَاتَلَ",
    ),
    _tmpl(
        "fvi_masdar",
        "تَفَاعُل",
        "F,A,L",
        "triliteral",
        "VI",
        "Masdar",
        [],
        [],
        "تَقَاتُل",
    ),
    # ════════════════════════════════════════════════════════
    # FORM VII — اِنْفِعَال / اِنْفَعَلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fvii_past",
        "اِنْفَعَلَ",
        "F,A,L",
        "triliteral",
        "VII",
        "Verb",
        ["op_hamza_wasl"],
        [{"feature": "transitivity", "required_value": "intransitive"}],
        "اِنْكَسَرَ",
    ),
    _tmpl(
        "fvii_masdar",
        "اِنْفِعَال",
        "F,A,L",
        "triliteral",
        "VII",
        "Masdar",
        [],
        [],
        "اِنْكِسَار",
    ),
    # ════════════════════════════════════════════════════════
    # FORM VIII — اِفْتِعَال / اِفْتَعَلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fviii_past",
        "اِفْتَعَلَ",
        "F,A,L",
        "triliteral",
        "VIII",
        "Verb",
        ["op_ibdal_ta_taa", "op_ibdal_ta_dal", "op_hamza_wasl", "op_idgham_doubled"],
        [],
        "اِجْتَمَعَ",
    ),
    _tmpl(
        "fviii_masdar",
        "اِفْتِعَال",
        "F,A,L",
        "triliteral",
        "VIII",
        "Masdar",
        [],
        [],
        "اِجْتِمَاع",
    ),
    # ════════════════════════════════════════════════════════
    # FORM IX — اِفْعِلَال / اِفْعَلَّ  (colours & defects)
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fix_past",
        "اِفْعَلَّ",
        "F,A,L",
        "triliteral",
        "IX",
        "Verb",
        ["op_idgham_doubled"],
        [{"feature": "semantic_domain", "required_value": "colour_defect"}],
        "اِحْمَرَّ",
    ),
    _tmpl(
        "fix_masdar",
        "اِفْعِلَال",
        "F,A,L",
        "triliteral",
        "IX",
        "Masdar",
        [],
        [],
        "اِحْمِرَار",
    ),
    # ════════════════════════════════════════════════════════
    # FORM X — اِسْتِفْعَال / اِسْتَفْعَلَ
    # ════════════════════════════════════════════════════════
    _tmpl(
        "fx_past",
        "اِسْتَفْعَلَ",
        "F,A,L",
        "triliteral",
        "X",
        "Verb",
        ["op_i3lal_qalb", "op_hamza_wasl"],
        [],
        "اِسْتَخْرَجَ",
    ),
    _tmpl(
        "fx_pres",
        "يَسْتَفْعِلُ",
        "F,A,L",
        "triliteral",
        "X",
        "Verb",
        ["op_i3lal_taskeen"],
        [],
        "يَسْتَخْرِجُ",
    ),
    _tmpl(
        "fx_masdar",
        "اِسْتِفْعَال",
        "F,A,L",
        "triliteral",
        "X",
        "Masdar",
        [],
        [],
        "اِسْتِخْرَاج",
    ),
    _tmpl(
        "fx_ism_fa3il",
        "مُسْتَفْعِل",
        "F,A,L",
        "triliteral",
        "X",
        "Agent",
        [],
        [],
        "مُسْتَخْرِج",
    ),
    _tmpl(
        "fx_ism_maf3ul",
        "مُسْتَفْعَل",
        "F,A,L",
        "triliteral",
        "X",
        "Patient",
        [],
        [],
        "مُسْتَخْرَج",
    ),
    # ════════════════════════════════════════════════════════
    # COMMON NOUN PATTERNS (Form I base)
    # ════════════════════════════════════════════════════════
    _tmpl(
        "n_ism_fa3il",
        "فَاعِل",
        "F,A,L",
        "triliteral",
        None,
        "Agent",
        ["op_i3lal_qalb"],
        [],
        "كَاتِب",
    ),
    _tmpl(
        "n_ism_maf3ul",
        "مَفْعُول",
        "F,A,L",
        "triliteral",
        None,
        "Patient",
        [],
        [],
        "مَكْتُوب",
    ),
    _tmpl(
        "n_sifa_mushabbaha",
        "فَعِيل",
        "F,A,L",
        "triliteral",
        None,
        "Adjective",
        [],
        [],
        "كَرِيم",
    ),
    _tmpl(
        "n_sifa_mushabbaha_fa3ul",
        "فَعُول",
        "F,A,L",
        "triliteral",
        None,
        "Adjective",
        [],
        [{"feature": "intensification", "required_value": "mubalaagha"}],
        "صَبُور",
    ),
    _tmpl(
        "n_mubalaagha_fa33al",
        "فَعَّال",
        "F,A,L",
        "triliteral",
        None,
        "Agent",
        [],
        [{"feature": "intensification", "required_value": "mubalaagha"}],
        "كَذَّاب",
    ),
    _tmpl(
        "n_mubalaagha_fa3il",
        "فَعِل",
        "F,A,L",
        "triliteral",
        None,
        "Agent",
        [],
        [],
        "حَذِر",
    ),
    _tmpl(
        "n_mubalaagha_mif3al",
        "مِفْعَال",
        "F,A,L",
        "triliteral",
        None,
        "Agent",
        [],
        [{"feature": "intensification", "required_value": "mubalaagha"}],
        "مِعْطَاء",
    ),
    _tmpl(
        "n_ism_tafdil",
        "أَفْعَل",
        "F,A,L",
        "triliteral",
        None,
        "Comparative",
        ["op_hamza_kat3"],
        [],
        "أَكْبَر",
    ),
    _tmpl(
        "n_ism_zaman_makan",
        "مَفْعَل",
        "F,A,L",
        "triliteral",
        None,
        "TimePlace",
        [],
        [],
        "مَكْتَب",
    ),
    _tmpl(
        "n_ism_zaman_makan_maf3il",
        "مَفْعِل",
        "F,A,L",
        "triliteral",
        None,
        "TimePlace",
        [],
        [],
        "مَجْلِس",
    ),
    _tmpl(
        "n_ism_ala",
        "مِفْعَل",
        "F,A,L",
        "triliteral",
        None,
        "Instrument",
        [],
        [],
        "مِبْرَد",
    ),
    _tmpl(
        "n_ism_ala_mif3ala",
        "مِفْعَلَة",
        "F,A,L",
        "triliteral",
        None,
        "Instrument",
        [],
        [],
        "مِكْنَسَة",
    ),
    _tmpl(
        "n_ism_ala_mif3al2",
        "مِفْعَال",
        "F,A,L",
        "triliteral",
        None,
        "Instrument",
        [],
        [],
        "مِفْتَاح",
    ),
    _tmpl(
        "n_jama3_taksir_af3al",
        "أَفْعَال",
        "F,A,L",
        "triliteral",
        None,
        "Plural",
        ["op_hamza_kat3"],
        [],
        "أَقْوَال",
    ),
    _tmpl(
        "n_jama3_taksir_fu3ul",
        "فُعُول",
        "F,A,L",
        "triliteral",
        None,
        "Plural",
        [],
        [],
        "كُتُب",
    ),
    _tmpl(
        "n_jama3_taksir_fi3al",
        "فِعَال",
        "F,A,L",
        "triliteral",
        None,
        "Plural",
        [],
        [],
        "كِتَاب",
    ),
    _tmpl(
        "n_tashghir",
        "فُعَيْل",
        "F,A,L",
        "triliteral",
        None,
        "Diminutive",
        ["op_tashghir_wuqays"],
        [],
        "كُتَيْب",
    ),
    # ════════════════════════════════════════════════════════
    # QUADRILITERAL — Form I + II
    # ════════════════════════════════════════════════════════
    _tmpl(
        "q_fi_past",
        "فَعْلَلَ",
        "F1,A,L1,L2",
        "quadriliteral",
        "QI",
        "Verb",
        [],
        [],
        "دَحْرَجَ",
    ),
    _tmpl(
        "q_fi_masdar",
        "فَعْلَلَة",
        "F1,A,L1,L2",
        "quadriliteral",
        "QI",
        "Masdar",
        [],
        [],
        "دَحْرَجَة",
    ),
    _tmpl(
        "q_fii_past",
        "تَفَعْلَلَ",
        "F1,A,L1,L2",
        "quadriliteral",
        "QII",
        "Verb",
        [],
        [],
        "تَدَحْرَجَ",
    ),
    _tmpl(
        "q_fii_masdar",
        "تَفَعْلُل",
        "F1,A,L1,L2",
        "quadriliteral",
        "QII",
        "Masdar",
        [],
        [],
        "تَدَحْرُج",
    ),
]


def get_templates() -> list[_T]:
    """Return all standard Arabic templates."""
    return TEMPLATES


def get_templates_by_form(verb_form: str) -> list[_T]:
    """Return templates for a specific verb form (I..X, QI, QII)."""
    return [t for t in TEMPLATES if t["verb_form"] == verb_form]


def get_templates_by_derivation(derivation_type: str) -> list[_T]:
    """Return templates by primary derivation type."""
    return [t for t in TEMPLATES if t["derivation_type"] == derivation_type]


def get_root_classes() -> list[_T]:
    """Return all root classes."""
    return ROOT_CLASSES


def get_ops() -> list[_T]:
    """Return all phonological operations."""
    return OPS
