from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.graph_manager import GraphManager
from app.core.config import AVERAGE_VELOCITY
from app.schemas.route_schema import RouteRequest, RouteResponse, ClosureRequest
from app.services.astar_service import AStarService, calculate_fare
from app.api.auth import authorize_admin

router = APIRouter(prefix="/v1")
astar_service = AStarService()

@router.post("/route", response_model=RouteResponse)
async def get_route(request: RouteRequest):
    result = astar_service.find_route(
        start_coords=(request.start_coords.lat, request.start_coords.lon),
        end_coords=(request.end_coords.lat, request.end_coords.lon),
        priority=request.priority
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="No route found between the specified coordinates under the given constraints.")
        
    path, total_distance, total_transfers = result
    
    total_fare = calculate_fare(total_distance, request.passenger_type)
    estimated_time = (total_distance / AVERAGE_VELOCITY) * 60.0
    
    return RouteResponse(
        path=path,
        total_subway_distance=total_distance,
        total_fare=total_fare,
        estimated_time_minutes=estimated_time
    )

@router.post("/admin/closures")
async def update_closures(request: ClosureRequest, admin: str = Depends(authorize_admin)):
    GraphManager().set_closed_nodes(
        stations=request.closed_stations,
        edges=request.closed_edges,
        lines=request.closed_lines
    )
    return {"status": "success", "message": "Graph entities updated.", "current_state": GraphManager().get_closed_nodes()}

@router.get("/admin/closures")
async def get_closures(admin: str = Depends(authorize_admin)):
    return GraphManager().get_closed_nodes()

@router.get("/network")
async def get_network():
    gm = GraphManager()
    stations = []
    for s_id, s in gm.stations.items():
        stations.append({
            "id": s_id,
            "name": s.name,
            "line_id": s.line_id,
            "lat": s.lat,
            "lon": s.lon
        })
    edges = []
    for s_id, e_list in gm.edges.items():
        for e in e_list:
            edges.append({
                "id": e.edge_id,
                "source": e.source_id,
                "target": e.target_id,
                "is_active": e.is_active
            })
    return {"stations": stations, "edges": edges}

@router.post("/reload-graph")
async def reload_graph(db: Session = Depends(get_db)):
    try:
        GraphManager().reload_graph(db)
        return {"status": "success", "message": "Graph data successfully reloaded from PostgreSQL."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload graph: {str(e)}")
