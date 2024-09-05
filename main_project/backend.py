from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, Depends, HTTPException
from jose import JWTError, jwt
from fastapi import FastAPI, Form, Depends, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

app=FastAPI()

DATABASE_URL = "sqlite:///test.db"  # SQLite file-based database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Part(Base):
    __tablename__ = 'parts'
    
    id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    currency = Column(String)
    stock_quantity = Column(Integer)
    part_parameters_id = Column(Integer, ForeignKey("part_parameters.id"), nullable=True)
    part_number = Column(String)
    manufacturer = Column(String)
    photo_path = Column(String)  # New field for storing the photo path

    part_parameters = relationship("CarParameter", back_populates="parts")

class CarParameter(Base):
    __tablename__ = 'part_parameters'
    
    id = Column(Integer, primary_key=True, index=True)
    car_name = Column(String, index=True)
    manufacturer = Column(String)
    year = Column(Integer)
    engine_type = Column(String)

    parts = relationship("Part", back_populates="part_parameters")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ADMIN_PASSWORD = "admin123"

def add_part_to_db(db: Session, name: str, description: str, price: float, currency: str, stock_quantity: int, part_parameters: int = None, photo_path: str = None):
    new_part = Part(
        part_name=name,
        description=description,
        price=price,
        currency=currency,
        stock_quantity=stock_quantity,
        part_parameters_id=part_parameters,
        photo_path=photo_path  # Assuming you add this field to the Part model
    )
    db.add(new_part)
    db.commit()


def add_part_parameters_to_db(db: Session, car_name: str, manufacturer: str, year: int, engine_type: str):
    new_part_parameter = CarParameter(
        car_name=car_name,
        manufacturer=manufacturer,
        year=year,
        engine_type=engine_type
    )
    db.add(new_part_parameter)
    db.commit()

def remove_part_from_db(db: Session, part_id: int):
    part_to_remove = db.query(Part).filter(Part.id == part_id).first()
    if part_to_remove:
        db.delete(part_to_remove)
        db.commit()


