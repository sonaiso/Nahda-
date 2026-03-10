from fastapi import APIRouter

from app.api import unicode_routes
from app.api import morphology_routes
from app.api import semantics_routes

router = APIRouter()
router.include_router(unicode_routes.router, tags=["unicode"])
router.include_router(morphology_routes.router, tags=["morphology"])
router.include_router(semantics_routes.router, tags=["semantics"])
