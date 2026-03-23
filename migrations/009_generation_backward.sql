-- Migration 009: Backward generation pipeline tables
-- Adds generation_runs and generation_branches tables used by the
-- GENERATE_BACKWARD pipeline (sections 12–14 of the Nahda spec).

CREATE TABLE IF NOT EXISTS generation_runs (
    id          VARCHAR(36)   PRIMARY KEY,
    run_id      VARCHAR(36)   NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    target_meaning TEXT        NOT NULL,
    status      VARCHAR(24)   NOT NULL DEFAULT 'completed',
    branch_count INTEGER      NOT NULL DEFAULT 0,
    top_score   FLOAT         NOT NULL DEFAULT 0.0,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_generation_runs_run_id ON generation_runs(run_id);
CREATE INDEX IF NOT EXISTS ix_generation_runs_status  ON generation_runs(status);

CREATE TABLE IF NOT EXISTS generation_branches (
    id                  VARCHAR(36) PRIMARY KEY,
    generation_run_id   VARCHAR(36) NOT NULL REFERENCES generation_runs(id) ON DELETE CASCADE,
    text                TEXT        NOT NULL,
    score               FLOAT       NOT NULL DEFAULT 0.0 CHECK (score >= 0 AND score <= 1),
    verified            BOOLEAN     NOT NULL DEFAULT FALSE,
    trace_json          JSON        NOT NULL DEFAULT '{}',
    rank                INTEGER     NOT NULL DEFAULT 1 CHECK (rank >= 1),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_generation_branches_generation_run_id ON generation_branches(generation_run_id);
CREATE INDEX IF NOT EXISTS ix_generation_branches_rank              ON generation_branches(rank);
