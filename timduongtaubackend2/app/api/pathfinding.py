from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.pathfinding import PathRequest, PathResponse
from app.service.pathfinding_service import find_path

router = APIRouter()


@router.post("/find", response_model=PathResponse)
def find_route(
    req: PathRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Nhận 2 toạ độ lat/lon từ bản đồ + priority.
    Tự động tìm ga tàu gần nhất rồi chạy Dijkstra.
    """
    try:
        return find_path(
            db=db,
            origin_lat=req.origin_lat,
            origin_lon=req.origin_lon,
            dest_lat=req.dest_lat,
            dest_lon=req.dest_lon,
            priority=req.priority,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))