from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import timedelta, datetime
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from db_models import User
from database import get_db
from typing import Optional
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

def authenticate_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"User with username {email} not found.")
        return False
    
    if not verify_password(password, user.hashed_password):
        print(f"Password for {email} does not match.")
        return False
    
    return user



def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == username).first()
    if user is None:
        raise credentials_exception
    return user
