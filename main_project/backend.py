from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import timedelta, datetime
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from db_models import User, Cart, CartItem
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

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def authenticate_user(username: str, password: str, db: Session):
#     user = db.query(User).filter(User.email == username).first()
#     if not user or not verify_password(password, user.hashed_password):
#         return False
#     return user

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        print(f"User with username {username} not found.")
        return False
    
    if not verify_password(password, user.hashed_password):
        print(f"Password for {username} does not match.")
        return False
    
    return user

def get_token_from_cookie(request: Request):
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


# User retrieval dependency using cookie token
# def get_current_user(token: str = Depends(get_token_from_cookie)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
#     return username




def add_to_cart(db: Session, user_id: int, product_id: int, quantity: int = 1):
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
async def update_cart_item(item_id: int, quantity: int = Form(...), db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart.user_id == user_id).first()
    if cart_item:
        cart_item.quantity = quantity
        db.commit()
    return RedirectResponse(url="/cart", status_code=303)

@app.post("/cart/remove/{item_id}")
async def remove_cart_item(item_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart.user_id == user_id).first()
    if cart_item:
        db.delete(cart_item)
        db.commit()
    return RedirectResponse(url="/cart", status_code=303)

def get_or_create_cart(db: Session, user_id: int):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

