from pydantic import BaseModel
from typing import Optional

class HexagonDataBase(BaseModel):
    center_lon: Optional[float] = None
    center_lat: Optional[float] = None
    avg_speed: Optional[float] = None
    avg_limit: Optional[float] = None
    stop_count: Optional[int] = None
    unique_routes_count: Optional[int] = None
    pedestrian_roads_count: Optional[int] = None
    dominant_coverage_type: Optional[str] = None
    count_road_type_1: Optional[int] = None
    count_road_type_2: Optional[int] = None
    count_road_type_3: Optional[int] = None
    count_road_type_4: Optional[int] = None
    count_road_type_5: Optional[int] = None
    count_road_type_6: Optional[int] = None
    count_road_type_7: Optional[int] = None
    count_road_type_9: Optional[int] = None
    count_road_type_10: Optional[int] = None
    count_parks: Optional[int] = None
    count_schools: Optional[int] = None
    count_hospitals: Optional[int] = None
    count_shops: Optional[int] = None
    count_factories: Optional[int] = None
    peaks_json: Optional[str] = None
    roads_list_json: Optional[str] = None
    neighbours: Optional[str] = None

class HexagonCreate(HexagonDataBase):
    pass

class HexagonUpdate(HexagonDataBase):
    pass

class HexagonInDBBase(HexagonDataBase):
    class Config:
        orm_mode = True

class Hexagon(HexagonInDBBase):
    pass