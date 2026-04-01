from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.graph_manager import GraphManager
from app.schemas.route_schema import RouteRequest, RouteResponse
from app.services.astar_service import AStarService

router = APIRouter(prefix="/v1")
astar_service = AStarService()

@router.post("/route", response_model=RouteResponse)
async def get_route(request: RouteRequest):
    result = astar_service.find_route(
        start_coords=(request.start_coords.lat, request.start_coords.lon),
        end_coords=(request.end_coords.lat, request.end_coords.lon),
        priority=request.priority,
        avoid_stations=request.avoid_stations,
        avoid_connections=request.avoid_connections,
        avoid_lines=request.avoid_lines
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="No route found between the specified coordinates under the given constraints.")
        
    path, total_time, total_distance = result
    
    return RouteResponse(
        path=path,
        total_subway_time=total_time,
        total_subway_distance=total_distance
    )

@router.post("/reload-graph")
async def reload_graph(db: Session = Depends(get_db)):
    try:
        GraphManager().reload_graph(db)
        return {"status": "success", "message": "Graph data successfully reloaded from PostgreSQL."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload graph: {str(e)}")
