from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from db_models import User, Part, CarParameter, Cart, CartItem
from database import get_db
from auth import get_current_user


app = FastAPI()





def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 1) -> Cart:
    cart = get_or_create_cart(db, user_id)
    cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.add(cart_item)
    db.commit()
    return cart

@app.post("/cart/update/{item_id}")
async def update_cart_item(item_id: int, quantity: int = Form(...), db: Session = Depends(get_db), user_id: int = Depends(get_current_user)) -> RedirectResponse:
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart.user_id == user_id).first()
    if cart_item:
        cart_item.quantity = quantity
        db.commit()
    return RedirectResponse(url="/cart", status_code=303)

@app.post("/cart/remove/{item_id}")
async def remove_cart_item(item_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)) -> RedirectResponse:
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart.user_id == user_id).first()
    if cart_item:
        db.delete(cart_item)
        db.commit()
    return RedirectResponse(url="/cart", status_code=303)

def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def add_part_to_db(db: Session, name: str, description: str, price: float, currency: str, stock_quantity: int, part_parameters: int = None, photo_path: str = None) -> None:
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


# Add car part parameters to the `part_parameters` table in the database.
def add_part_parameters_to_db(db: Session, car_name: str, manufacturer: str, year: int, engine_type: str) -> None:
    print(f"engine type is {engine_type} 2")
    new_part_parameter = CarParameter(
        car_name=car_name,
        manufacturer=manufacturer,
        year=year,
        engine_type=engine_type
    )
    db.add(new_part_parameter)  # Add the new parameters to the session.
    db.commit()
    db.refresh(new_part_parameter)  # Commit the transaction to save the new parameters.


# Remove a part from the `parts` table in the database by its ID.
def remove_part_from_db(db: Session, part_id: int) -> None:
    part_to_remove = db.query(Part).filter(Part.id == part_id).first()  # Find the part by ID.
    if part_to_remove:
        db.delete(part_to_remove)  # Mark the part for deletion.
        db.commit()  # Commit the transaction to apply the deletion.

