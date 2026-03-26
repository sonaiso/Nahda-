"""
Graph Schema API routes.

GET  /graph/schema    – return the full Graph Schema definition (JSON, Neo4j-compatible)
GET  /graph/templates – return all standard Arabic templates + Ops + RootClasses
POST /graph/analyze   – analyse Arabic text and return the built graph
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.tracing import start_span
from app.db.session import get_db
from app.graph.schema import export_schema
from app.graph.service import run_graph_analysis
from app.graph.templates import get_ops, get_root_classes, get_templates
from app.schemas.graph import (
    GraphAnalyzeRequest,
    GraphAnalyzeResponse,
    GraphAnalysisMetrics,
    GraphSchemaResponse,
    GraphTemplatesResponse,
    GraphTokenOut,
    EvidenceOut,
    RootCandidateOut,
    PatternCandidateOut,
    SegCandidateOut,
)

router = APIRouter()


@router.get("/graph/schema", response_model=GraphSchemaResponse)
def get_graph_schema() -> GraphSchemaResponse:
    """Return the complete Graph Schema definition (Neo4j-compatible)."""
    with start_span("graph.schema", {"nahda.layer": "graph"}):
        data = export_schema()
    return GraphSchemaResponse(**data)


@router.get("/graph/templates", response_model=GraphTemplatesResponse)
def get_graph_templates() -> GraphTemplatesResponse:
    """Return all standard Arabic morphological templates, Ops and RootClasses."""
    with start_span("graph.templates", {"nahda.layer": "graph"}):
        templates = get_templates()
        ops = get_ops()
        root_classes = get_root_classes()
    return GraphTemplatesResponse(
        template_count=len(templates),
        op_count=len(ops),
        root_class_count=len(root_classes),
        templates=templates,  # type: ignore[arg-type]
        ops=ops,  # type: ignore[arg-type]
        root_classes=root_classes,  # type: ignore[arg-type]
    )


@router.post("/graph/analyze", response_model=GraphAnalyzeResponse)
def graph_analyze(
    payload: GraphAnalyzeRequest,
    db: Session = Depends(get_db),
) -> GraphAnalyzeResponse:
    """Analyse Arabic text and return the constructed graph (candidates + evidence)."""
    with start_span("graph.analyze", {"nahda.layer": "graph"}):
        result = run_graph_analysis(db=db, text=payload.text)

    token_outs: list[GraphTokenOut] = []
    total_evidence = 0
    total_root_cands = 0
    total_pat_cands = 0

    for tok in result.tokens:
        evidence_outs = [
            EvidenceOut(
                ev_id=ev["ev_id"],
                source_layer=ev["source_layer"],
                rule_id=ev.get("rule_id", ""),
                feature=ev["feature"],
                value=ev["value"],
                weight=ev["weight"],
                polarity=ev["polarity"],
                explanation=ev["explanation"],
            )
            for ev in tok.evidence
        ]
        root_outs = [
            RootCandidateOut(
                root=rc["root"],
                score=rc["score"],
                rank=rc["rank"],
                method=rc["method"],
            )
            for rc in tok.root_candidates
        ]
        pat_outs = [
            PatternCandidateOut(
                template_id=pc["template_id"],
                pattern=pc["pattern"],
                derivation_type=pc["derivation_type"],
                score=pc["score"],
                rank=pc["rank"],
                method=pc["method"],
            )
            for pc in tok.pattern_candidates
        ]
        seg = tok.seg_candidate
        seg_out = SegCandidateOut(
            seg_id=seg["seg_id"],
            path_rank=seg["path_rank"],
            score=seg["score"],
            method=seg["method"],
            segments=seg["segments"],
        )

        total_evidence += len(evidence_outs)
        total_root_cands += len(root_outs)
        total_pat_cands += len(pat_outs)

        token_outs.append(
            GraphTokenOut(
                token_id=tok.token_id,
                surface=tok.surface,
                norm=tok.norm,
                tok_index=tok.tok_index,
                stem_surface=tok.stem_surface,
                augmentations=tok.augmentations,
                root_candidates=root_outs,
                pattern_candidates=pat_outs,
                seg_candidate=seg_out,
                evidence=evidence_outs,
            )
        )

    return GraphAnalyzeResponse(
        run_id=result.run_id,
        normalized_text=result.normalized_text,
        tokens=token_outs,
        metrics=GraphAnalysisMetrics(
            token_count=result.token_count,
            triliteral_ratio=result.triliteral_ratio,
            evidence_count=total_evidence,
            root_candidate_count=total_root_cands,
            pattern_candidate_count=total_pat_cands,
        ),
    )
