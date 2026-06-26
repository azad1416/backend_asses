import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_product(client: TestClient) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": "iPhone 15",
            "sku": "IPH15",
            "price": 79999,
            "stock_quantity": 50,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_customer(client: TestClient) -> dict:
    response = client.post(
        "/api/customers",
        json={
            "full_name": "Azad Khan",
            "email": "azad@gmail.com",
            "phone": "9999999999",
        },
    )
    assert response.status_code == 201
    return response.json()
