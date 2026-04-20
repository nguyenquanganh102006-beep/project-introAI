from dataclasses import dataclass
from sqlalchemy import Column, String, Float, Integer, Boolean
from app.core.database import Base

@dataclass
class Station:
    id: str
    name: str
    line_id: str
    lat: float
    lon: float

@dataclass
class Edge:
    id: int
    source_id: str
    target_id: str
    distance_km: float
    is_transfer: bool
    is_active: bool

# ==========================================
# SQLALCHEMY MODELS (Dùng cho PostgreSQL DB)
# ==========================================

class StationDB(Base):
    __tablename__ = "stations"

    station_id = Column(String, primary_key=True, index=True)
    station_name = Column(String, index=True)
    line_id = Column(String)
    lat = Column(Float)
    lon = Column(Float)

class EdgeDB(Base):
    __tablename__ = "edges"

    edge_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_id = Column(String, index=True)
    target_id = Column(String, index=True)
    distance_km = Column(Float)
    is_transfer = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

class LineDB(Base):
    __tablename__ = "line"

    line_id = Column(String, primary_key=True, index=True)
    line_name = Column(String)
    color = Column(String)

