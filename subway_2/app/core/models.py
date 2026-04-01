from dataclasses import dataclass
from sqlalchemy import Column, String, Float
from app.core.database import Base

@dataclass
class Station:
    id: str
    name: str
    lat: float
    lon: float

@dataclass
class Connection:
    id: str  # Added ID for connection filtering
    from_station_id: str
    to_station_id: str
    line_id: str
    distance_km: float
    travel_time_sec: float

# ==========================================
# SQLALCHEMY MODELS (Dùng cho PostgreSQL DB)
# ==========================================

class StationDB(Base):
    __tablename__ = "stations"  # Tên bảng thực tế trong db PostgreSQL của bạn

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lon = Column(Float)

class ConnectionDB(Base):
    __tablename__ = "connections"

    id = Column(String, primary_key=True, index=True)
    from_station_id = Column(String, index=True)
    to_station_id = Column(String, index=True)
    line_id = Column(String)
    distance_km = Column(Float)
    travel_time_sec = Column(Float)
