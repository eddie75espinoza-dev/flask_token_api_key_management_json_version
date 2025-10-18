"""
Tests unificados para el módulo token_cli.py
"""
import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path


class TestTokenCLI:
    """Tests unificados para el CLI de tokens."""
    
    @patch.dict('os.environ', {'JWT_SECRET_KEY': 'test-secret'})
    def test_get_jwt_secret_success(self):
        """Test get_jwt_secret con variable de entorno válida."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import get_jwt_secret
            
            result = get_jwt_secret()
            assert result == "test-secret"
        except Exception as e:
            pytest.fail(f"get_jwt_secret test failed: {e}")
    
    def test_get_jwt_secret_missing(self):
        """Test get_jwt_secret con variable de entorno faltante."""
        with patch.dict('os.environ', {}, clear=True):
            try:
                import sys
                sys.path.insert(0, '/backend')
                from scripts.token_cli import get_jwt_secret
                
                with pytest.raises(ValueError, match="JWT_SECRET_KEY not found"):
                    get_jwt_secret()
            except Exception as e:
                pytest.fail(f"get_jwt_secret missing test failed: {e}")
    
    @patch('scripts.token_cli.jwt.encode')
    @patch('scripts.token_cli.get_jwt_secret')
    @patch('scripts.token_cli.TokenRegistry')
    def test_generate_token_success(self, mock_registry_class, mock_get_secret, mock_encode):
        """Test generate_token exitoso."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_get_secret.return_value = "test-secret"
        mock_encode.return_value = "test-jwt-token"
        
        # Mock the return value to match what the actual function returns
        mock_registry.register_token.return_value = {
            'jti': 'test-jti',
            'issued_to': 'test-client',
            'issuer': 'test-service',
            'token': 'test-jwt-token',
            'issued_at': '2025-01-01T00:00:00Z'
        }
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import generate_token
            
            result = generate_token(
                issued_to="test-client",
                issuer="test-service",
                token_type="access",
                notes="Test token"
            )
            
            # Check that the result has the expected structure
            assert 'jti' in result
            assert 'issued_to' in result
            assert 'issuer' in result
            assert 'token' in result
            assert result['issued_to'] == 'test-client'
            assert result['issuer'] == 'test-service'
            assert result['token'] == 'test-jwt-token'
            mock_registry.register_token.assert_called_once()
        except Exception as e:
            pytest.fail(f"generate_token test failed: {e}")
    
    @patch('scripts.token_cli.TokenRegistry')
    def test_list_tokens_all(self, mock_registry_class):
        """Test list_tokens sin filtros."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry.search_tokens.return_value = [
            {
                'jti': 'test-jti-1',
                'issued_to': 'client-1',
                'issuer': 'api-1',
                'token_type': 'access',
                'is_active': True
            }
        ]
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import list_tokens
            
            result = list_tokens()
            assert len(result) == 1
            assert result[0]['jti'] == 'test-jti-1'
            mock_registry.search_tokens.assert_called_once_with(is_active=None)
        except Exception as e:
            pytest.fail(f"list_tokens test failed: {e}")
    
    @patch('scripts.token_cli.TokenRegistry')
    def test_list_tokens_with_filters(self, mock_registry_class):
        """Test list_tokens con filtros."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry.search_tokens.return_value = [
            {
                'jti': 'test-jti-1',
                'issued_to': 'client-1',
                'issuer': 'api-1',
                'token_type': 'access',
                'is_active': True
            }
        ]
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import list_tokens
            
            result = list_tokens(issued_to="client-1", issuer="api-1", active_only=True)
            assert len(result) == 1
            mock_registry.search_tokens.assert_called_once_with(
                issued_to="client-1",
                issuer="api-1",
                is_active=True
            )
        except Exception as e:
            pytest.fail(f"list_tokens with filters test failed: {e}")
    
    @patch('scripts.token_cli.TokenRegistry')
    def test_query_token_found(self, mock_registry_class):
        """Test query_token cuando el token existe."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_by_jti.return_value = {
            'jti': 'test-jti',
            'issued_to': 'test-client',
            'issuer': 'test-service',
            'is_active': True
        }
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import query_token
            
            result = query_token('test-jti')
            assert result is not None
            assert result['jti'] == 'test-jti'
            mock_registry.get_by_jti.assert_called_once_with('test-jti')
        except Exception as e:
            pytest.fail(f"query_token found test failed: {e}")
    
    @patch('scripts.token_cli.TokenRegistry')
    def test_query_token_not_found(self, mock_registry_class):
        """Test query_token cuando el token no existe."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_by_jti.return_value = None
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import query_token
            
            result = query_token('nonexistent-jti')
            assert result is None
            mock_registry.get_by_jti.assert_called_once_with('nonexistent-jti')
        except Exception as e:
            pytest.fail(f"query_token not found test failed: {e}")
    
    @patch('scripts.token_cli.get_blacklist')
    @patch('scripts.token_cli.TokenRegistry')
    def test_revoke_token_success(self, mock_registry_class, mock_get_blacklist):
        """Test revoke_token exitoso."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_by_jti.return_value = {
            'jti': 'test-jti',
            'issued_to': 'test-client'
        }
        
        mock_blacklist = MagicMock()
        mock_get_blacklist.return_value = mock_blacklist
        mock_blacklist.revoke.return_value = True
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import revoke_token
            
            result = revoke_token(
                jti='test-jti',
                reason='Test revocation',
                revoked_by='admin'
            )
            assert result is True
            mock_blacklist.revoke.assert_called_once()
        except Exception as e:
            pytest.fail(f"revoke_token test failed: {e}")
    
    @patch('scripts.token_cli.get_blacklist')
    @patch('scripts.token_cli.TokenRegistry')
    def test_revoke_token_not_found(self, mock_registry_class, mock_get_blacklist):
        """Test revoke_token cuando el token no existe en el registro."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_by_jti.return_value = None
        
        mock_blacklist = MagicMock()
        mock_get_blacklist.return_value = mock_blacklist
        mock_blacklist.revoke.return_value = True
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import revoke_token
            
            result = revoke_token(
                jti='nonexistent-jti',
                reason='Test revocation',
                revoked_by='admin'
            )
            assert result is True
            mock_blacklist.revoke.assert_called_once()
        except Exception as e:
            pytest.fail(f"revoke_token not found test failed: {e}")
    
    # Tests de unrevoke eliminados - comando no disponible
    
    @patch('scripts.token_cli.get_blacklist')
    @patch('scripts.token_cli.TokenRegistry')
    def test_get_statistics_success(self, mock_registry_class, mock_get_blacklist):
        """Test get_statistics exitoso."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_statistics.return_value = {
            'total_tokens': 5,
            'active_tokens': 3,
            'inactive_tokens': 2,
            'unique_issuers': 2,
            'unique_subjects': 3
        }
        
        mock_blacklist = MagicMock()
        mock_get_blacklist.return_value = mock_blacklist
        mock_blacklist.count_revoked.return_value = 2
        mock_blacklist.get_revocations.return_value = [
            {'jti': 'revoked-1', 'reason': 'Security breach'}
        ]
        
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import get_statistics
            
            result = get_statistics()
            assert 'registry' in result
            assert 'blacklist' in result
            assert result['registry']['total_tokens'] == 5
            assert result['blacklist']['revoked_count'] == 2
        except Exception as e:
            pytest.fail(f"get_statistics test failed: {e}")
    
    def test_print_token_table(self):
        """Test print_token_table."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_token_table
            
            tokens = [
                {
                    'jti': 'test-jti-1',
                    'issued_to': 'client-1',
                    'issuer': 'api-1',
                    'token_type': 'access',
                    'is_active': True
                }
            ]
            
            # No debería lanzar excepción
            print_token_table(tokens)
        except Exception as e:
            pytest.fail(f"print_token_table test failed: {e}")
    
    def test_print_token_details(self):
        """Test print_token_details."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_token_details
            
            token = {
                'jti': 'test-jti',
                'issued_to': 'test-client',
                'issuer': 'test-service',
                'token_type': 'access',
                'is_active': True,
                'issued_at': '2025-01-01T00:00:00Z'
            }
            
            # No debería lanzar excepción
            print_token_details(token)
        except Exception as e:
            pytest.fail(f"print_token_details test failed: {e}")
    
    def test_print_statistics(self):
        """Test print_statistics."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_statistics
            
            stats = {
                'registry': {
                    'total_tokens': 5,
                    'active_tokens': 3,
                    'inactive_tokens': 2
                },
                'blacklist': {
                    'revoked_count': 2
                }
            }
            
            # No debería lanzar excepción
            print_statistics(stats)
        except Exception as e:
            pytest.fail(f"print_statistics test failed: {e}")
    
    def test_print_token_table_empty(self):
        """Test print_token_table with empty tokens list (lines 250-251)."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_token_table
            
            # Test with empty list to cover lines 250-251
            print_token_table([])
        except Exception as e:
            pytest.fail(f"print_token_table empty test failed: {e}")
    
    def test_print_statistics_with_issuers_subjects(self):
        """Test print_statistics with issuers and subjects (lines 320, 323)."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_statistics
            
            stats = {
                'registry': {
                    'total_tokens': 5,
                    'active_tokens': 3,
                    'inactive_tokens': 2,
                    'issuers': ['service-1', 'service-2'],
                    'subjects': ['client-1', 'client-2']
                },
                'blacklist': {
                    'revoked_count': 2
                }
            }
            
            # Test with issuers and subjects to cover lines 320, 323
            print_statistics(stats)
        except Exception as e:
            pytest.fail(f"print_statistics with issuers/subjects test failed: {e}")
    
    def test_generate_command_logic(self):
        """Test generate command logic by testing the internal function directly."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import generate_token
            
            # Test the generate_token function directly
            with patch('scripts.token_cli.jwt.encode') as mock_encode:
                with patch('scripts.token_cli.get_jwt_secret') as mock_secret:
                    with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                        mock_registry = MagicMock()
                        mock_registry_class.return_value = mock_registry
                        mock_secret.return_value = "test-secret"
                        mock_encode.return_value = "test-jwt-token"
                        
                        mock_registry.register_token.return_value = {
                            'jti': 'test-jti',
                            'issued_to': 'test-client',
                            'issuer': 'test-service',
                            'token': 'test-jwt-token',
                            'issued_at': '2025-01-01T00:00:00Z'
                        }
                        
                        result = generate_token(
                            issued_to="test-client",
                            issuer="test-service",
                            token_type="access",
                            notes="Test token"
                        )
                        
                        # Check that the result has the expected structure
                        assert 'jti' in result
                        assert 'issued_to' in result
                        assert 'issuer' in result
                        assert 'token' in result
                        assert result['issued_to'] == 'test-client'
                        assert result['issuer'] == 'test-service'
                        assert result['token'] == 'test-jwt-token'
                        mock_registry.register_token.assert_called_once()
        except Exception as e:
            pytest.fail(f"generate command logic test failed: {e}")
    
    def test_list_command_logic(self):
        """Test list command logic by testing the internal function directly."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import list_tokens
            
            with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                mock_registry = MagicMock()
                mock_registry_class.return_value = mock_registry
                mock_registry.search_tokens.return_value = [
                    {
                        'jti': 'test-jti-1',
                        'issued_to': 'client-1',
                        'issuer': 'service-1',
                        'token_type': 'access',
                        'is_active': True
                    }
                ]
                
                result = list_tokens(issued_to="client-1", issuer="service-1", active_only=True)
                
                assert len(result) == 1
                assert result[0]['jti'] == 'test-jti-1'
                mock_registry.search_tokens.assert_called_once_with(
                    issued_to="client-1",
                    issuer="service-1",
                    is_active=True
                )
        except Exception as e:
            pytest.fail(f"list command logic test failed: {e}")
    
    def test_query_command_logic(self):
        """Test query command logic by testing the internal function directly."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import query_token
            
            with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                mock_registry = MagicMock()
                mock_registry_class.return_value = mock_registry
                mock_registry.get_by_jti.return_value = {
                    'jti': 'test-jti',
                    'issued_to': 'test-client',
                    'issuer': 'test-service',
                    'is_active': True
                }
                
                result = query_token('test-jti')
                
                assert result is not None
                assert result['jti'] == 'test-jti'
                mock_registry.get_by_jti.assert_called_once_with('test-jti')
        except Exception as e:
            pytest.fail(f"query command logic test failed: {e}")
    
    def test_revoke_command_logic(self):
        """Test revoke command logic by testing the internal function directly."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import revoke_token
            
            with patch('scripts.token_cli.get_blacklist') as mock_get_blacklist:
                with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                    mock_blacklist = MagicMock()
                    mock_get_blacklist.return_value = mock_blacklist
                    mock_blacklist.revoke.return_value = True
                    
                    mock_registry = MagicMock()
                    mock_registry_class.return_value = mock_registry
                    mock_registry.get_by_jti.return_value = {
                        'jti': 'test-jti',
                        'issued_to': 'test-client'
                    }
                    
                    result = revoke_token(
                        jti='test-jti',
                        reason='Test revocation',
                        revoked_by='admin'
                    )
                    
                    assert result is True
                    mock_blacklist.revoke.assert_called_once()
        except Exception as e:
            pytest.fail(f"revoke command logic test failed: {e}")
    
    def test_stats_command_logic(self):
        """Test stats command logic by testing the internal function directly."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import get_statistics
            
            with patch('scripts.token_cli.get_blacklist') as mock_get_blacklist:
                with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                    mock_blacklist = MagicMock()
                    mock_get_blacklist.return_value = mock_blacklist
                    mock_blacklist.count_revoked.return_value = 2
                    mock_blacklist.get_revocations.return_value = [
                        {'jti': 'revoked-1', 'reason': 'Security breach'}
                    ]
                    
                    mock_registry = MagicMock()
                    mock_registry_class.return_value = mock_registry
                    mock_registry.get_statistics.return_value = {
                        'total_tokens': 5,
                        'active_tokens': 3,
                        'inactive_tokens': 2,
                        'unique_issuers': 2,
                        'unique_subjects': 3
                    }
                    
                    result = get_statistics()
                    
                    assert 'registry' in result
                    assert 'blacklist' in result
                    assert result['registry']['total_tokens'] == 5
                    assert result['blacklist']['revoked_count'] == 2
        except Exception as e:
            pytest.fail(f"stats command logic test failed: {e}")
    
    def test_generate_token_with_fresh_flag(self):
        """Test generate_token with fresh flag."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import generate_token
            
            with patch('scripts.token_cli.jwt.encode') as mock_encode:
                with patch('scripts.token_cli.get_jwt_secret') as mock_secret:
                    with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                        mock_registry = MagicMock()
                        mock_registry_class.return_value = mock_registry
                        mock_secret.return_value = "test-secret"
                        mock_encode.return_value = "test-jwt-token"
                        
                        mock_registry.register_token.return_value = {
                            'jti': 'test-jti',
                            'issued_to': 'test-client',
                            'issuer': 'test-service',
                            'token': 'test-jwt-token',
                            'issued_at': '2025-01-01T00:00:00Z'
                        }
                        
                        result = generate_token(
                            issued_to="test-client",
                            issuer="test-service",
                            token_type="access",
                            notes="Test token",
                            fresh=True
                        )
                        
                        assert result['issued_to'] == 'test-client'
                        assert result['issuer'] == 'test-service'
                        mock_registry.register_token.assert_called_once()
        except Exception as e:
            pytest.fail(f"generate_token with fresh flag test failed: {e}")
    
    def test_list_tokens_with_filters(self):
        """Test list_tokens with different filter combinations."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import list_tokens
            
            with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                mock_registry = MagicMock()
                mock_registry_class.return_value = mock_registry
                mock_registry.search_tokens.return_value = [
                    {
                        'jti': 'test-jti-1',
                        'issued_to': 'client-1',
                        'issuer': 'service-1',
                        'token_type': 'access',
                        'is_active': True
                    }
                ]
                
                # Test with issued_to filter
                result1 = list_tokens(issued_to="client-1")
                assert len(result1) == 1
                
                # Test with issuer filter
                result2 = list_tokens(issuer="service-1")
                assert len(result2) == 1
                
                # Test with both filters
                result3 = list_tokens(issued_to="client-1", issuer="service-1")
                assert len(result3) == 1
                
                # Test with active_only
                result4 = list_tokens(active_only=True)
                assert len(result4) == 1
                
                mock_registry.search_tokens.assert_called()
        except Exception as e:
            pytest.fail(f"list_tokens with filters test failed: {e}")
    
    def test_query_token_not_found(self):
        """Test query_token when token is not found."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import query_token
            
            with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                mock_registry = MagicMock()
                mock_registry_class.return_value = mock_registry
                mock_registry.get_by_jti.return_value = None
                
                result = query_token('nonexistent-jti')
                
                assert result is None
                mock_registry.get_by_jti.assert_called_once_with('nonexistent-jti')
        except Exception as e:
            pytest.fail(f"query_token not found test failed: {e}")
    
    def test_query_token_with_revoked_check(self):
        """Test query_token with revoked token check."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import query_token
            
            with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                with patch('scripts.token_cli.get_blacklist') as mock_get_blacklist:
                    mock_registry = MagicMock()
                    mock_registry_class.return_value = mock_registry
                    mock_registry.get_by_jti.return_value = {
                        'jti': 'test-jti',
                        'issued_to': 'test-client',
                        'issuer': 'test-service',
                        'is_active': True
                    }
                    
                    mock_blacklist = MagicMock()
                    mock_get_blacklist.return_value = mock_blacklist
                    mock_blacklist.is_revoked.return_value = True
                    
                    result = query_token('test-jti')
                    
                    assert result is not None
                    assert result['is_revoked'] is True
                    mock_blacklist.is_revoked.assert_called_once_with('test-jti')
        except Exception as e:
            pytest.fail(f"query_token with revoked check test failed: {e}")
    
    def test_revoke_token_without_registry_record(self):
        """Test revoke_token when token is not in registry."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import revoke_token
            
            with patch('scripts.token_cli.get_blacklist') as mock_get_blacklist:
                with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                    mock_blacklist = MagicMock()
                    mock_get_blacklist.return_value = mock_blacklist
                    mock_blacklist.revoke.return_value = True
                    
                    mock_registry = MagicMock()
                    mock_registry_class.return_value = mock_registry
                    mock_registry.get_by_jti.return_value = None
                    
                    result = revoke_token(
                        jti='test-jti',
                        reason='Test revocation',
                        revoked_by='admin'
                    )
                    
                    assert result is True
                    mock_blacklist.revoke.assert_called_once_with(
                        jti='test-jti',
                        reason='Test revocation',
                        issued_to=None,
                        revoked_by='admin'
                    )
        except Exception as e:
            pytest.fail(f"revoke_token without registry record test failed: {e}")
    
    def test_get_jwt_secret_missing(self):
        """Test get_jwt_secret when JWT_SECRET_KEY is missing."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import get_jwt_secret
            
            with patch.dict('os.environ', {}, clear=True):
                with pytest.raises(ValueError, match="JWT_SECRET_KEY not found"):
                    get_jwt_secret()
        except Exception as e:
            pytest.fail(f"get_jwt_secret missing test failed: {e}")
    
    def test_get_jwt_secret_success(self):
        """Test get_jwt_secret when JWT_SECRET_KEY is present."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import get_jwt_secret
            
            with patch.dict('os.environ', {'JWT_SECRET_KEY': 'test-secret'}):
                result = get_jwt_secret()
                assert result == 'test-secret'
        except Exception as e:
            pytest.fail(f"get_jwt_secret success test failed: {e}")
    
    def test_print_token_table_with_tokens(self):
        """Test print_token_table with actual tokens."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_token_table
            
            tokens = [
                {
                    'jti': 'test-jti-1',
                    'issued_to': 'client-1',
                    'issuer': 'service-1',
                    'token_type': 'access',
                    'is_active': True
                },
                {
                    'jti': 'test-jti-2',
                    'issued_to': 'client-2',
                    'issuer': 'service-2',
                    'token_type': 'refresh',
                    'is_active': False
                }
            ]
            
            with patch('click.echo') as mock_echo:
                print_token_table(tokens)
                assert mock_echo.call_count >= 4  # Header, separator, 2 tokens, total
        except Exception as e:
            pytest.fail(f"print_token_table with tokens test failed: {e}")
    
    def test_print_token_details_complete(self):
        """Test print_token_details with complete token data."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_token_details
            
            token = {
                'jti': 'test-jti',
                'issued_to': 'test-client',
                'issuer': 'test-service',
                'token_type': 'access',
                'algorithm': 'HS256',
                'issued_at': '2025-01-01T00:00:00Z',
                'not_before': '2025-01-01T00:00:00Z',
                'expires_at': '2025-01-02T00:00:00Z',
                'is_active': True,
                'is_revoked': False,
                'secret_key_hash': 'hash123',
                'notes': 'Test token',
                'token': 'jwt-token-here'
            }
            
            with patch('click.echo') as mock_echo:
                print_token_details(token)
                assert mock_echo.call_count >= 12  # Multiple echo calls for all fields
        except Exception as e:
            pytest.fail(f"print_token_details complete test failed: {e}")
    
    def test_print_statistics_complete(self):
        """Test print_statistics with complete statistics."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import print_statistics
            
            stats = {
                'registry': {
                    'total_tokens': 10,
                    'active_tokens': 8,
                    'inactive_tokens': 2,
                    'unique_issuers': 3,
                    'unique_subjects': 5,
                    'issuers': ['service-1', 'service-2', 'service-3'],
                    'subjects': ['client-1', 'client-2', 'client-3', 'client-4', 'client-5']
                },
                'blacklist': {
                    'revoked_count': 2,
                    'revocations': [
                        {'jti': 'revoked-1', 'reason': 'Security breach'},
                        {'jti': 'revoked-2', 'reason': 'Expired'}
                    ]
                }
            }
            
            with patch('click.echo') as mock_echo:
                print_statistics(stats)
                assert mock_echo.call_count >= 10  # Multiple echo calls for all sections
        except Exception as e:
            pytest.fail(f"print_statistics complete test failed: {e}")
    
    def test_generate_token_with_all_parameters(self):
        """Test generate_token with all parameters to increase coverage."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import generate_token
            
            with patch('scripts.token_cli.jwt.encode') as mock_encode:
                with patch('scripts.token_cli.get_jwt_secret') as mock_secret:
                    with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                        mock_registry = MagicMock()
                        mock_registry_class.return_value = mock_registry
                        mock_secret.return_value = "test-secret"
                        mock_encode.return_value = "test-jwt-token"
                        
                        mock_registry.register_token.return_value = {
                            'jti': 'test-jti',
                            'issued_to': 'test-client',
                            'issuer': 'test-service',
                            'token': 'test-jwt-token',
                            'issued_at': '2025-01-01T00:00:00Z'
                        }
                        
                        # Test with all parameters including fresh=True
                        result = generate_token(
                            issued_to="test-client",
                            issuer="test-service",
                            token_type="refresh",
                            notes="Test token with all params",
                            fresh=True
                        )
                        
                        assert result['issued_to'] == 'test-client'
                        assert result['issuer'] == 'test-service'
                        assert result['token'] == 'test-jwt-token'
                        mock_registry.register_token.assert_called_once()
        except Exception as e:
            pytest.fail(f"generate_token with all parameters test failed: {e}")
    
    def test_list_tokens_all_combinations(self):
        """Test list_tokens with all parameter combinations."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import list_tokens
            
            with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                mock_registry = MagicMock()
                mock_registry_class.return_value = mock_registry
                mock_registry.search_tokens.return_value = []
                
                # Test all combinations
                list_tokens()  # No parameters
                list_tokens(issued_to="client-1")  # Only issued_to
                list_tokens(issuer="service-1")  # Only issuer
                list_tokens(active_only=True)  # Only active_only
                list_tokens(issued_to="client-1", issuer="service-1")  # Both filters
                list_tokens(issued_to="client-1", active_only=True)  # issued_to + active_only
                list_tokens(issuer="service-1", active_only=True)  # issuer + active_only
                list_tokens(issued_to="client-1", issuer="service-1", active_only=True)  # All parameters
                
                # Verify search_tokens was called multiple times
                assert mock_registry.search_tokens.call_count >= 8
        except Exception as e:
            pytest.fail(f"list_tokens all combinations test failed: {e}")
    
    def test_query_token_edge_cases(self):
        """Test query_token edge cases."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import query_token
            
            with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                with patch('scripts.token_cli.get_blacklist') as mock_get_blacklist:
                    mock_registry = MagicMock()
                    mock_registry_class.return_value = mock_registry
                    
                    mock_blacklist = MagicMock()
                    mock_get_blacklist.return_value = mock_blacklist
                    
                    # Test with token found and not revoked
                    mock_registry.get_by_jti.return_value = {
                        'jti': 'test-jti',
                        'issued_to': 'test-client',
                        'issuer': 'test-service',
                        'is_active': True
                    }
                    mock_blacklist.is_revoked.return_value = False
                    
                    result = query_token('test-jti')
                    assert result is not None
                    assert result['is_revoked'] is False
                    
                    # Test with token found and revoked
                    mock_blacklist.is_revoked.return_value = True
                    result = query_token('test-jti')
                    assert result is not None
                    assert result['is_revoked'] is True
                    
                    # Test with token not found
                    mock_registry.get_by_jti.return_value = None
                    result = query_token('nonexistent-jti')
                    assert result is None
        except Exception as e:
            pytest.fail(f"query_token edge cases test failed: {e}")
    
    def test_revoke_token_simple(self):
        """Test revoke_token simple case."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import revoke_token
            
            with patch('scripts.token_cli.get_blacklist') as mock_get_blacklist:
                with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                    mock_blacklist = MagicMock()
                    mock_get_blacklist.return_value = mock_blacklist
                    
                    mock_registry = MagicMock()
                    mock_registry_class.return_value = mock_registry
                    
                    # Test with token found in registry
                    mock_registry.get_by_jti.return_value = {
                        'jti': 'test-jti',
                        'issued_to': 'test-client'
                    }
                    mock_blacklist.revoke.return_value = True
                    
                    result = revoke_token(
                        jti='test-jti',
                        reason='Test revocation',
                        revoked_by='admin'
                    )
                    
                    assert result is True
                    mock_registry.mark_inactive.assert_called_once_with('test-jti')
                    mock_blacklist.revoke.assert_called_once()
        except Exception as e:
            pytest.fail(f"revoke_token simple test failed: {e}")
    
    def test_get_statistics_comprehensive(self):
        """Test get_statistics comprehensive coverage."""
        try:
            import sys
            sys.path.insert(0, '/backend')
            from scripts.token_cli import get_statistics
            
            with patch('scripts.token_cli.get_blacklist') as mock_get_blacklist:
                with patch('scripts.token_cli.TokenRegistry') as mock_registry_class:
                    mock_blacklist = MagicMock()
                    mock_get_blacklist.return_value = mock_blacklist
                    mock_blacklist.count_revoked.return_value = 3
                    mock_blacklist.get_revocations.return_value = [
                        {'jti': 'revoked-1', 'reason': 'Security breach'},
                        {'jti': 'revoked-2', 'reason': 'Expired'},
                        {'jti': 'revoked-3', 'reason': 'Manual'}
                    ]
                    
                    mock_registry = MagicMock()
                    mock_registry_class.return_value = mock_registry
                    mock_registry.get_statistics.return_value = {
                        'total_tokens': 10,
                        'active_tokens': 7,
                        'inactive_tokens': 3,
                        'unique_issuers': 2,
                        'unique_subjects': 5
                    }
                    
                    result = get_statistics()
                    
                    assert 'registry' in result
                    assert 'blacklist' in result
                    assert result['registry']['total_tokens'] == 10
                    assert result['blacklist']['revoked_count'] == 3
                    assert len(result['blacklist']['revocations']) == 3
                    
                    mock_registry.get_statistics.assert_called_once()
                    mock_blacklist.count_revoked.assert_called_once()
                    mock_blacklist.get_revocations.assert_called_once()
        except Exception as e:
            pytest.fail(f"get_statistics comprehensive test failed: {e}")
    
    
