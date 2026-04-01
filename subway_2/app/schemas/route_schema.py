from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RoutePriority(str, Enum):
    TIME = "time"
    DISTANCE = "distance"

class Coordinates(BaseModel):
    lat: float
    lon: float

class RouteRequest(BaseModel):
    start_coords: Coordinates
    end_coords: Coordinates
    priority: RoutePriority = RoutePriority.TIME
    avoid_stations: List[str] = Field(default_factory=list)
    avoid_connections: List[str] = Field(default_factory=list)
    avoid_lines: List[str] = Field(default_factory=list)

class RouteResponse(BaseModel):
    path: List[str]
    total_subway_time: float
    total_subway_distance: float
