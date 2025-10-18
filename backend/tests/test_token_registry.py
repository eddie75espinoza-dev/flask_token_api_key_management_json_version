"""
Tests unificados para el módulo token_registry.py
"""
import pytest
import json
import tempfile
import datetime
import os
from pathlib import Path
from core.token_registry import TokenRegistry


@pytest.fixture
def temp_registry_file():
    """Create a temporary registry file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({
            "tokens": [],
            "last_updated": None,
            "total_issued": 0
        }, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestTokenRegistry:
    """Tests unificados para TokenRegistry."""
    
    def test_registry_initialization(self, temp_registry_file):
        """Test TokenRegistry initialization."""
        registry = TokenRegistry(temp_registry_file)
        assert registry.filepath == Path(temp_registry_file)
        assert registry._tokens == []
    
    def test_registry_load_empty_file(self, temp_registry_file):
        """Test loading empty registry file."""
        registry = TokenRegistry(temp_registry_file)
        assert registry._tokens == []
    
    def test_registry_load_with_data(self):
        """Test loading registry with existing data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                "tokens": [
                    {
                        "jti": "test-jti-1",
                        "issued_to": "client-1",
                        "issuer": "api-1",
                        "is_active": True
                    }
                ],
                "last_updated": "2025-01-01T00:00:00Z",
                "total_issued": 1
            }, f)
            temp_path = f.name
        
        try:
            registry = TokenRegistry(temp_path)
            assert len(registry._tokens) == 1
            assert registry._tokens[0]["jti"] == "test-jti-1"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_registry_register_token(self, temp_registry_file):
        """Test registering a new token."""
        registry = TokenRegistry(temp_registry_file)
        
        now = datetime.datetime.now(datetime.timezone.utc)
        result = registry.register_token(
            jti="test-jti",
            issued_to="test-client",
            issuer="test-service",
            token="test-token",
            secret_key="test-secret",
            algorithm="HS256",
            issued_at=now,
            not_before=now,
            expires_at=None,
            token_type="access",
            additional_claims={"fresh": False},
            notes="Test token"
        )
        
        assert result["jti"] == "test-jti"
        assert result["issued_to"] == "test-client"
        assert result["issuer"] == "test-service"
        assert result["is_active"] is True
        assert len(registry._tokens) == 1
    
    def test_registry_register_duplicate_token(self, temp_registry_file):
        """Test registering a duplicate token."""
        registry = TokenRegistry(temp_registry_file)
        
        # Register first token
        registry.register_token(
            jti="test-jti",
            issued_to="client-1",
            issuer="service-1",
            token="token-1",
            secret_key="secret-1"
        )
        
        # Try to register same JTI again
        result = registry.register_token(
            jti="test-jti",
            issued_to="client-2",
            issuer="service-2",
            token="token-2",
            secret_key="secret-2"
        )
        
        # Should return existing token
        assert result["issued_to"] == "client-1"
        assert len(registry._tokens) == 1
    
    def test_registry_get_by_jti(self, temp_registry_file):
        """Test getting token by JTI."""
        registry = TokenRegistry(temp_registry_file)
        
        registry.register_token(
            jti="test-jti",
            issued_to="test-client",
            issuer="test-service",
            token="test-token",
            secret_key="test-secret"
        )
        
        result = registry.get_by_jti("test-jti")
        assert result is not None
        assert result["jti"] == "test-jti"
        assert result["issued_to"] == "test-client"
    
    def test_registry_get_by_jti_not_found(self, temp_registry_file):
        """Test getting non-existent token by JTI."""
        registry = TokenRegistry(temp_registry_file)
        
        result = registry.get_by_jti("nonexistent-jti")
        assert result is None
    
    def test_registry_get_by_issued_to(self, temp_registry_file):
        """Test getting tokens by issued_to."""
        registry = TokenRegistry(temp_registry_file)
        
        # Register tokens for same client
        registry.register_token("jti-1", "client-1", "service-1", "token-1", "secret-1")
        registry.register_token("jti-2", "client-1", "service-2", "token-2", "secret-2")
        registry.register_token("jti-3", "client-2", "service-1", "token-3", "secret-3")
        
        results = registry.get_by_issued_to("client-1")
        assert len(results) == 2
        assert all(token["issued_to"] == "client-1" for token in results)
    
    def test_registry_get_by_issuer(self, temp_registry_file):
        """Test getting tokens by issuer."""
        registry = TokenRegistry(temp_registry_file)
        
        # Register tokens from same issuer
        registry.register_token("jti-1", "client-1", "service-1", "token-1", "secret-1")
        registry.register_token("jti-2", "client-2", "service-1", "token-2", "secret-2")
        registry.register_token("jti-3", "client-1", "service-2", "token-3", "secret-3")
        
        results = registry.get_by_issuer("service-1")
        assert len(results) == 2
        assert all(token["issuer"] == "service-1" for token in results)
    
    def test_registry_mark_inactive(self, temp_registry_file):
        """Test marking token as inactive."""
        registry = TokenRegistry(temp_registry_file)
        
        registry.register_token("test-jti", "client-1", "service-1", "token-1", "secret-1")
        
        result = registry.mark_inactive("test-jti")
        assert result is True
        
        token = registry.get_by_jti("test-jti")
        assert token["is_active"] is False
        assert "deactivated_at" in token
    
    def test_registry_mark_inactive_not_found(self, temp_registry_file):
        """Test marking non-existent token as inactive."""
        registry = TokenRegistry(temp_registry_file)
        
        result = registry.mark_inactive("nonexistent-jti")
        assert result is False
    
    def test_registry_search_tokens(self, temp_registry_file):
        """Test searching tokens with filters."""
        registry = TokenRegistry(temp_registry_file)
        
        # Register test tokens
        registry.register_token("jti-1", "client-1", "service-1", "token-1", "secret-1")
        registry.register_token("jti-2", "client-1", "service-2", "token-2", "secret-2")
        registry.register_token("jti-3", "client-2", "service-1", "token-3", "secret-3")
        
        # Mark one as inactive
        registry.mark_inactive("jti-2")
        
        # Search by issued_to
        results = registry.search_tokens(issued_to="client-1")
        assert len(results) == 2
        
        # Search by issuer
        results = registry.search_tokens(issuer="service-1")
        assert len(results) == 2
        
        # Search by is_active
        results = registry.search_tokens(is_active=True)
        assert len(results) == 2
        
        results = registry.search_tokens(is_active=False)
        assert len(results) == 1
        
        # Search with multiple filters
        results = registry.search_tokens(issued_to="client-1", issuer="service-1")
        assert len(results) == 1
    
    def test_registry_get_statistics(self, temp_registry_file):
        """Test getting registry statistics."""
        registry = TokenRegistry(temp_registry_file)
        
        # Register tokens
        registry.register_token("jti-1", "client-1", "service-1", "token-1", "secret-1")
        registry.register_token("jti-2", "client-1", "service-2", "token-2", "secret-2")
        registry.register_token("jti-3", "client-2", "service-1", "token-3", "secret-3")
        
        # Mark one as inactive
        registry.mark_inactive("jti-2")
        
        stats = registry.get_statistics()
        
        assert stats["total_tokens"] == 3
        assert stats["active_tokens"] == 2
        assert stats["inactive_tokens"] == 1
        assert stats["unique_issuers"] == 2
        assert stats["unique_subjects"] == 2
    
    def test_registry_count_tokens(self, temp_registry_file):
        """Test counting tokens."""
        registry = TokenRegistry(temp_registry_file)
        
        assert registry.count_tokens() == 0
        
        registry.register_token("jti-1", "client-1", "service-1", "token-1", "secret-1")
        assert registry.count_tokens() == 1
        
        registry.register_token("jti-2", "client-2", "service-2", "token-2", "secret-2")
        assert registry.count_tokens() == 2
    
    def test_registry_save_exception(self, temp_registry_file):
        """Test save method with exception."""
        from unittest.mock import patch
        
        registry = TokenRegistry(temp_registry_file)
        registry._tokens.append({"jti": "test-jti"})
        
        with patch('builtins.open', side_effect=Exception("File error")):
            # Should not raise exception
            registry._save()
    
    def test_registry_load_exception(self):
        """Test load method with exception."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"invalid": json}')
            temp_path = f.name
        
        try:
            registry = TokenRegistry(temp_path)
            # Should handle JSON error gracefully
            assert registry._tokens == []
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_registry_hash_secret(self, temp_registry_file):
        """Test secret key hashing."""
        registry = TokenRegistry(temp_registry_file)
        
        hash1 = registry._hash_secret("test-secret")
        hash2 = registry._hash_secret("test-secret")
        hash3 = registry._hash_secret("different-secret")
        
        assert hash1 == hash2  # Same input should produce same hash
        assert hash1 != hash3  # Different input should produce different hash
        assert len(hash1) == 16  # Should be truncated to 16 characters
