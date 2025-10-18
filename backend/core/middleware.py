"""
JWT Authentication Middleware with Multi-Token Support.

This module provides flexible JWT authentication that accepts any valid JWT
signed with the configured JWT_SECRET_KEY. Includes token blacklist support
and client identification for logging and auditing.
"""

import jwt
from flask import request, jsonify, g
from functools import wraps
from typing import Optional, Tuple, Any, Callable, Dict

from core.config import APP_CONFIG
from core.token_blacklist import get_blacklist
from logs import logs_config


BEARER_PREFIX = "Bearer "
EXPECTED_ALGORITHM = "HS256"

# Standardized error messages (no internal details exposed)
ERROR_MESSAGES = {
    'missing_header': 'Authorization required',
    'invalid_format': 'Invalid authorization format',
    'invalid_token': 'Invalid token',
    'token_revoked': 'Token has been revoked',
    'access_denied': 'Access denied',
    'server_error': 'Authentication error'
}


def _extract_token(auth_header: str) -> Optional[str]:
    """
    Safely extracts token from Authorization header.
    
    Args:
        auth_header: Authorization header value
        
    Returns:
        Extracted token or None if invalid format
    """
    if not auth_header.startswith(BEARER_PREFIX):
        return None
    
    # Extract token and validate it's not empty
    token = auth_header[len(BEARER_PREFIX):].strip()
    return token if token else None


def _extract_client_info(decoded_token: Dict) -> Dict:
    """
    Extract client identification information from JWT payload.
    
    Args:
        decoded_token: Decoded JWT payload
    
    Returns:
        Dictionary with client information for logging
    """
    return {
        'jti': decoded_token.get('jti', 'unknown'),
        'sub': decoded_token.get('sub', 'unknown'),
        'iss': decoded_token.get('iss', 'unknown'),
        'type': decoded_token.get('type', 'unknown'),
        'iat': decoded_token.get('iat', 'unknown')
    }


def _log_auth_failure(reason: str, details: str = "", client_info: Optional[Dict] = None) -> None:
    """
    Securely logs authentication failures without exposing sensitive data.
    
    Filters out sensitive information like tokens, keys, or secrets
    from the log details to prevent security leaks.
    
    Args:
        reason: Primary reason for authentication failure
        details: Additional details (filtered for sensitive data)
        client_info: Client identification info if available
    """
    log_message = f"Authentication failed: {reason}"
    
    # Add client info if available
    if client_info:
        log_message += f" [Client: {client_info.get('sub', 'unknown')}, "
        log_message += f"JTI: {client_info.get('jti', 'unknown')}]"
    
    # Only add details if they don't contain sensitive information
    if details and not any(
        sensitive in details.lower() 
        for sensitive in ['token', 'key', 'secret']
    ):
        log_message += f" - {details}"
    
    logs_config.logger.warning(log_message)


def _log_auth_success(client_info: Dict) -> None:
    """
    Log successful authentication with client identification.
    
    Args:
        client_info: Client identification information
    """
    logs_config.logger.info(
        f"Authentication successful - Client: {client_info.get('sub')}, "
        f"Issuer: {client_info.get('iss')}, JTI: {client_info.get('jti')}"
    )


def token_required(func: Callable) -> Callable:
    """
    Decorator that enforces JWT authentication with blacklist support.
    
    This implements a flexible authentication system:
    1. Any JWT signed with JWT_SECRET_KEY is accepted
    2. JWT payload is validated for required fields: sub, iss, iat, type
    3. Token is checked against revocation blacklist
    4. Client information is extracted and added to Flask g context
    
    Authentication flow:
    - Extract Bearer token from Authorization header
    - Decode token as JWT using JWT_SECRET_KEY for signature verification
    - Validate JWT payload fields (sub, iss, iat, type)
    - Check if token (JTI) is in blacklist
    - Extract and store client info in g.client_info for logging
    
    Security features:
    - Secure logging (no token exposure)
    - Standardized error messages
    - Token revocation via blacklist
    - Client identification for audit trails
    - Comprehensive JWT validation options
    
    Args:
        func: Function to protect with authentication
        
    Returns:
        Decorated function with JWT validation and blacklist checking
    """
    @wraps(func)
    def decorated(*args, **kwargs) -> Tuple[Any, int]:
        try:
            # Step 1: Validate Authorization header presence
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                _log_auth_failure("Missing Authorization header")
                return jsonify({'msg': ERROR_MESSAGES['missing_header']}), 401

            # Step 2: Extract token safely from header
            token = _extract_token(auth_header)
            if not token:
                _log_auth_failure("Invalid Authorization header format")
                return jsonify({'msg': ERROR_MESSAGES['invalid_format']}), 401

            # Step 3: Decode and validate JWT structure and signature
            # Any JWT signed with JWT_SECRET_KEY is valid
            decoded_token = jwt.decode(
                token, 
                APP_CONFIG.JWT_SECRET_KEY, 
                algorithms=[EXPECTED_ALGORITHM],
                options={
                    "verify_signature": True,    # Verify JWT signature
                    "verify_exp": False,         # Don't require expiration
                    "verify_iat": True,          # Verify issued at time
                    "require": ["sub", "iss", "iat", "type"]  # Required JWT fields
                }
            )
            
            # Step 4: Extract client information for logging and context
            client_info = _extract_client_info(decoded_token)
            
            # Step 5: Check if token is revoked (blacklist validation)
            blacklist = get_blacklist()
            jti = client_info.get('jti')
            
            if blacklist.is_revoked(jti):
                _log_auth_failure(
                    "Token revoked", 
                    "Token found in blacklist",
                    client_info
                )
                return jsonify({'msg': ERROR_MESSAGES['token_revoked']}), 403
            
            # Step 6: Store client info in Flask g context for request lifecycle
            g.client_info = client_info
            g.decoded_token = decoded_token
            
            # Step 7: Log successful authentication
            _log_auth_success(client_info)
            
            # Step 8: Authentication successful - proceed with original function
            return func(*args, **kwargs)

        except jwt.InvalidSignatureError:
            # JWT signature verification failed
            _log_auth_failure("Invalid JWT signature")
            return jsonify({'msg': ERROR_MESSAGES['invalid_token']}), 403
            
        except jwt.DecodeError:
            # JWT structure is malformed
            _log_auth_failure("JWT decode error")
            return jsonify({'msg': ERROR_MESSAGES['invalid_token']}), 403
            
        except jwt.MissingRequiredClaimError as error:
            # Required JWT claims missing
            _log_auth_failure("Missing required JWT claims", str(error))
            return jsonify({'msg': ERROR_MESSAGES['invalid_token']}), 403
            
        except jwt.InvalidTokenError as error:
            # Other JWT validation errors
            _log_auth_failure("Invalid JWT token", str(error))
            return jsonify({'msg': ERROR_MESSAGES['invalid_token']}), 403
            
        except Exception as error:
            # Unexpected errors - log for debugging but don't expose details
            logs_config.logger.error(
                f"Unexpected authentication error: {type(error).__name__}: {str(error)}"
            )
            return jsonify({'msg': ERROR_MESSAGES['server_error']}), 500

    return decorated
