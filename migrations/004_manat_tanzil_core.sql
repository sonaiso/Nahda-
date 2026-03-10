-- Phase 4 Manat & Tanzil schema (L12)

CREATE TABLE IF NOT EXISTS case_profiles (
  id TEXT PRIMARY KEY,
  external_case_id TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_features (
  id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL REFERENCES case_profiles(id) ON DELETE CASCADE,
  feature_key TEXT NOT NULL,
  feature_value TEXT NOT NULL,
  verification_state TEXT NOT NULL DEFAULT 'verified'
);

CREATE TABLE IF NOT EXISTS manat_units (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
  rule_id TEXT NOT NULL REFERENCES rule_units(id) ON DELETE CASCADE,
  case_id TEXT NOT NULL REFERENCES case_profiles(id) ON DELETE CASCADE,
  verified_features_json TEXT NOT NULL DEFAULT '[]',
  missing_features_json TEXT NOT NULL DEFAULT '[]',
  applies_state TEXT NOT NULL,
  confidence_score REAL NOT NULL,
  CHECK(applies_state IN ('true','false','suspend')),
  CHECK(confidence_score >= 0 AND confidence_score <= 1)
);

CREATE TABLE IF NOT EXISTS tanzil_decisions (
  id TEXT PRIMARY KEY,
  manat_id TEXT NOT NULL REFERENCES manat_units(id) ON DELETE CASCADE,
  final_decision TEXT NOT NULL,
  rationale TEXT NOT NULL,
  decided_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applicability_checks (
  id TEXT PRIMARY KEY,
  manat_id TEXT NOT NULL REFERENCES manat_units(id) ON DELETE CASCADE,
  check_type TEXT NOT NULL,
  passed BOOLEAN NOT NULL DEFAULT 0,
  details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_case_feature_case_key ON case_features(case_id, feature_key);
CREATE INDEX IF NOT EXISTS idx_manat_rule_case ON manat_units(rule_id, case_id);
CREATE INDEX IF NOT EXISTS idx_tanzil_manat ON tanzil_decisions(manat_id);
