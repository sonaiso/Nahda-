from fastapi import APIRouter, Depends

from app.api import auth_routes
from app.api import unicode_routes
from app.api import morphology_routes
from app.api import semantics_routes
from app.api import infer_routes
from app.api import rule_routes
from app.api import manat_routes
from app.api import awareness_routes
from app.api import explainability_routes
from app.api import health_routes
from app.api import graph_routes
from app.api import axiomatic_routes
from app.security.auth import get_current_principal

router = APIRouter()
router.include_router(auth_routes.router, tags=["auth"])
router.include_router(
	unicode_routes.router,
	tags=["unicode"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	morphology_routes.router,
	tags=["morphology"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	semantics_routes.router,
	tags=["semantics"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	infer_routes.router,
	tags=["inference"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	rule_routes.router,
	tags=["rule"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	manat_routes.router,
	tags=["manat"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	awareness_routes.router,
	tags=["awareness"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	explainability_routes.router,
	tags=["explainability"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(health_routes.router, tags=["health"])
router.include_router(
	graph_routes.router,
	tags=["graph"],
	dependencies=[Depends(get_current_principal)],
)
router.include_router(
	axiomatic_routes.router,
	tags=["axiomatic"],
	dependencies=[Depends(get_current_principal)],
)
