"""
Test configuration and fixtures for JWT middleware tests.
"""
import datetime
import jwt
import pytest
from unittest.mock import Mock
from flask import Flask


# Test constants
TEST_JWT_SECRET_KEY = "test_secret_key_for_jwt_signing_12345"
TEST_TOKEN_API_KEY = "test_api_key_token_12345"
TEST_SUB = "test-service-api"
TEST_ISS = "test-service-issuer"


@pytest.fixture
def flask_app():
    """Create Flask test application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def request_context(flask_app):
    """Create Flask request context."""
    with flask_app.test_request_context():
        yield flask_app


@pytest.fixture
def mock_app_config():
    """Mock APP_CONFIG with test values."""
    config = Mock()
    config.JWT_SECRET_KEY = TEST_JWT_SECRET_KEY
    config.TOKEN_API_KEY = TEST_TOKEN_API_KEY
    config.SUB = TEST_SUB
    config.ISS = TEST_ISS
    return config


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing."""
    payload = {
        "sub": TEST_SUB,
        "iss": TEST_ISS,
        "iat": datetime.datetime.now(),
        "type": "access",
        "jti": "test-jti-12345"
    }
    return jwt.encode(payload, TEST_JWT_SECRET_KEY, algorithm="HS256")


@pytest.fixture
def invalid_signature_token():
    """Generate a JWT token with invalid signature."""
    payload = {
        "sub": TEST_SUB,
        "iss": TEST_ISS,
        "iat": datetime.datetime.now(),
        "type": "access",
        "jti": "invalid-sig"
    }
    return jwt.encode(payload, "wrong_secret_key", algorithm="HS256")


@pytest.fixture
def malformed_jwt_token():
    """Generate a malformed JWT token."""
    return "invalid.jwt.token"


@pytest.fixture
def missing_fields_token():
    """Generate a JWT token missing required fields."""
    payload = {"iat": datetime.datetime.now()}
    return jwt.encode(payload, TEST_JWT_SECRET_KEY, algorithm="HS256")


@pytest.fixture
def test_function():
    """Simple test function to be decorated."""
    def protected_endpoint():
        return {"message": "success"}, 200
    return protected_endpoint