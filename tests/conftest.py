import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
import pytest
from fastapi.testclient import TestClient

# from moto import mock_dynamodb, mock_sqs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with test database"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_sqs():
    """Mock AWS SQS for testing"""
    with mock_sqs():
        client = boto3.client("sqs", region_name="us-east-1")
        # Create test queue
        client.create_queue(QueueName="student-events")
        yield client


@pytest.fixture
def mock_dynamodb():
    """Mock AWS DynamoDB for testing"""
    with mock_dynamodb():
        client = boto3.resource("dynamodb", region_name="us-east-1")
        # Create test table
        client.create_table(
            TableName="audit-logs",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield client
