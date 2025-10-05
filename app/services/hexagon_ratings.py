import random
from collections import defaultdict
import math
from operator import index
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends
from database.database import get_db
from sqlalchemy.orm import Session
from models.hexagon import HexagonData
import json


def get_neighbors(idx, db):
    hexagon = db.query(HexagonData).filter(HexagonData.hex_id == idx).first()
    neigbors = json.loads(hexagon.neighbours)
    return neigbors

class Places(Enum):
    ROAD_TYPE_1 = 0 # фед трасса
    ROAD_TYPE_2 = 1 # междугородная
    ROAD_TYPE_3 = 2 # Магистральная
    ROAD_TYPE_4 = 3 # Основные улицы
    ROAD_TYPE_5 = 4 # Маленькие улицы
    ROAD_TYPE_6 = 5
    ROAD_TYPE_7 = 6
    ROAD_TYPE_8 = 7
    ROAD_TYPE_9 = 8
    AVG_SPEED = 9
    AVG_LIMIT = 10
    UNQ_ROUTES = 11
    STOP_COUNT = 12
    PED_ROAD_COUNT = 13
    DOM_COV_TYPE_IS_ASH = 14
    PARK = 15
    SCHOOL = 16
    FACTORIES = 17
    HOSPITAL = 18
    SHOP = 19

default2 = [0.0]*20
neighbor_effect = default2.copy()
neighbor_effect[Places.ROAD_TYPE_1.value] = 0.6
neighbor_effect[Places.ROAD_TYPE_2.value] = 0.6
neighbor_effect[Places.ROAD_TYPE_3.value] = 0.6
neighbor_effect[Places.ROAD_TYPE_4.value] = 0.3
neighbor_effect[Places.ROAD_TYPE_5.value] = 0
neighbor_effect[Places.ROAD_TYPE_6.value] = 0
neighbor_effect[Places.ROAD_TYPE_7.value] = 0
neighbor_effect[Places.ROAD_TYPE_8.value] = 0
neighbor_effect[Places.ROAD_TYPE_9.value] = 0
neighbor_effect[Places.AVG_SPEED.value] = 0
neighbor_effect[Places.AVG_LIMIT.value] = 0
neighbor_effect[Places.UNQ_ROUTES.value] = 0.5
neighbor_effect[Places.STOP_COUNT.value] = 0.5
neighbor_effect[Places.PED_ROAD_COUNT.value] = 0.4
neighbor_effect[Places.DOM_COV_TYPE_IS_ASH.value] = 0
neighbor_effect[Places.PARK.value] = 0.6
neighbor_effect[Places.SCHOOL.value] = 0.5
neighbor_effect[Places.FACTORIES.value] = 0.8
neighbor_effect[Places.HOSPITAL.value] = 0.8
neighbor_effect[Places.SHOP.value] = 0.4

