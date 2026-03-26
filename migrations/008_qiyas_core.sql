-- Migration 008: Qiyas (Analogical Reasoning) Core Tables
-- Adds the qiyas_units and qiyas_daal_links tables that support the
-- Qiyas pipeline (app/services/qiyas_pipeline.py).
--
-- Naming note: the canonical vocabulary uses `daal_type` (DaalType).
-- The informal aliases DaalForm and DaalFunction must not appear in
-- schema, code, or documentation — this migration enforces that contract.

CREATE TABLE IF NOT EXISTS qiyas_units (
    id                   VARCHAR(36) PRIMARY KEY,
    run_id               VARCHAR(36) NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
    -- Source case with known judgment
    asl_text             TEXT        NOT NULL DEFAULT '',
    asl_judgment         VARCHAR(128) NOT NULL DEFAULT '',
    -- Target case seeking judgment
    far_text             TEXT        NOT NULL DEFAULT '',
    -- Effective cause
    illa_description     TEXT        NOT NULL DEFAULT '',
    -- Indication type — canonical DaalType vocabulary
    daal_type            VARCHAR(32) NOT NULL DEFAULT 'mutabaqa'
        CHECK (daal_type IN ('mutabaqa','tadammun','iltizam','nass','zahir','mafhum')),
    -- Transfer outcome
    transferred_judgment VARCHAR(128) NOT NULL DEFAULT '',
    transfer_state       VARCHAR(16) NOT NULL DEFAULT 'suspend'
        CHECK (transfer_state IN ('valid','invalid','suspend')),
    rationale            TEXT        NOT NULL DEFAULT '',
    confidence_score     FLOAT       NOT NULL DEFAULT 0.5
        CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_qiyas_units_run_id       ON qiyas_units(run_id);
CREATE INDEX IF NOT EXISTS ix_qiyas_units_transfer_state ON qiyas_units(transfer_state);

CREATE TABLE IF NOT EXISTS qiyas_daal_links (
    id               VARCHAR(36)  PRIMARY KEY,
    qiyas_id         VARCHAR(36)  NOT NULL REFERENCES qiyas_units(id) ON DELETE CASCADE,
    evidence_text    TEXT         NOT NULL DEFAULT '',
    evidence_source  VARCHAR(128) NOT NULL DEFAULT 'nass',
    strength         VARCHAR(16)  NOT NULL DEFAULT 'zanni',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_qiyas_daal_links_qiyas_id ON qiyas_daal_links(qiyas_id);
