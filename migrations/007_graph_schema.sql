-- 007_graph_schema.sql
-- Graph Schema nodes and edges for the Arabic Fractal Engine.
-- Implements the full Label set (A-H + Core) from the schema specification.

-- ── A) Text layer ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_tokens (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    surface TEXT NOT NULL,
    norm TEXT NOT NULL,
    tok_index INTEGER NOT NULL DEFAULT 0,
    is_punct INTEGER NOT NULL DEFAULT 0,
    prev_token_id TEXT,
    next_token_id TEXT,
    UNIQUE(run_id, tok_index)
);
CREATE INDEX IF NOT EXISTS idx_g_tokens_run_id ON g_tokens(run_id);
CREATE INDEX IF NOT EXISTS idx_g_tokens_surface ON g_tokens(surface);

-- ── B) Graphemic layer ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_diacritics (
    id TEXT PRIMARY KEY,
    grapheme_id TEXT NOT NULL REFERENCES grapheme_units(id) ON DELETE CASCADE,
    mark TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_g_diacritics_grapheme ON g_diacritics(grapheme_id);

-- ── D) Morpheme / Segmentation ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_morpheme_lattices (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    token_id TEXT NOT NULL REFERENCES g_tokens(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_g_lattices_run_id ON g_morpheme_lattices(run_id);
CREATE INDEX IF NOT EXISTS idx_g_lattices_token_id ON g_morpheme_lattices(token_id);

CREATE TABLE IF NOT EXISTS g_morphemes (
    id TEXT PRIMARY KEY,
    lattice_id TEXT NOT NULL REFERENCES g_morpheme_lattices(id) ON DELETE CASCADE,
    form TEXT NOT NULL,
    morph_type TEXT NOT NULL,
    gloss TEXT NOT NULL DEFAULT '',
    path_rank INTEGER NOT NULL DEFAULT 1,
    prev_morpheme_id TEXT,
    next_morpheme_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_g_morphemes_lattice ON g_morphemes(lattice_id);

CREATE TABLE IF NOT EXISTS g_stems (
    id TEXT PRIMARY KEY,
    morpheme_id TEXT NOT NULL REFERENCES g_morphemes(id) ON DELETE CASCADE,
    stem_surface TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_g_stems_morpheme ON g_stems(morpheme_id);
CREATE INDEX IF NOT EXISTS idx_g_stems_surface ON g_stems(stem_surface);

-- ── E) Morphology ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_root_classes (
    id TEXT PRIMARY KEY,
    class_name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    UNIQUE(class_name)
);

CREATE TABLE IF NOT EXISTS g_roots (
    id TEXT PRIMARY KEY,
    root TEXT NOT NULL,
    radicals_count INTEGER NOT NULL DEFAULT 3,
    root_class_id TEXT REFERENCES g_root_classes(id) ON DELETE SET NULL,
    UNIQUE(root)
);
CREATE INDEX IF NOT EXISTS idx_g_roots_root ON g_roots(root);

CREATE TABLE IF NOT EXISTS g_patterns (
    id TEXT PRIMARY KEY,
    pattern TEXT NOT NULL,
    slots TEXT NOT NULL DEFAULT 'F,A,L',
    UNIQUE(pattern)
);

CREATE TABLE IF NOT EXISTS g_templates (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    surface_pattern TEXT NOT NULL,
    slots TEXT NOT NULL DEFAULT 'F,A,L',
    level TEXT NOT NULL DEFAULT 'triliteral',
    verb_form TEXT,
    pattern_id TEXT REFERENCES g_patterns(id) ON DELETE SET NULL,
    UNIQUE(template_id)
);
CREATE INDEX IF NOT EXISTS idx_g_templates_template_id ON g_templates(template_id);

CREATE TABLE IF NOT EXISTS g_derivation_types (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    family TEXT NOT NULL DEFAULT 'noun',
    template_id TEXT REFERENCES g_templates(id) ON DELETE SET NULL,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS g_lexemes (
    id TEXT PRIMARY KEY,
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,
    is_jamid INTEGER NOT NULL DEFAULT 0,
    register TEXT NOT NULL DEFAULT 'fus7a',
    root_id TEXT REFERENCES g_roots(id) ON DELETE SET NULL,
    UNIQUE(lemma, pos)
);
CREATE INDEX IF NOT EXISTS idx_g_lexemes_lemma ON g_lexemes(lemma);

-- ── Candidates (per run) ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_root_candidates (
    id TEXT PRIMARY KEY,
    stem_id TEXT NOT NULL REFERENCES g_stems(id) ON DELETE CASCADE,
    root_id TEXT NOT NULL REFERENCES g_roots(id) ON DELETE CASCADE,
    score REAL NOT NULL DEFAULT 0.5,
    rank INTEGER NOT NULL DEFAULT 1,
    method TEXT NOT NULL DEFAULT 'consonant_extract'
);
CREATE INDEX IF NOT EXISTS idx_g_root_cands_stem ON g_root_candidates(stem_id);
CREATE INDEX IF NOT EXISTS idx_g_root_cands_root ON g_root_candidates(root_id);

CREATE TABLE IF NOT EXISTS g_pattern_candidates (
    id TEXT PRIMARY KEY,
    stem_id TEXT NOT NULL REFERENCES g_stems(id) ON DELETE CASCADE,
    pattern_id TEXT REFERENCES g_patterns(id) ON DELETE SET NULL,
    template_id TEXT REFERENCES g_templates(id) ON DELETE SET NULL,
    score REAL NOT NULL DEFAULT 0.5,
    rank INTEGER NOT NULL DEFAULT 1,
    method TEXT NOT NULL DEFAULT 'template_match',
    alignment_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_g_pat_cands_stem ON g_pattern_candidates(stem_id);

CREATE TABLE IF NOT EXISTS g_seg_candidates (
    id TEXT PRIMARY KEY,
    lattice_id TEXT NOT NULL REFERENCES g_morpheme_lattices(id) ON DELETE CASCADE,
    path_rank INTEGER NOT NULL DEFAULT 1,
    score REAL NOT NULL DEFAULT 0.5,
    method TEXT NOT NULL DEFAULT 'rule_based',
    segments_json TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_g_seg_cands_lattice ON g_seg_candidates(lattice_id);

-- ── F) Syntax ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_governors (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    token_id TEXT NOT NULL REFERENCES g_tokens(id) ON DELETE CASCADE,
    gov_type TEXT NOT NULL,
    strength TEXT NOT NULL DEFAULT 'strong'
);
CREATE INDEX IF NOT EXISTS idx_g_governors_run ON g_governors(run_id);

CREATE TABLE IF NOT EXISTS g_syntactic_features (
    id TEXT PRIMARY KEY,
    token_id TEXT NOT NULL REFERENCES g_tokens(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    feature_value TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'governor'
);
CREATE INDEX IF NOT EXISTS idx_g_syn_feat_token ON g_syntactic_features(token_id);

-- ── G) Semantics ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_senses (
    id TEXT PRIMARY KEY,
    lexeme_id TEXT NOT NULL REFERENCES g_lexemes(id) ON DELETE CASCADE,
    gloss TEXT NOT NULL,
    domain TEXT NOT NULL DEFAULT 'general',
    priority INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_g_senses_lexeme ON g_senses(lexeme_id);

CREATE TABLE IF NOT EXISTS g_semantic_features (
    id TEXT PRIMARY KEY,
    token_id TEXT NOT NULL REFERENCES g_tokens(id) ON DELETE CASCADE,
    dalala TEXT NOT NULL DEFAULT 'mutabaqa',
    truth TEXT NOT NULL DEFAULT 'haqiqa',
    scope TEXT NOT NULL DEFAULT 'khas',
    restriction TEXT NOT NULL DEFAULT 'mutlaq'
);
CREATE INDEX IF NOT EXISTS idx_g_sem_feat_token ON g_semantic_features(token_id);

-- ── H) Conceptual / Normative ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_concepts (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'kulli'
);
CREATE INDEX IF NOT EXISTS idx_g_concepts_run ON g_concepts(run_id);

CREATE TABLE IF NOT EXISTS g_norms (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    norm_type TEXT NOT NULL DEFAULT 'hukm'
        CHECK (norm_type IN ('wajib','mandub','mubah','makruh','haram','hukm')),
    source_scope TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_g_norms_run ON g_norms(run_id);

CREATE TABLE IF NOT EXISTS g_illas (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL DEFAULT 'illa'
        CHECK (kind IN ('illa','shart','mani')),
    pattern TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_g_illas_run ON g_illas(run_id);

-- ── Core: Evidence / Constraint / Rule / Op ───────────────────────────────────

CREATE TABLE IF NOT EXISTS g_evidences (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    source_layer TEXT NOT NULL,
    rule_id TEXT,
    feature TEXT NOT NULL,
    value TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    polarity TEXT NOT NULL DEFAULT 'supports',
    explanation TEXT NOT NULL DEFAULT '',
    target_node_type TEXT NOT NULL DEFAULT '',
    target_node_id TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_g_evidence_run ON g_evidences(run_id);
CREATE INDEX IF NOT EXISTS idx_g_evidence_target ON g_evidences(target_node_id);

CREATE TABLE IF NOT EXISTS g_constraints (
    id TEXT PRIMARY KEY,
    template_id TEXT REFERENCES g_templates(id) ON DELETE CASCADE,
    feature TEXT NOT NULL,
    required_value TEXT NOT NULL,
    penalty REAL NOT NULL DEFAULT 1.0,
    scope TEXT NOT NULL DEFAULT 'token',
    emitter_type TEXT NOT NULL DEFAULT 'template',
    emitter_id TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_g_constraints_template ON g_constraints(template_id);

CREATE TABLE IF NOT EXISTS g_rules (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    layer TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    UNIQUE(rule_id)
);

CREATE TABLE IF NOT EXISTS g_ops (
    id TEXT PRIMARY KEY,
    op_id TEXT NOT NULL,
    op_type TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    root_class_id TEXT REFERENCES g_root_classes(id) ON DELETE SET NULL,
    description TEXT NOT NULL DEFAULT '',
    UNIQUE(op_id)
);
CREATE INDEX IF NOT EXISTS idx_g_ops_type ON g_ops(op_type);

-- ── Generic Graph Edge ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS g_edges (
    id TEXT PRIMARY KEY,
    run_id TEXT,
    src_label TEXT NOT NULL,
    src_id TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    dst_label TEXT NOT NULL,
    dst_id TEXT NOT NULL,
    props_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_g_edges_run ON g_edges(run_id);
CREATE INDEX IF NOT EXISTS idx_g_edges_src ON g_edges(src_id);
CREATE INDEX IF NOT EXISTS idx_g_edges_dst ON g_edges(dst_id);
CREATE INDEX IF NOT EXISTS idx_g_edges_rel ON g_edges(rel_type);
