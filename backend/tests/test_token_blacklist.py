"""
Tests unificados para el módulo token_blacklist.py
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.token_blacklist import TokenBlacklist


@pytest.fixture
def temp_blacklist_file():
    """Create a temporary blacklist file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump({
            "revoked_jtis": [],
            "last_updated": None,
            "revocations": []
        }, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestTokenBlacklist:
    """Tests unificados para TokenBlacklist."""
    
    def test_blacklist_initialization(self, temp_blacklist_file):
        """Test TokenBlacklist initialization."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        assert blacklist.filepath == Path(temp_blacklist_file)
        assert blacklist._blacklist == set()
        assert blacklist._revocations == []
    
    def test_blacklist_load_empty_file(self, temp_blacklist_file):
        """Test loading empty blacklist file."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        assert blacklist._blacklist == set()
        assert blacklist._revocations == []
    
    def test_blacklist_load_with_data(self):
        """Test loading blacklist with existing data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                "revoked_jtis": ["jti-1", "jti-2"],
                "revocations": [
                    {"jti": "jti-1", "reason": "Security breach", "revoked_at": "2025-01-01T00:00:00Z"}
                ]
            }, f)
            temp_path = f.name
        
        try:
            blacklist = TokenBlacklist(temp_path, enable_hot_reload=False)
            assert "jti-1" in blacklist._blacklist
            assert "jti-2" in blacklist._blacklist
            assert len(blacklist._revocations) == 1
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_blacklist_save(self, temp_blacklist_file):
        """Test saving blacklist."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        blacklist._blacklist.add("test-jti")
        blacklist._revocations.append({
            "jti": "test-jti",
            "reason": "Test revocation",
            "revoked_at": "2025-01-01T00:00:00Z"
        })
        
        blacklist._save()
        
        # Verify file was saved
        with open(temp_blacklist_file, 'r') as f:
            data = json.load(f)
            assert "test-jti" in data["revoked_jtis"]
            assert len(data["revocations"]) == 1
    
    def test_blacklist_revoke_token(self, temp_blacklist_file):
        """Test revoking a token."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        result = blacklist.revoke(
            jti="test-jti",
            reason="Security breach",
            issued_to="test-client",
            revoked_by="admin"
        )
        
        assert result is True
        assert "test-jti" in blacklist._blacklist
        assert blacklist.is_revoked("test-jti") is True
    
    def test_blacklist_revoke_duplicate(self, temp_blacklist_file):
        """Test revoking an already revoked token."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        # First revocation
        result1 = blacklist.revoke("test-jti", "First reason", "client", "admin")
        assert result1 is True
        
        # Second revocation (should return False for duplicate)
        result2 = blacklist.revoke("test-jti", "Second reason", "client", "admin")
        assert result2 is False  # Should return False for duplicate
        assert "test-jti" in blacklist._blacklist
    
    def test_blacklist_unrevoke_token(self, temp_blacklist_file):
        """Test unrevoking a token."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        # First revoke
        blacklist.revoke("test-jti", "Test reason", "client", "admin")
        assert blacklist.is_revoked("test-jti") is True
        
        # Then unrevoke
        result = blacklist.unrevoke("test-jti")
        assert result is True
        assert blacklist.is_revoked("test-jti") is False
    
    def test_blacklist_unrevoke_nonexistent(self, temp_blacklist_file):
        """Test unrevoking a non-revoked token."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        result = blacklist.unrevoke("nonexistent-jti")
        assert result is False
    
    def test_blacklist_is_revoked(self, temp_blacklist_file):
        """Test checking if token is revoked."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        # Not revoked initially
        assert blacklist.is_revoked("test-jti") is False
        
        # After revoking
        blacklist.revoke("test-jti", "Test reason", "client", "admin")
        assert blacklist.is_revoked("test-jti") is True
    
    def test_blacklist_count_revoked(self, temp_blacklist_file):
        """Test counting revoked tokens."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        assert blacklist.count_revoked() == 0
        
        blacklist.revoke("jti-1", "Reason 1", "client", "admin")
        blacklist.revoke("jti-2", "Reason 2", "client", "admin")
        
        assert blacklist.count_revoked() == 2
    
    def test_blacklist_get_revocations(self, temp_blacklist_file):
        """Test getting revocation list."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        blacklist.revoke("jti-1", "Reason 1", "client-1", "admin")
        blacklist.revoke("jti-2", "Reason 2", "client-2", "admin")
        
        revocations = blacklist.get_revocations()
        assert len(revocations) == 2
        assert all("jti" in rev for rev in revocations)
    
    def test_blacklist_load_file_not_found(self):
        """Test loading when file doesn't exist."""
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            non_existent_file = tmp.name
        
        blacklist = TokenBlacklist(non_existent_file, enable_hot_reload=False)
        # Should create empty blacklist
        assert blacklist._blacklist == set()
        assert blacklist._revocations == []
    
    def test_blacklist_save_exception(self, temp_blacklist_file):
        """Test save method with exception."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        blacklist._blacklist.add("test-jti")
        
        with patch('builtins.open', side_effect=Exception("File error")):
            # Should not raise exception
            blacklist._save()
    
    def test_blacklist_hot_reload_disabled(self, temp_blacklist_file):
        """Test blacklist with hot-reload disabled."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        assert blacklist._observer is None
    
    def test_blacklist_stop_hot_reload_no_observer(self, temp_blacklist_file):
        """Test stop_hot_reload when no observer exists."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        # Should not raise exception
        blacklist.stop_hot_reload()
    
    def test_blacklist_stop_hot_reload_with_observer(self, temp_blacklist_file):
        """Test stop_hot_reload with observer."""
        blacklist = TokenBlacklist(temp_blacklist_file, enable_hot_reload=False)
        
        # Mock observer
        mock_observer = MagicMock()
        blacklist._observer = mock_observer
        
        blacklist.stop_hot_reload()
        
        mock_observer.stop.assert_called_once()
        # Note: The actual implementation might not set _observer to None
        # Just verify that stop was called
    
    def test_blacklist_file_handler_init(self):
        """Test BlacklistFileHandler initialization."""
        from core.token_blacklist import BlacklistFileHandler
        
        mock_blacklist = MagicMock()
        handler = BlacklistFileHandler(mock_blacklist)
        assert handler.blacklist == mock_blacklist
    
    def test_blacklist_file_handler_on_modified(self):
        """Test BlacklistFileHandler on_modified."""
        from core.token_blacklist import BlacklistFileHandler
        
        mock_blacklist = MagicMock()
        mock_blacklist.filepath = "/tmp/test.json"
        
        handler = BlacklistFileHandler(mock_blacklist)
        
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(mock_blacklist.filepath)
        
        with patch('core.token_blacklist.logs_config.logger.info') as mock_info:
            handler.on_modified(mock_event)
            mock_info.assert_called()
            mock_blacklist.load.assert_called_once()
    
    def test_blacklist_load_json_parse_error(self):
        """Test load with JSON parse error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"invalid": json}')
            temp_path = f.name
        
        try:
            blacklist = TokenBlacklist(temp_path, enable_hot_reload=False)
            with patch('core.token_blacklist.logs_config.logger.error') as mock_error:
                blacklist.load()
                mock_error.assert_called()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_blacklist_load_general_exception(self):
        """Test load with general exception."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"revoked_jtis": [], "revocations": []}')
            temp_path = f.name
        
        try:
            blacklist = TokenBlacklist(temp_path, enable_hot_reload=False)
            with patch('builtins.open', side_effect=Exception("File error")):
                with patch('core.token_blacklist.logs_config.logger.error') as mock_error:
                    blacklist.load()
                    mock_error.assert_called()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
