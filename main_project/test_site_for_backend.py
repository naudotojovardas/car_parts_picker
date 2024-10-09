from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator
from datetime import timedelta, datetime
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
import psycopg2  # Add psycopg2 for direct connections (optional)
from config import config

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

# Update this URL to use PostgreSQL instead of SQLite
# DATABASE_URL = "postgresql://your_user:your_password@localhost:5432/your_db_name"

# PostgreSQL Engine and Session Setup
engine = create_engine(config())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# PostgreSQL Direct Connection Example (optional if not using SQLAlchemy)
# def connect_to_postgres():
#     try:
#         conn = psycopg2.connect(
#             dbname="your_db_name",
#             user="your_user",
#             password="your_password",
#             host="localhost",  # Or your PostgreSQL server address
#             port="5432"  # Default PostgreSQL port
#         )
#         return conn
#     except Exception as e:
#         print(f"Error connecting to PostgreSQL: {e}")
#         raise 

# Database Models
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


class CarParameter(Base):
    __tablename__ = 'part_parameters'
    id = Column(Integer, primary_key=True, index=True)
    car_name = Column(String, index=True)
    manufacturer = Column(String)
    year = Column(Integer)
    engine_type = Column(String)

    parts = relationship("Part", back_populates="part_parameters")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Example function to use PostgreSQL directly with psycopg2
@app.get("/direct_db_test")
async def direct_db_test():
    conn = connect_to_postgres()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM your_table")
    rows = cur.fetchall()
    
    cur.close()
    conn.close()

    return {"rows": rows}

ADMIN_PASSWORD = "admin123"

# Functions to manage parts and parameters using SQLAlchemy
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

# Pydantic Models
class UserCreate(BaseModel):
    email: str
    password: str
    confirm_password: str

    @field_validator('email')
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email. Must contain '@'.")
        return v

    @field_validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError("Passwords do not match.")
        return v

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Register endpoint
@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    user_in_db = db.query(User).filter(User.email == user.email).first()
    if user_in_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully"}

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(user.email, user.password, db)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": db_user.email}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}

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

fake_users_db = {}