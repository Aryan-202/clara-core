import pytest
from fastapi.testclient import TestClient
from clara.main import clara


@pytest.fixture(scope="session")
def app():
    """Return the FastAPI application instance"""
    return clara


@pytest.fixture(scope="session")
def client(app):
    """Return a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def clean_connections():
    """Ensure clean connection state before each test"""
    from clara.api.ws.router import manager
    # Clear any existing connections
    manager.active_connections.clear()
    yield
    # Clean up after test
    manager.active_connections.clear()
