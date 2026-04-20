from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RoutePriority(str, Enum):
    SHORTEST_DISTANCE = "shortest_distance"
    LOWEST_FARE = "lowest_fare"
    FEWEST_TRANSFERS = "fewest_transfers"

class PassengerType(str, Enum):
    ADULT = "adult"
    CHILD = "child"

class Coordinates(BaseModel):
    lat: float
    lon: float

class RouteRequest(BaseModel):
    start_coords: Coordinates
    end_coords: Coordinates
    priority: RoutePriority = RoutePriority.SHORTEST_DISTANCE
    passenger_type: PassengerType = PassengerType.ADULT

class RouteResponse(BaseModel):
    path: List[str]
    total_subway_distance: float
    total_fare: int
    estimated_time_minutes: float

class ClosureRequest(BaseModel):
    closed_stations: Optional[List[str]] = None
    closed_edges: Optional[List[int]] = None
    closed_lines: Optional[List[str]] = None
