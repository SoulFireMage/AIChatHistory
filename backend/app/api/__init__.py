from fastapi import APIRouter
from . import providers, api_keys, projects, conversations, import_jobs

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(import_jobs.router, prefix="/import-jobs", tags=["import-jobs"])
