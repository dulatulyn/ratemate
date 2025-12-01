from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasic
from sqlalchemy.ext.asyncio import AsyncSession

from ratemate_app.db.session import get_db
from ratemate_app.services.admin import require_admin

router = APIRouter()
basic = HTTPBasic()

@router.get("/ping", dependencies=[Depends(require_admin)])
async def admin_ping(db: AsyncSession = Depends(get_db)):
    return {"success": True}



