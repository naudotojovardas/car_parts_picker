# DB models

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from database import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    
    cart = relationship("Cart", uselist=False, back_populates="user")  # Relationship to Cart


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
    photo_path = Column(String)

    part_parameters = relationship("CarParameter", back_populates="parts")

class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Corrected foreign key

    # Relationship to CartItem, with lazy loading of items
    items = relationship("CartItem", back_populates="cart")
    user = relationship("User", back_populates="cart")  # Relationship to User

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    quantity = Column(Integer, default=1)

    # Reverse relationship to Cart
    cart = relationship("Cart", back_populates="items")


class CarParameter(Base):
    __tablename__ = 'part_parameters'
    id = Column(Integer, primary_key=True, index=True)
    car_name = Column(String, index=True)
    manufacturer = Column(String)
    year = Column(Integer)
    engine_type = Column(String)

    parts = relationship("Part", back_populates="part_parameters")


def add_part_to_db(db: Session, name: str, description: str, price: float, currency: str, stock_quantity: int, part_parameters: int = None, photo_path: str = None):
    new_part = Part(
        part_name=name,
        description=description,
        price=price,
        currency=currency,
        stock_quantity=stock_quantity,
        part_parameters_id=part_parameters,
        photo_path=photo_path
    )
    db.add(new_part)  # Add the new part to the session.
    db.commit()  # Commit the transaction to save changes in the DB.


# 16. Add car part parameters to the `part_parameters` table in the database.
def add_part_parameters_to_db(db: Session, car_name: str, manufacturer: str, year: int, engine_type: str):
    print(f"engine type is {engine_type} 2")
    new_part_parameter = CarParameter(
        car_name=car_name,
        manufacturer=manufacturer,
        year=year,
        engine_type=engine_type
    )
    db.add(new_part_parameter)  # Add the new parameters to the session.
    db.commit()  # Commit the transaction to save the new parameters.


# 17. Remove a part from the `parts` table in the database by its ID.
def remove_part_from_db(db: Session, part_id: int):
    part_to_remove = db.query(Part).filter(Part.id == part_id).first()  # Find the part by ID.
    if part_to_remove:
        db.delete(part_to_remove)  # Mark the part for deletion.
        db.commit()  # Commit the transaction to apply the deletion.