def calc_rating(idx, builder_flg, driver_flg, 
                uses_public_transport_flg, parent_flg, 
                pet_owner_flg, big_family_flg, old_family_flg,
                db: Session):

    hexagon = db.query(HexagonData).filter(HexagonData.hex_id == idx).first()
    
    values = [0] * 20
    values[Places.ROAD_TYPE_1.value] = hexagon.count_road_type_1
    values[Places.ROAD_TYPE_2.value] = hexagon.count_road_type_2
    values[Places.ROAD_TYPE_3.value] = hexagon.count_road_type_3
    values[Places.ROAD_TYPE_4.value] = hexagon.count_road_type_4
    values[Places.ROAD_TYPE_5.value] = hexagon.count_road_type_5
    values[Places.ROAD_TYPE_6.value] = hexagon.count_road_type_6
    values[Places.ROAD_TYPE_7.value] = hexagon.count_road_type_7
    values[Places.ROAD_TYPE_8.value] = 0
    values[Places.ROAD_TYPE_9.value] = hexagon.count_road_type_9

    values[Places.AVG_SPEED.value] = hexagon.avg_speed
    values[Places.AVG_LIMIT.value] = hexagon.avg_limit
    values[Places.STOP_COUNT.value] = hexagon.stop_count
    values[Places.UNQ_ROUTES.value] = hexagon.unique_routes_count
    values[Places.PED_ROAD_COUNT.value] = hexagon.pedestrian_roads_count
    values[Places.DOM_COV_TYPE_IS_ASH.value] = hexagon.dominant_coverage_type == "Асфальт"
    values[Places.PARK.value] = hexagon.count_parks
    values[Places.SCHOOL.value] = hexagon.count_schools
    values[Places.HOSPITAL.value] = hexagon.count_hospitals
    values[Places.SHOP.value] = hexagon.count_shops
    values[Places.FACTORIES.value] = hexagon.count_factories
    
    default = [0]*20

    default[Places.FACTORIES.value]= -15
    default[Places.ROAD_TYPE_1.value]= -15
    default[Places.ROAD_TYPE_2.value]= -10
    default[Places.ROAD_TYPE_3.value]= -5


    builder = default.copy()
    builder[Places.ROAD_TYPE_4.value]= 10
    builder[Places.ROAD_TYPE_5.value]= 10
    builder[Places.ROAD_TYPE_6.value]= 10
    builder[Places.ROAD_TYPE_7.value]= 10
    builder[Places.ROAD_TYPE_8.value]= 0
    builder[Places.ROAD_TYPE_9.value]= 10
    builder[Places.UNQ_ROUTES.value]= 15
    builder[Places.STOP_COUNT.value]= 15
    builder[Places.PED_ROAD_COUNT.value]= 5
    builder[Places.SHOP.value]= 20
    builder[Places.HOSPITAL.value]= 20
    builder[Places.SCHOOL.value]= 20


    driver= default.copy()
    driver[Places.ROAD_TYPE_1.value]= -9
    driver[Places.ROAD_TYPE_2.value]= -6
    driver[Places.ROAD_TYPE_3.value]= -3
    driver[Places.ROAD_TYPE_4.value]= 15
    driver[Places.ROAD_TYPE_5.value]= 10
    driver[Places.ROAD_TYPE_6.value]= 5
    driver[Places.ROAD_TYPE_7.value]= 1
    driver[Places.AVG_SPEED.value] = 2
    driver[Places.AVG_SPEED.value] = 5
    driver[Places.UNQ_ROUTES.value]= 1
    driver[Places.STOP_COUNT.value]= 1
    driver[Places.PED_ROAD_COUNT.value]= 3
    driver[Places.SHOP.value]= 5
    driver[Places.HOSPITAL.value]= 8
    driver[Places.DOM_COV_TYPE_IS_ASH.value]=20


    walker = default.copy()
    walker[Places.ROAD_TYPE_1.value]= -20
    walker[Places.ROAD_TYPE_2.value]= -15
    walker[Places.ROAD_TYPE_3.value]= -10
    walker[Places.ROAD_TYPE_4.value]= 5
    walker[Places.ROAD_TYPE_5.value]= 5
    walker[Places.ROAD_TYPE_6.value]= 5
    walker[Places.ROAD_TYPE_7.value]= 1
    walker[Places.ROAD_TYPE_8.value]= 0
    walker[Places.ROAD_TYPE_9.value]= 10
    walker[Places.PARK.value]=20
    walker[Places.PED_ROAD_COUNT.value]= 40
    walker[Places.SHOP.value]= 25
    walker[Places.HOSPITAL.value]= 25


    uses_public_transport = default.copy()
    uses_public_transport[Places.STOP_COUNT.value] = 20
    uses_public_transport[Places.UNQ_ROUTES.value] = 30


    parent = default.copy()
    parent[Places.UNQ_ROUTES.value]= 15
    parent[Places.STOP_COUNT.value]= 15
    parent[Places.PED_ROAD_COUNT.value]= 10
    parent[Places.PARK.value]=25
    parent[Places.SHOP.value]= 25
    parent[Places.HOSPITAL.value]= 25
    parent[Places.SCHOOL.value]= 25
    parent[Places.FACTORIES.value]= -20


    pet_owner = default.copy()
    pet_owner[Places.UNQ_ROUTES.value]= 15
    pet_owner[Places.STOP_COUNT.value]= 15
    pet_owner[Places.PED_ROAD_COUNT.value]= 10
    pet_owner[Places.SHOP.value]= 25
    pet_owner[Places.PARK.value]=30
    pet_owner[Places.HOSPITAL.value]= 25


    big_family = default.copy()
    big_family[Places.SHOP.value]=35
    big_family[Places.PARK.value]=30
    big_family[Places.HOSPITAL.value]= 25



    old_family = default.copy()
    old_family[Places.PARK.value]=35
    old_family[Places.HOSPITAL.value]= 45
    old_family[Places.FACTORIES.value]= -25

    if builder_flg:
        rati = builder.copy()
    else:
        if driver_flg:
            rati=driver.copy()
        else:
            rati=walker.copy()

        if uses_public_transport_flg:

            for i in range(len(uses_public_transport)):
                if rati[i]>=0:
                    rati[i]=max(uses_public_transport[i],rati[i])
                else:
                    rati[i] = min(uses_public_transport[i], rati[i])

        if parent_flg:

            for i in range(len(parent)):
                if rati[i]>=0:
                    rati[i]=max(parent[i],rati[i])
                else:
                    rati[i] = min(parent[i], rati[i])

        if pet_owner_flg:

            for i in range(len(pet_owner)):
                if rati[i] >= 0:
                    rati[i] = max(pet_owner[i], rati[i])
                else:
                    rati[i] = min(pet_owner[i], rati[i])

        if big_family_flg:

            for i in range(len(big_family)):
                if rati[i] >= 0:
                    rati[i] = max(big_family[i], rati[i])
                else:
                    rati[i] = min(big_family[i], rati[i])

        if old_family_flg:

            for i in range(len(old_family)):
                if rati[i] >= 0:
                    rati[i] = max(old_family[i], rati[i])
                else:
                    rati[i] = min(old_family[i], rati[i])
            
    rating = 0                
    for i in range(len(values)):
        rating += values[i]*rati[i]    

    return rating, values, rati

def calc_finaly_rating(idx, builder_flg, driver_flg, 
                        uses_public_transport_flg, parent_flg, 
                        pet_owner_flg, big_family_flg, old_family_flg,
                        db: Session):

    neighbors = get_neighbors(idx, db)
    hexagon = db.query(HexagonData).filter(HexagonData.hex_id == idx).first()

    rating, values, rati = calc_rating(idx, builder_flg,driver_flg,
                                uses_public_transport_flg,parent_flg,
                                pet_owner_flg,big_family_flg,old_family_flg, db)

    for neig in neighbors:
        neig_rate, neig_values, neig_rati = calc_rating(neig, builder_flg, driver_flg,
                                                uses_public_transport_flg, parent_flg,
                                                pet_owner_flg, big_family_flg, old_family_flg,
                                                db)
        for i in range(len(values)):
            rating += neighbor_effect[i]*neig_values[i]*neig_rati[i]

    return rating
