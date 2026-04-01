import heapq
from typing import List, Optional, Tuple, Dict
from app.core.graph_manager import GraphManager
from app.schemas.route_schema import RoutePriority
from app.core.utils import haversine

class AStarService:
    def __init__(self):
        self.graph_manager = GraphManager()

    def _heuristic(self, lat1: float, lon1: float, lat2: float, lon2: float, priority: str) -> float:
        distance_km = haversine(lat1, lon1, lat2, lon2)
        if priority == RoutePriority.DISTANCE:
            return distance_km
        else:
            # Convert to time assuming max speed 100 km/h (admissible heuristic)
            return distance_km * 3600 / 100

    def find_route(
        self,
        start_coords: tuple,
        end_coords: tuple,
        priority: RoutePriority,
        avoid_stations: List[str] = None,
        avoid_connections: List[str] = None,
        avoid_lines: List[str] = None
    ) -> Optional[Tuple[List[str], float, float]]:
        
        avoid_stations = avoid_stations or []
        avoid_connections = avoid_connections or []
        avoid_lines = avoid_lines or []
        
        # Mapping coordinates to nearest valid stations
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        
        start_stations = self.graph_manager.get_nearby_stations(start_lat, start_lon, limit=5)
        end_stations = self.graph_manager.get_nearby_stations(end_lat, end_lon, limit=5)
        
        start_st = next((st for st in start_stations if st.id not in avoid_stations), None)
        end_st = next((st for st in end_stations if st.id not in avoid_stations), None)
        
        if not start_st or not end_st:
            return None
            
        start_id = start_st.id
        end_id = end_st.id

        # Priority Queue: (f_score, count, current_station_id, current_line_id, path_so_far, total_time, total_dist, transfers)
        # count is to break tie
        counter = 0
        open_set = []
        
        # Best cost to reach (station_id, line_id)
        best_g_scores: Dict[Tuple[str, Optional[str]], float] = {}
        
        # Initial state (we don't have a line yet)
        h_score = self._heuristic(start_st.lat, start_st.lon, end_st.lat, end_st.lon, priority)
        initial_path = [start_st.name]
        heapq.heappush(open_set, (h_score, counter, start_id, None, initial_path, 0.0, 0.0, 0))
        best_g_scores[(start_id, None)] = 0.0
        
        while open_set:
            f, _, current_id, current_line, path, g_time, g_dist, transfers = heapq.heappop(open_set)
            
            # Goal check
            if current_id == end_id:
                return path, g_time, g_dist
                
            current_st = self.graph_manager.get_station(current_id)
            
            for conn in self.graph_manager.get_neighbors(current_id):
                if conn.id in avoid_connections:
                    continue
                if conn.to_station_id in avoid_stations:
                    continue
                if conn.line_id in avoid_lines:
                    continue
                    
                neighbor_st = self.graph_manager.get_station(conn.to_station_id)
                next_line = conn.line_id
                
                # Calculate transfer penalties
                is_transfer = current_line is not None and current_line != next_line
                
                # Step cost
                step_time = conn.travel_time_sec + (300.0 if is_transfer else 0.0)
                step_dist = conn.distance_km + (1.0 if is_transfer else 0.0) # 1.0 km penalty for distance priority
                
                new_g_time = g_time + step_time
                new_g_dist = g_dist + step_dist
                new_transfers = transfers + (1 if is_transfer else 0)
                
                g_cost = new_g_time if priority == RoutePriority.TIME else new_g_dist
                
                state_key = (neighbor_st.id, next_line)
                
                if state_key not in best_g_scores or g_cost < best_g_scores[state_key]:
                    best_g_scores[state_key] = g_cost
                    
                    # Compute h
                    h_cost = self._heuristic(neighbor_st.lat, neighbor_st.lon, end_st.lat, end_st.lon, priority)
                    new_f = g_cost + h_cost
                    
                    new_path = list(path)
                    # Use station_name as requested, avoiding consecutive duplicates if any
                    if not new_path or new_path[-1] != neighbor_st.name:
                        new_path.append(neighbor_st.name)
                    
                    counter += 1
                    heapq.heappush(
                        open_set, 
                        (new_f, counter, neighbor_st.id, next_line, new_path, new_g_time, new_g_dist, new_transfers)
                    )
                    
        return None  # No path found
