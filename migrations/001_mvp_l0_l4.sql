-- MVP L0-L4 schema for Nahda Arabic Fractal Engine

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'ar',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_segments (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  segment_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  input_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS layer_executions (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  layer_name TEXT NOT NULL,
  success BOOLEAN NOT NULL DEFAULT 1,
  duration_ms REAL NOT NULL DEFAULT 0,
  quality_score REAL NOT NULL DEFAULT 1,
  details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS processing_errors (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  layer_name TEXT NOT NULL,
  error_code TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unicode_scalars (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  segment_id TEXT NOT NULL REFERENCES document_segments(id) ON DELETE CASCADE,
  scalar_value INTEGER NOT NULL,
  char_value TEXT NOT NULL,
  position_index INTEGER NOT NULL,
  prev_scalar_id TEXT,
  next_scalar_id TEXT,
  UNIQUE(run_id, position_index)
);

CREATE TABLE IF NOT EXISTS grapheme_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  base_scalar_id TEXT NOT NULL REFERENCES unicode_scalars(id) ON DELETE CASCADE,
  marks_json TEXT NOT NULL DEFAULT '[]',
  norm_class TEXT NOT NULL DEFAULT 'standard',
  token_index INTEGER NOT NULL,
  char_index INTEGER NOT NULL,
  normalized_char TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS phonetic_atoms (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  grapheme_id TEXT,
  atom_type TEXT NOT NULL,
  lower_features_json TEXT NOT NULL DEFAULT '{}',
  prev_atom_id TEXT,
  next_atom_id TEXT
);

CREATE TABLE IF NOT EXISTS syllable_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  pattern TEXT NOT NULL,
  text TEXT NOT NULL,
  atoms_json TEXT NOT NULL DEFAULT '[]',
  prev_syllable_id TEXT,
  next_syllable_id TEXT
);

CREATE TABLE IF NOT EXISTS pattern_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  token TEXT NOT NULL,
  root_c1 TEXT NOT NULL,
  root_c2 TEXT NOT NULL,
  root_c3 TEXT NOT NULL,
  pattern_name TEXT NOT NULL,
  class_type TEXT NOT NULL DEFAULT 'mushtaq',
  augmentations_json TEXT NOT NULL DEFAULT '[]',
  semantic_shift_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_unicode_run_pos ON unicode_scalars(run_id, position_index);
CREATE INDEX IF NOT EXISTS idx_grapheme_run_token ON grapheme_units(run_id, token_index);
CREATE INDEX IF NOT EXISTS idx_pattern_run_token ON pattern_units(run_id, token);
