import heapq
from typing import List, Optional, Tuple, Dict
from app.core.graph_manager import GraphManager
from app.schemas.route_schema import RoutePriority
from app.core.utils import haversine

def calculate_fare(distance_km: float, passenger_type: str) -> int:
    is_child = (passenger_type == "child") if isinstance(passenger_type, str) else (passenger_type.value == "child")
    if distance_km <= 6:
        return 90 if is_child else 180
    elif distance_km <= 11:
        return 110 if is_child else 210
    elif distance_km <= 19:
        return 130 if is_child else 260
    elif distance_km <= 27:
        return 150 if is_child else 300
    else:
        return 170 if is_child else 330

class AStarService:
    def __init__(self):
        self.graph_manager = GraphManager()

    def _heuristic(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return haversine(lat1, lon1, lat2, lon2)

    def find_route(
        self,
        start_coords: tuple,
        end_coords: tuple,
        priority: RoutePriority
    ) -> Optional[Tuple[List[str], float, int]]:
        
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        
        start_stations = self.graph_manager.get_nearby_stations(start_lat, start_lon, limit=5)
        end_stations = self.graph_manager.get_nearby_stations(end_lat, end_lon, limit=5)
        
        start_st = next((st for st in start_stations if st.id not in self.graph_manager.closed_stations), None)
        end_st = next((st for st in end_stations if st.id not in self.graph_manager.closed_stations), None)
        
        if not start_st or not end_st:
            return None
            
        start_id = start_st.id
        end_id = end_st.id

        counter = 0
        open_set = []
        
        best_g_scores: Dict[Tuple[str, Optional[str]], float] = {}
        
        h_score = self._heuristic(start_st.lat, start_st.lon, end_st.lat, end_st.lon)
        initial_path = [start_id]
        # Queue: (f_score, count, current_id, current_line_id, path, total_dist, transfers)
        heapq.heappush(open_set, (h_score, counter, start_id, start_st.line_id, initial_path, 0.0, 0))
        best_g_scores[(start_id, start_st.line_id)] = 0.0
        
        while open_set:
            f, _, current_id, current_line, path, g_dist, transfers = heapq.heappop(open_set)
            
            if current_id == end_id:
                return path, g_dist, transfers
                
            for edge in self.graph_manager.get_neighbors(current_id):
                # Skip inactive edges
                if not edge.is_active:
                    continue
                # Skip edges closed by Admin
                if edge.id in self.graph_manager.closed_edges:
                    continue
                # Skip edges leading to closed stations
                if edge.target_id in self.graph_manager.closed_stations:
                    continue
                    
                neighbor_st = self.graph_manager.get_station(edge.target_id)
                if not neighbor_st:
                    continue

                # Determine the line of the neighbor station
                next_line = neighbor_st.line_id
                
                # Skip edges leading to closed lines
                if next_line in self.graph_manager.closed_lines:
                    continue

                # Transfer detection: use edge's is_transfer flag or line change
                is_transfer = edge.is_transfer or (current_line is not None and current_line != next_line)
                
                step_dist = edge.distance_km
                new_g_dist = g_dist + step_dist
                new_transfers = transfers + (1 if is_transfer else 0)
                
                # Dynamic cost calculation
                if priority == RoutePriority.FEWEST_TRANSFERS:
                    g_cost = new_g_dist + new_transfers * 5.0
                else:
                    g_cost = new_g_dist
                
                state_key = (neighbor_st.id, next_line)
                
                if state_key not in best_g_scores or g_cost < best_g_scores[state_key]:
                    best_g_scores[state_key] = g_cost
                    
                    h_cost = self._heuristic(neighbor_st.lat, neighbor_st.lon, end_st.lat, end_st.lon)
                    new_f = g_cost + h_cost
                    
                    new_path = list(path)
                    if not new_path or new_path[-1] != neighbor_st.id:
                        new_path.append(neighbor_st.id)
                    
                    counter += 1
                    heapq.heappush(
                        open_set, 
                        (new_f, counter, neighbor_st.id, next_line, new_path, new_g_dist, new_transfers)
                    )
                    
        return None  # No path found

