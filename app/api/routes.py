from fastapi import APIRouter

from app.api import unicode_routes
from app.api import morphology_routes
from app.api import semantics_routes
from app.api import infer_routes
from app.api import rule_routes
from app.api import manat_routes

router = APIRouter()
router.include_router(unicode_routes.router, tags=["unicode"])
router.include_router(morphology_routes.router, tags=["morphology"])
router.include_router(semantics_routes.router, tags=["semantics"])
router.include_router(infer_routes.router, tags=["inference"])
router.include_router(rule_routes.router, tags=["rule"])
router.include_router(manat_routes.router, tags=["manat"])
