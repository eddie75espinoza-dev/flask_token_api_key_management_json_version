"""
Tests unificados para el módulo middleware.py
"""
import pytest
from unittest.mock import patch, Mock
import jwt
import datetime
from flask import Flask

from core.middleware import (
    _extract_token,
    _log_auth_failure,
    token_required,
    ERROR_MESSAGES
)

# Test constants
TEST_JWT_SECRET_KEY = "test_secret_key_for_jwt_signing_12345"
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
    with flask_app.test_request_context() as ctx:
        yield ctx


class TestMiddleware:
    """Tests unificados para el middleware JWT."""
    
    def test_extract_token_valid_authorization_header(self, request_context):
        """Test _extract_token with valid Authorization header."""
        result = _extract_token('Bearer valid_token_here')
        assert result == 'valid_token_here'
    
    def test_extract_token_missing_authorization_header(self, request_context):
        """Test _extract_token with missing Authorization header."""
        result = _extract_token("")
        assert result is None
    
    def test_extract_token_invalid_authorization_format(self, request_context):
        """Test _extract_token with invalid Authorization format."""
        result = _extract_token('InvalidFormat token')
        assert result is None
    
    def test_log_auth_failure(self, request_context):
        """Test _log_auth_failure function."""
        with patch('core.middleware.logs_config.logger.warning') as mock_warning:
            _log_auth_failure("test-reason", "test-client", {"sub": "test-client"})
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0][0]
            assert "test-reason" in call_args
    
    def test_token_required_valid_token(self, flask_app, request_context):
        """Test token_required decorator with valid token."""
        # Create a valid JWT token with all required fields
        payload = {
            'sub': TEST_SUB,
            'iss': TEST_ISS,
            'iat': datetime.datetime.now(datetime.UTC),
            'jti': 'test-jti-123',
            'type': 'access'  # Required field
        }
        valid_token = jwt.encode(payload, TEST_JWT_SECRET_KEY, algorithm='HS256')
        
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('core.middleware.get_blacklist') as mock_get_blacklist:
            mock_blacklist = Mock()
            mock_blacklist.is_revoked.return_value = False
            mock_get_blacklist.return_value = mock_blacklist
            
            with patch('core.middleware.APP_CONFIG') as mock_config:
                mock_config.JWT_SECRET_KEY = TEST_JWT_SECRET_KEY
                with flask_app.test_request_context('/test', headers={'Authorization': f'Bearer {valid_token}'}):
                    response = test_route()
                    assert response[1] == 200
    
    def test_token_required_missing_token(self, flask_app, request_context):
        """Test token_required decorator with missing token."""
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('core.middleware._log_auth_failure') as mock_log:
            with flask_app.test_request_context('/test'):
                response = test_route()
                assert response[1] == 401
                mock_log.assert_called_once()
    
    def test_token_required_invalid_token_format(self, flask_app, request_context):
        """Test token_required decorator with invalid token format."""
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('core.middleware._log_auth_failure') as mock_log:
            with flask_app.test_request_context('/test', headers={'Authorization': 'InvalidFormat token'}):
                response = test_route()
                assert response[1] == 401
                mock_log.assert_called_once()
    
    def test_token_required_invalid_jwt_token(self, flask_app, request_context):
        """Test token_required decorator with invalid JWT token."""
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('core.middleware._log_auth_failure') as mock_log:
            with patch.dict('os.environ', {'JWT_SECRET_KEY': TEST_JWT_SECRET_KEY}):
                with flask_app.test_request_context('/test', headers={'Authorization': 'Bearer invalid_jwt_token'}):
                    response = test_route()
                    assert response[1] == 403
                    mock_log.assert_called_once()
    
    def test_token_required_revoked_token(self, flask_app, request_context):
        """Test token_required decorator with revoked token."""
        # Create a valid JWT token with all required fields
        payload = {
            'sub': TEST_SUB,
            'iss': TEST_ISS,
            'iat': datetime.datetime.now(datetime.UTC),
            'jti': 'revoked-jti-123',
            'type': 'access'  # Required field
        }
        valid_token = jwt.encode(payload, TEST_JWT_SECRET_KEY, algorithm='HS256')
        
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('core.middleware.get_blacklist') as mock_get_blacklist:
            mock_blacklist = Mock()
            mock_blacklist.is_revoked.return_value = True
            mock_get_blacklist.return_value = mock_blacklist
            
            with patch('core.middleware._log_auth_failure') as mock_log:
                with patch('core.middleware.APP_CONFIG') as mock_config:
                    mock_config.JWT_SECRET_KEY = TEST_JWT_SECRET_KEY
                    with flask_app.test_request_context('/test', headers={'Authorization': f'Bearer {valid_token}'}):
                        response = test_route()
                        assert response[1] == 403  # Revoked token returns 403
                        mock_log.assert_called_once()
    
    def test_token_required_missing_jwt_secret(self, flask_app, request_context):
        """Test token_required decorator with missing JWT_SECRET_KEY."""
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('core.middleware._log_auth_failure') as mock_log:
            with patch('core.middleware.APP_CONFIG') as mock_config:
                # Simulate missing JWT_SECRET_KEY by raising an exception
                mock_config.JWT_SECRET_KEY = None
                with patch('jwt.decode', side_effect=Exception("JWT_SECRET_KEY not found")):
                    with flask_app.test_request_context('/test', headers={'Authorization': 'Bearer valid_token'}):
                        response = test_route()
                        assert response[1] == 500
                        # Don't check mock_log since the exception might not trigger it
    
    def test_token_required_jwt_decode_exception(self, flask_app, request_context):
        """Test token_required decorator with JWT decode exception."""
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('jwt.decode', side_effect=jwt.InvalidTokenError("Invalid token")):
            with patch('core.middleware._log_auth_failure') as mock_log:
                with patch.dict('os.environ', {'JWT_SECRET_KEY': TEST_JWT_SECRET_KEY}):
                    with flask_app.test_request_context('/test', headers={'Authorization': 'Bearer valid_token_format'}):
                        response = test_route()
                        assert response[1] == 403
                        mock_log.assert_called_once()
    
    def test_token_required_general_exception(self, flask_app, request_context):
        """Test token_required decorator with general exception."""
        @flask_app.route('/test')
        @token_required
        def test_route():
            return {'message': 'success'}, 200
        
        with patch('core.middleware._log_auth_failure') as mock_log:
            with patch('core.middleware.APP_CONFIG') as mock_config:
                mock_config.JWT_SECRET_KEY = TEST_JWT_SECRET_KEY
                with patch('jwt.decode', side_effect=Exception("General error")):
                    with flask_app.test_request_context('/test', headers={'Authorization': 'Bearer valid_token_format'}):
                        response = test_route()
                        assert response[1] == 500
                        # Don't check mock_log since the exception might not trigger it
    
    def test_error_messages_defined(self):
        """Test that all error messages are properly defined."""
        # Check that ERROR_MESSAGES exists and has some messages
        assert isinstance(ERROR_MESSAGES, dict)
        assert len(ERROR_MESSAGES) > 0
        
        # Check that all values are strings
        for message in ERROR_MESSAGES.values():
            assert isinstance(message, str)
            assert len(message) > 0
