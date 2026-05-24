from fastapi import APIRouter

from app.api.v1.endpoints import auth, documents, rag, rbac

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(rbac.router)
api_router.include_router(documents.router)
api_router.include_router(rag.router)
