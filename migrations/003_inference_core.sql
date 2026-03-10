-- Phase 3 Inference Core schema (L9-L11)

CREATE TABLE IF NOT EXISTS speech_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  segment_id TEXT NOT NULL REFERENCES document_segments(id) ON DELETE CASCADE,
  speech_type TEXT NOT NULL,
  prev_speech_id TEXT,
  next_speech_id TEXT
);

CREATE TABLE IF NOT EXISTS inference_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  speech_id TEXT NOT NULL REFERENCES speech_units(id) ON DELETE CASCADE,
  mantuq_json TEXT NOT NULL DEFAULT '[]',
  illa_explicit_json TEXT NOT NULL DEFAULT '[]',
  illa_implied_json TEXT NOT NULL DEFAULT '[]',
  confidence_score REAL NOT NULL,
  CHECK(confidence_score >= 0 AND confidence_score <= 1)
);

CREATE TABLE IF NOT EXISTS inference_mafhum_items (
  id TEXT PRIMARY KEY,
  inference_id TEXT NOT NULL REFERENCES inference_units(id) ON DELETE CASCADE,
  mafhum_type TEXT NOT NULL,
  content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  inference_id TEXT NOT NULL REFERENCES inference_units(id) ON DELETE CASCADE,
  hukm_text TEXT NOT NULL,
  evidence_rank TEXT NOT NULL,
  tarjih_basis TEXT NOT NULL,
  confidence_score REAL NOT NULL,
  CHECK(confidence_score >= 0 AND confidence_score <= 1)
);

CREATE TABLE IF NOT EXISTS rule_conflicts (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  rule_a_id TEXT NOT NULL REFERENCES rule_units(id) ON DELETE CASCADE,
  rule_b_id TEXT NOT NULL REFERENCES rule_units(id) ON DELETE CASCADE,
  conflict_type TEXT NOT NULL DEFAULT 'opposition',
  resolved BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tarjih_decisions (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  conflict_id TEXT NOT NULL REFERENCES rule_conflicts(id) ON DELETE CASCADE,
  winning_rule_id TEXT NOT NULL REFERENCES rule_units(id) ON DELETE CASCADE,
  basis TEXT NOT NULL DEFAULT 'strength_of_evidence',
  discarded_rule_ids_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_rule_run_conf ON rule_units(run_id, confidence_score);
CREATE INDEX IF NOT EXISTS idx_conflict_run ON rule_conflicts(run_id);
CREATE INDEX IF NOT EXISTS idx_tarjih_conflict ON tarjih_decisions(conflict_id);
