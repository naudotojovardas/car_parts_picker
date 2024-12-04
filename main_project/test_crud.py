import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db  # Import your FastAPI app and dependency
from db_models import User, Part, CartItem, CarParameter
from database import Base
from crud import add_part_to_db, add_part_parameters_to_db, remove_part_from_db

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use SQLite for testing
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the dependency
@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)  # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)



def test_add_part_to_db(test_db):
    add_part_to_db(test_db, name="Part1", description="Test Part", price=100.0, currency="USD", stock_quantity=10)
    part = test_db.query(Part).filter_by(part_name="Part1").first()
    assert part is not None
    assert part.price == 100.0


def test_add_part_parameters_to_db(test_db):
    add_part_parameters_to_db(test_db, car_name="Test Car", manufacturer="Test Maker", year=2022, engine_type="V8")
    param = test_db.query(CarParameter).filter_by(car_name="Test Car").first()
    assert param is not None
    assert param.engine_type == "V8"


def test_remove_part_from_db(test_db):
    part = Part(part_name="PartToRemove", description="Remove This", price=50.0, currency="USD", stock_quantity=5)
    test_db.add(part)
    test_db.commit()

    remove_part_from_db(test_db, part_id=part.id)
    assert test_db.query(Part).filter_by(id=part.id).first() is None


pytest.main(["-v", "test_crud.py"])




