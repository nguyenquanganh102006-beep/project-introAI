from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.models import Station, Edge, StationDB, EdgeDB
from app.core.utils import haversine

class GraphManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GraphManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.stations: Dict[str, Station] = {}
        self.adjacency_list: Dict[str, List[Edge]] = {}
        self.closed_stations = set()
        self.closed_edges = set()
        self.closed_lines = set()
        self._initialized = True

    def load_data(self, db: Session):
        """Loads or reloads the graph from PostgreSQL database."""
        self.stations.clear()
        self.adjacency_list.clear()

        # Load Stations
        for st_db in db.query(StationDB).all():
            st = Station(
                id=st_db.station_id,
                name=st_db.station_name,
                line_id=st_db.line_id,
                lat=st_db.lat,
                lon=st_db.lon
            )
            self.stations[st.id] = st
            self.adjacency_list[st.id] = []
            
        # Load Edges
        for edge_db in db.query(EdgeDB).all():
            edge = Edge(
                id=edge_db.edge_id,
                source_id=edge_db.source_id,
                target_id=edge_db.target_id,
                distance_km=edge_db.distance_km,
                is_transfer=edge_db.is_transfer,
                is_active=edge_db.is_active
            )
            # Only add edges if both stations exist
            if edge.source_id in self.stations and edge.target_id in self.stations:
                self.adjacency_list[edge.source_id].append(edge)

    def get_station(self, station_id: str) -> Optional[Station]:
        return self.stations.get(station_id)

    def get_closest_station(self, lat: float, lon: float) -> Optional[Station]:
        if not self.stations:
            return None
            
        closest_station = None
        min_distance = float('inf')
        
        for st in self.stations.values():
            dist = haversine(lat, lon, st.lat, st.lon)
            if dist < min_distance:
                min_distance = dist
                closest_station = st
                
        return closest_station

    def get_nearby_stations(self, lat: float, lon: float, limit: int = 5) -> List[Station]:
        if not self.stations:
            return []
            
        stations_with_dist = []
        for st in self.stations.values():
            dist = haversine(lat, lon, st.lat, st.lon)
            stations_with_dist.append((dist, st))
            
        stations_with_dist.sort(key=lambda x: x[0])
        return [st for dist, st in stations_with_dist[:limit]]

    def get_neighbors(self, station_id: str) -> List[Edge]:
        return self.adjacency_list.get(station_id, [])

    def set_closed_nodes(self, stations: List[str] = None, edges: List[int] = None, lines: List[str] = None):
        if stations is not None:
            self.closed_stations = set(stations)
        if edges is not None:
            self.closed_edges = set(edges)
        if lines is not None:
            self.closed_lines = set(lines)
            
    def get_closed_nodes(self):
        return {
            "closed_stations": list(self.closed_stations),
            "closed_edges": list(self.closed_edges),
            "closed_lines": list(self.closed_lines)
        }

    def reload_graph(self, db: Session):
        self.load_data(db)
