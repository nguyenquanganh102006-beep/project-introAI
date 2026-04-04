from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Priority(str, Enum):
    time      = "time"       # tối thiểu thời gian
    cost      = "cost"       # tối thiểu tiền
    transfers = "transfers"  # tối thiểu số lần đổi tàu
    distance  = "distance"   # tối thiểu khoảng cách

class PathRequest(BaseModel):
    # Người dùng chọn 2 điểm lat/lon trên bản đồ
    origin_lat:  float
    origin_lon:  float
    dest_lat:    float
    dest_lon:    float
    priority:    Priority = Priority.time

class StepOut(BaseModel):
    from_station:   str
    to_station:     str
    line_name:      str
    distance_km:    float
    time_min:       float
    fare_yen:       int
    is_transfer:    bool

class PathResponse(BaseModel):
    origin_station:      str   # ga gần điểm xuất phát nhất
    dest_station:        str   # ga gần điểm đích nhất
    steps:               List[StepOut]
    total_time_min:      float
    total_cost_yen:      int
    total_distance_km:   float
    total_transfers:     int
    priority_used:       Priority