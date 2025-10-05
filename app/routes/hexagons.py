from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import schemas
from database.database import SessionLocal, get_db
from models.hexagon import HexagonData
from services.hexagon_ratings import calc_finaly_rating


router = APIRouter(prefix="/hexagons", tags=["hexagons"])

@router.get("/", response_model=List[schemas.Hexagon])
def read_hexagons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    hexagons = db.query(HexagonData).offset(skip).limit(limit).all()
    return hexagons

@router.get("/{hexagon_id}", response_model=schemas.Hexagon)
def read_hexagon(hexagon_id: int, db: Session = Depends(get_db)):
    hexagon = db.query(HexagonData).filter(HexagonData.hex_id == hexagon_id).first()
    if hexagon is None:
        raise HTTPException(status_code=404, detail="Hexagon data not found")
    return hexagon

@router.get("/{hexagon_id}/metrics")
def read_hexagon_metrics(
    hexagon_id: int, 
    builder_flg: bool = False,
    driver_flg: bool = False,
    uses_public_transport_flg: bool = False,
    parent_flg: bool = False,
    pet_owner_flg: bool = False,
    big_family_flg: bool = False,
    old_family_flg: bool = False,
    db: Session = Depends(get_db)
):
    # Get the hexagon data
    hexagon = db.query(HexagonData).filter(HexagonData.hex_id == hexagon_id).first()
    if hexagon is None:
        raise HTTPException(status_code=404, detail="Hexagon data not found")
    
    # Calculate rating based on provided flags
    rating = calc_finaly_rating(
        hexagon_id, 
        builder_flg, 
        driver_flg, 
        uses_public_transport_flg, 
        parent_flg, 
        pet_owner_flg, 
        big_family_flg, 
        old_family_flg,
        db
    )
    
    # Return metrics including the calculated rating
    metrics = {
        "rating": rating,
    }
    
    return metrics

@router.post("/", response_model=schemas.Hexagon)
def create_hexagon(hexagon: schemas.HexagonCreate, db: Session = Depends(get_db)):
    db_hexagon = HexagonData(**hexagon.dict())
    db.add(db_hexagon)
    db.commit()
    db.refresh(db_hexagon)
    return db_hexagon

@router.put("/{hexagon_id}", response_model=schemas.Hexagon)
def update_hexagon(hexagon_id: int, hexagon: schemas.HexagonUpdate, db: Session = Depends(get_db)):
    db_hexagon = db.query(HexagonData).filter(HexagonData.hex_id == hexagon_id).first()
    if db_hexagon is None:
        raise HTTPException(status_code=404, detail="Hexagon data not found")
    
    update_data = hexagon.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_hexagon, key, value)
    
    db.commit()
    db.refresh(db_hexagon)
    return db_hexagon

@router.patch("/{hexagon_id}", response_model=schemas.Hexagon)
def patch_hexagon(hexagon_id: int, hexagon: schemas.HexagonUpdate, db: Session = Depends(get_db)):
    db_hexagon = db.query(HexagonData).filter(HexagonData.hex_id == hexagon_id).first()
    if db_hexagon is None:
        raise HTTPException(status_code=404, detail="Hexagon data not found")
    
    update_data = hexagon.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_hexagon, key, value)
    
    db.commit()
    db.refresh(db_hexagon)
    return db_hexagon

@router.delete("/{hexagon_id}")
def delete_hexagon(hexagon_id: int, db: Session = Depends(get_db)):
    db_hexagon = db.query(HexagonData).filter(HexagonData.hex_id == hexagon_id).first()
    if db_hexagon is None:
        raise HTTPException(status_code=404, detail="Hexagon data not found")
    
    db.delete(db_hexagon)
    db.commit()
    return {"message": "Hexagon data deleted successfully"}