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
import psycopg2  # For direct PostgreSQL connection
from config import config  # Import the config function for DB connection details

# CORS Middleware to allow frontend communication
app = FastAPI()

def config():
    return "postgresql://postgres:testas000@localhost:5432/car_parts_db"


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

# ----- SQLAlchemy SETUP (ORM) -----
# 1. Get the connection string from config() (e.g., postgresql://user:pass@localhost/dbname)
# 2. `create_engine()` is used to establish a connection to the database using the provided connection string.
engine = create_engine(config())

# 3. `sessionmaker` is a factory that creates new `Session` objects bound to our engine. This is used to interact with the DB using SQLAlchemy.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. `Base` is used as a declarative base class for creating our ORM models.
Base = declarative_base()

# ----- Database Models -----
# These models map to the tables in the PostgreSQL database. SQLAlchemy will use them to execute queries.

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

# 5. This line creates all the tables in the database if they do not exist already, based on the models defined above.
Base.metadata.create_all(bind=engine)

# ----- SQLAlchemy Database Dependency -----
# 6. This function manages the session with the database, ensuring the connection is opened and closed properly.
# `SessionLocal()` creates a new session. The session is closed after the request is handled.
def get_db():
    db = SessionLocal()
    try:
        yield db  # This yield allows FastAPI to return the session to the route using this dependency.
    finally:
        db.close()  # Always close the session after completing the transaction.

# ----- Direct Database Access (psycopg2) -----
# This function will now be renamed to `direct_db`.
@app.get("/direct_db")
async def direct_db():
    conn_info = config()  # 7. Retrieve the connection string from the `config()` function.
    try:
        # 8. Establish a connection to the PostgreSQL database directly using psycopg2.
        conn = psycopg2.connect(conn_info)
        
        # 9. Create a cursor, which allows you to execute SQL commands.
        cur = conn.cursor()

        # 10. Execute an SQL query. (Replace 'your_table' with your actual table name)
        cur.execute("SELECT * FROM your_table")  
        
        # 11. Fetch all results from the executed query.
        rows = cur.fetchall()

        # 12. Always close the cursor and connection after you're done to prevent resource leaks.
        cur.close()
        conn.close()

        # 13. Return the fetched rows as the response.
        return {"rows": rows}

    # 14. Catch and handle any exceptions that occur during the connection or query execution.
    except Exception as e:
        return {"error": str(e)}

# ----- CRUD Operations using SQLAlchemy -----
# These functions use SQLAlchemy's ORM to perform CRUD operations (create, read, update, delete) on the database.

# 15. Add a part to the `parts` table in the database.
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

# ----- Pydantic Models -----
# These models are used to validate incoming data.

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

# ----- Password and Token Utilities -----
# These functions handle password hashing, verification, and JWT creation for authentication.

ADMIN_PASSWORD = "admin123"

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

# ----- Authentication and Registration -----
# FastAPI route handlers for user registration and login.

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

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


