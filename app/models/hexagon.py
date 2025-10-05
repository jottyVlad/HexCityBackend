from sqlalchemy import Column, Integer, String, Float, Text
from database.database import Base

class HexagonData(Base):
    __tablename__ = "hexagonal_data"

    hex_id = Column(String, primary_key=True, index=True, nullable=True)
    center_lon = Column(Float, nullable=True)
    center_lat = Column(Float, nullable=True)
    avg_speed = Column(Float, nullable=True)
    avg_limit = Column(Float, nullable=True)
    stop_count = Column(Integer, nullable=True)
    unique_routes_count = Column(Integer, nullable=True)
    pedestrian_roads_count = Column(Integer, nullable=True)
    dominant_coverage_type = Column(String, nullable=True)
    count_road_type_1 = Column(Integer, nullable=True)
    count_road_type_2 = Column(Integer, nullable=True)
    count_road_type_3 = Column(Integer, nullable=True)
    count_road_type_4 = Column(Integer, nullable=True)
    count_road_type_5 = Column(Integer, nullable=True)
    count_road_type_6 = Column(Integer, nullable=True)
    count_road_type_7 = Column(Integer, nullable=True)
    count_road_type_9 = Column(Integer, nullable=True)
    count_road_type_10 = Column(Integer, nullable=True)
    count_parks = Column(Integer, nullable=True)
    count_schools = Column(Integer, nullable=True)
    count_hospitals = Column(Integer, nullable=True)
    count_shops = Column(Integer, nullable=True)
    count_factories = Column(Integer, nullable=True)
    peaks_json = Column(Text, nullable=True)
    roads_list_json = Column(Text, nullable=True)
    neighbours = Column(Text, nullable=True)
