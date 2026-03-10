-- 006_awareness_layer.sql

CREATE TABLE IF NOT EXISTS concept_units (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    concept_key TEXT NOT NULL,
    summary TEXT NOT NULL,
    confidence_score REAL NOT NULL DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_concept_units_run_id ON concept_units(run_id);

CREATE TABLE IF NOT EXISTS scale_assessments (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    scale_name TEXT NOT NULL DEFAULT 'sharia_value',
    value_score REAL NOT NULL DEFAULT 0.5 CHECK (value_score >= 0 AND value_score <= 1),
    rationale TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_scale_assessments_run_id ON scale_assessments(run_id);

CREATE TABLE IF NOT EXISTS spirit_signals (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    alignment_score REAL NOT NULL DEFAULT 0.5 CHECK (alignment_score >= 0 AND alignment_score <= 1),
    remembrance_level TEXT NOT NULL DEFAULT 'moderate',
    rationale TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_spirit_signals_run_id ON spirit_signals(run_id);

CREATE TABLE IF NOT EXISTS inclination_profiles (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    tendency TEXT NOT NULL DEFAULT 'suspend',
    intensity_score REAL NOT NULL DEFAULT 0.5 CHECK (intensity_score >= 0 AND intensity_score <= 1),
    rationale TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_inclination_profiles_run_id ON inclination_profiles(run_id);

CREATE TABLE IF NOT EXISTS will_decisions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    action TEXT NOT NULL DEFAULT 'suspend' CHECK (action IN ('do', 'avoid', 'suspend')),
    rationale TEXT NOT NULL,
    confidence_score REAL NOT NULL DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_will_decisions_run_id ON will_decisions(run_id);
