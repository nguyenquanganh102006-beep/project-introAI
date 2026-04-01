from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.models import Station, Connection, StationDB, ConnectionDB
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
        self.adjacency_list: Dict[str, List[Connection]] = {}
        self._initialized = True

    def load_data(self, db: Session):
        """Loads or reloads the graph from PostgreSQL database."""
        self.stations.clear()
        self.adjacency_list.clear()

        # Load Stations
        for st_db in db.query(StationDB).all():
            st = Station(id=st_db.id, name=st_db.name, lat=st_db.lat, lon=st_db.lon)
            self.stations[st.id] = st
            self.adjacency_list[st.id] = []
            
        # Load Connections
        for conn_db in db.query(ConnectionDB).all():
            conn = Connection(
                id=conn_db.id,
                from_station_id=conn_db.from_station_id,
                to_station_id=conn_db.to_station_id,
                line_id=conn_db.line_id,
                distance_km=conn_db.distance_km,
                travel_time_sec=conn_db.travel_time_sec
            )
            # Only add connections if both stations exist
            if conn.from_station_id in self.stations and conn.to_station_id in self.stations:
                self.adjacency_list[conn.from_station_id].append(conn)

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

    def get_neighbors(self, station_id: str) -> List[Connection]:
        return self.adjacency_list.get(station_id, [])

    def reload_graph(self, db: Session):
        self.load_data(db)
