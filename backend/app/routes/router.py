from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.interview import router as interview_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(interview_router)
