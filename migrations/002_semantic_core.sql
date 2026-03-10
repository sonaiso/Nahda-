-- Phase 2 Semantic Core schema (L5-L8)

CREATE TABLE IF NOT EXISTS lexeme_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  surface_form TEXT NOT NULL,
  pos TEXT NOT NULL,
  independence BOOLEAN NOT NULL DEFAULT 1,
  pattern_id TEXT NOT NULL REFERENCES pattern_units(id) ON DELETE CASCADE,
  lemma TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meaning_registries (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  lexeme_id TEXT NOT NULL REFERENCES lexeme_units(id) ON DELETE CASCADE,
  qareena_required BOOLEAN NOT NULL DEFAULT 1,
  notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS meaning_senses (
  id TEXT PRIMARY KEY,
  registry_id TEXT NOT NULL REFERENCES meaning_registries(id) ON DELETE CASCADE,
  sense_type TEXT NOT NULL,
  gloss TEXT NOT NULL,
  priority_rank INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS indication_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  lexeme_id TEXT NOT NULL REFERENCES lexeme_units(id) ON DELETE CASCADE,
  mutabaqa_json TEXT NOT NULL DEFAULT '[]',
  tadammun_json TEXT NOT NULL DEFAULT '[]',
  iltizam_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS relation_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  target_ref TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lexeme_run_pos ON lexeme_units(run_id, pos);
CREATE INDEX IF NOT EXISTS idx_sense_registry_type ON meaning_senses(registry_id, sense_type);
CREATE INDEX IF NOT EXISTS idx_relation_run_type ON relation_units(run_id, relation_type);
