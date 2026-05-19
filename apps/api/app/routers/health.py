from fastapi import APIRouter
from app.db.database import check_db_connection

router = APIRouter()

@router.get("/")
def health_check():
    db_ok = check_db_connection()
    return {
        "status":   "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }