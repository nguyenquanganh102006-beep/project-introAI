import heapq
import math
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session

from app.models.subway import Station, Edge, Line
from app.schemas.pathfinding import Priority, StepOut, PathResponse


# ─────────────────────────────────────────────
# 1. Tìm ga gần nhất với toạ độ lat/lon
# ─────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Khoảng cách (km) giữa 2 toạ độ theo công thức Haversine."""
    R = 6371
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def find_nearest_station(db: Session, lat: float, lon: float) -> Optional[Station]:
    """Trả về ga còn hoạt động gần toạ độ nhất."""
    stations = db.query(Station).filter(Station.is_active == True).all()
    if not stations:
        return None
    return min(stations, key=lambda s: _haversine(lat, lon, s.lat, s.lon))


# ─────────────────────────────────────────────
# 2. Xây đồ thị từ DB (chỉ cạnh còn active)
# ─────────────────────────────────────────────
def _build_graph(db: Session, priority: Priority) -> Dict[str, List[Tuple]]:
    """
    graph[node] = [(weight, neighbor, edge_obj), ...]
    weight tuỳ theo priority.
    """
    edges = (
        db.query(Edge)
        .filter(Edge.is_active == True)
        .all()
    )

    # Loại bỏ các cạnh có ga bị ban
    active_station_ids = {
        s.station_id
        for s in db.query(Station).filter(Station.is_active == True).all()
    }

    graph: Dict[str, List] = {}

    for e in edges:
        if e.source_id not in active_station_ids:
            continue
        if e.target_id not in active_station_ids:
            continue

        if priority == Priority.time:
            w = e.time_min
        elif priority == Priority.cost:
            w = e.fare_yen
        elif priority == Priority.distance:
            w = e.distance_km
        else:  # transfers — đổi tàu tính thêm penalty cao
            w = 1 + (1000 if e.is_transfer else 0)

        graph.setdefault(e.source_id, []).append((w, e.target_id, e))
        graph.setdefault(e.target_id, []).append((w, e.source_id, e))  # đồ thị vô hướng

    return graph


# ─────────────────────────────────────────────
# 3. Dijkstra
# ─────────────────────────────────────────────
def _dijkstra(graph: Dict, start: str, end: str):
    """
    Trả về (dist, prev_edge) để reconstruct path.
    dist[node] = chi phí nhỏ nhất từ start đến node.
    prev_edge[node] = (parent_node, edge_obj) để truy ngược.
    """
    dist: Dict[str, float] = {start: 0}
    prev_edge: Dict[str, Optional[Tuple]] = {start: None}
    heap = [(0, start)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float("inf")):
            continue
        if u == end:
            break
        for w, v, edge in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev_edge[v] = (u, edge)
                heapq.heappush(heap, (nd, v))

    return dist, prev_edge


def _reconstruct_path(prev_edge: Dict, end: str) -> List[Edge]:
    """Truy ngược từ end về start, trả về list Edge theo thứ tự đi."""
    path = []
    node = end
    while prev_edge.get(node) is not None:
        parent, edge = prev_edge[node]
        if parent != node:
            path.append((parent, node, edge))
        node = parent
    path.reverse()
    return path


# ─────────────────────────────────────────────
# 4. Main service function
# ─────────────────────────────────────────────
def find_path(
    db: Session,
    origin_lat: float, origin_lon: float,
    dest_lat:   float, dest_lon:   float,
    priority:   Priority,
) -> PathResponse:
    # Tìm ga gần nhất
    origin_station = find_nearest_station(db, origin_lat, origin_lon)
    dest_station   = find_nearest_station(db, dest_lat,   dest_lon)

    if origin_station is None or dest_station is None:
        raise ValueError("Không tìm thấy ga nào còn hoạt động")

    if origin_station.station_id == dest_station.station_id:
        raise ValueError("Điểm xuất phát và điểm đích cùng một ga")

    # Xây đồ thị & chạy Dijkstra
    graph = _build_graph(db, priority)
    dist, prev_edge = _dijkstra(graph, origin_station.station_id, dest_station.station_id)

    if dest_station.station_id not in dist:
        raise ValueError("Không tìm được đường đi (có thể do các ga/đoạn đường bị cấm)")

    path_edges = _reconstruct_path(prev_edge, dest_station.station_id)

    # Lấy map line_id -> Line để lấy tên tuyến
    line_map = {l.line_id: l for l in db.query(Line).all()}
    station_map = {s.station_id: s for s in db.query(Station).all()}

    steps: List[StepOut] = []
    total_time = total_cost = total_distance = total_transfers = 0

    for (src_id, tgt_id, edge) in path_edges:
        src_station = station_map.get(src_id)
        tgt_station = station_map.get(tgt_id)
        if src_station.station_name == tgt_station.station_name:
            continue
        
        if src_id != tgt_id:
            line = line_map.get(src_station.line_id, None) if src_station else None
            steps.append(StepOut(
                from_station = src_station.station_name if src_station else src_id,
                to_station   = tgt_station.station_name if tgt_station else tgt_id,
                line_name    = line.line_name if line else "Unknown",
                ###
                from_lat     = src_station.lat if src_station else 0.0,
                from_lon     = src_station.lon if src_station else 0.0,
                to_lat       = tgt_station.lat if tgt_station else 0.0,
                to_lon       = tgt_station.lon if tgt_station else 0.0,
                
                distance_km  = edge.distance_km or 0,
                time_min     = edge.time_min    or 0,
                fare_yen     = edge.fare_yen    or 0,
                is_transfer  = edge.is_transfer or False,
            ))

        total_time     += edge.time_min     or 0
        total_cost     += edge.fare_yen     or 0
        total_distance += edge.distance_km  or 0
        if edge.is_transfer:
            total_transfers += 1

    return PathResponse(
        origin_station    = origin_station.station_name,
        dest_station      = dest_station.station_name,
        steps             = steps,
        total_time_min    = round(total_time, 2),
        total_cost_yen    = total_cost,
        total_distance_km = round(total_distance, 3),
        total_transfers   = total_transfers,
        priority_used     = priority,
    )