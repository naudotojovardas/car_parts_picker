from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import timedelta, datetime
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from db_models import User, Cart, CartItem, Part, CarParameter
from database import get_db
from typing import Optional
from fastapi.responses import RedirectResponse
# CORS Middleware to allow frontend communication
app = FastAPI()




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


ADMIN_PASSWORD = "admin123"

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        print(f"User with username {username} not found.")
        return False
    
    if not verify_password(password, user.hashed_password):
        print(f"Password for {username} does not match.")
        return False
    
    return user

def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return token


def get_current_user(token: str = Depends(get_token_from_cookie), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    print("0")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print("1")
            raise credentials_exception
    except JWTError:
        print("2")
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        print("3")
        raise credentials_exception
    return user


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
    db.commit()  # Commit the transaction to save the new parameters.


# Remove a part from the `parts` table in the database by its ID.
def remove_part_from_db(db: Session, part_id: int) -> None:
    part_to_remove = db.query(Part).filter(Part.id == part_id).first()  # Find the part by ID.
    if part_to_remove:
        db.delete(part_to_remove)  # Mark the part for deletion.
        db.commit()  # Commit the transaction to apply the deletion.

