from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config


Base = declarative_base()

def config():
    return "postgresql://postgres:testas000@localhost:5432/car_parts_db"


engine = create_engine(config())


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()  


