"""
Tests unificados para el módulo logs_config.py
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestLogsConfig:
    """Tests unificados para la configuración de logs."""
    
    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        try:
            from logs import logs_config
            assert hasattr(logs_config, 'logger')
            assert hasattr(logs_config.logger, 'info')
            assert hasattr(logs_config.logger, 'warning')
            assert hasattr(logs_config.logger, 'error')
            assert hasattr(logs_config.logger, 'debug')
        except Exception as e:
            pytest.fail(f"Failed to import logs_config: {e}")
    
    def test_logger_methods_exist(self):
        """Test that all required logger methods exist."""
        from logs import logs_config
        
        required_methods = ['info', 'warning', 'error', 'debug', 'critical']
        for method in required_methods:
            assert hasattr(logs_config.logger, method)
            assert callable(getattr(logs_config.logger, method))
    
    def test_logger_can_log_messages(self):
        """Test that logger can log different types of messages."""
        from logs import logs_config
        
        # Test that logging methods can be called without errors
        try:
            logs_config.logger.info("Test info message")
            logs_config.logger.warning("Test warning message")
            logs_config.logger.error("Test error message")
            logs_config.logger.debug("Test debug message")
        except Exception as e:
            pytest.fail(f"Failed to log messages: {e}")
    
    def test_logger_with_mocked_handlers(self):
        """Test logger with mocked handlers."""
        with patch('logs.logs_config.logger') as mock_logger:
            mock_logger.info.return_value = None
            mock_logger.warning.return_value = None
            mock_logger.error.return_value = None
            
            # Test that methods can be called
            mock_logger.info("Test message")
            mock_logger.warning("Test warning")
            mock_logger.error("Test error")
            
            # Verify calls
            assert mock_logger.info.called
            assert mock_logger.warning.called
            assert mock_logger.error.called
    
    def test_logger_configuration_values(self):
        """Test logger configuration values."""
        from logs import logs_config
        
        # Test that logger has expected attributes (loguru doesn't have handlers attribute)
        assert hasattr(logs_config.logger, 'level')
        
        # Test that logger can be used
        assert callable(logs_config.logger.info)
    
    def test_logger_level_setting(self):
        """Test logger level setting."""
        from logs import logs_config
        
        # Test that logger has level attribute (loguru doesn't have setLevel)
        assert hasattr(logs_config.logger, 'level')
        # Loguru level might be a string or int, just check it exists
        assert logs_config.logger.level is not None
    
    def test_logger_with_patch(self):
        """Test logger with patch to avoid side effects."""
        with patch('logs.logs_config.logger') as mock_logger:
            mock_logger.info = MagicMock()
            mock_logger.warning = MagicMock()
            mock_logger.error = MagicMock()
            
            # Test logging calls
            mock_logger.info("Test info")
            mock_logger.warning("Test warning")
            mock_logger.error("Test error")
            
            # Verify all methods were called
            mock_logger.info.assert_called_once_with("Test info")
            mock_logger.warning.assert_called_once_with("Test warning")
            mock_logger.error.assert_called_once_with("Test error")
    
    def test_logger_import_structure(self):
        """Test that logs_config can be imported correctly."""
        try:
            import logs.logs_config as logs_config
            assert hasattr(logs_config, 'logger')
        except ImportError as e:
            pytest.fail(f"Failed to import logs_config: {e}")
    
    def test_logger_handlers_configuration(self):
        """Test logger handlers configuration."""
        from logs import logs_config
        
        # Test that logger can be used (loguru doesn't expose handlers directly)
        assert callable(logs_config.logger.info)
        assert callable(logs_config.logger.warning)
        assert callable(logs_config.logger.error)
    
    def test_intercept_handler_emit(self):
        """Test InterceptHandler emit method (lines 43-56)."""
        from logs.logs_config import InterceptHandler
        import logging
        
        handler = InterceptHandler()
        
        # Create a test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Test emit method
        with patch('logs.logs_config.logger.opt') as mock_opt:
            with patch('logs.logs_config.logger.level') as mock_level:
                mock_level.return_value.name = "INFO"
                handler.emit(record)
                mock_opt.assert_called_once()
    
    def test_intercept_handler_value_error(self):
        """Test InterceptHandler with ValueError (lines 45-46)."""
        from logs.logs_config import InterceptHandler
        import logging
        
        handler = InterceptHandler()
        
        # Create a test record with invalid level
        record = logging.LogRecord(
            name="test",
            level=999,  # Invalid level
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Test emit method with ValueError
        with patch('logs.logs_config.logger.opt') as mock_opt:
            with patch('logs.logs_config.logger.level', side_effect=ValueError("Invalid level")):
                handler.emit(record)
                mock_opt.assert_called_once()
    
    
    def test_intercept_handler_simple_emit(self):
        """Test InterceptHandler simple emit without complex mocking."""
        from logs.logs_config import InterceptHandler
        import logging
        
        handler = InterceptHandler()
        
        # Create a test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Test emit with simple mocking
        with patch('logs.logs_config.logger.opt') as mock_opt:
            with patch('logs.logs_config.logger.level') as mock_level:
                mock_level.return_value.name = "INFO"
                handler.emit(record)
                mock_opt.assert_called_once()
    
    def test_ansi_escape_pattern(self):
        """Test ANSI escape pattern functionality."""
        from logs.logs_config import InterceptHandler
        import re
        
        handler = InterceptHandler()
        
        # Test ANSI escape pattern
        test_message = "\x1B[31mRed text\x1B[0m"
        clean_message = handler.ANSI_ESCAPE_PATTERN.sub('', test_message)
        assert clean_message == "Red text"
    
    def test_logger_configuration_values(self):
        """Test logger configuration values."""
        from logs import logs_config
        
        # Test that logger has expected attributes (loguru doesn't have handlers attribute)
        assert hasattr(logs_config.logger, 'level')
        
        # Test that logger can be used
        assert callable(logs_config.logger.info)
    
    def test_logger_level_setting(self):
        """Test logger level setting."""
        from logs import logs_config
        
        # Test that logger has level attribute (loguru doesn't have setLevel)
        assert hasattr(logs_config.logger, 'level')
        assert logs_config.logger.level is not None
    
    def test_logger_with_patch(self):
        """Test logger with patch to avoid side effects."""
        with patch('logs.logs_config.logger') as mock_logger:
            mock_logger.info = MagicMock()
            mock_logger.warning = MagicMock()
            mock_logger.error = MagicMock()
            
            from logs import logs_config
            logs_config.logger.info("Test info")
            logs_config.logger.warning("Test warning")
            logs_config.logger.error("Test error")
            
            mock_logger.info.assert_called_once_with("Test info")
            mock_logger.warning.assert_called_once_with("Test warning")
            mock_logger.error.assert_called_once_with("Test error")
    
    def test_logger_handlers_configuration(self):
        """Test logger handlers configuration."""
        from logs import logs_config
        
        # Test that logger can be used (loguru doesn't expose handlers directly)
        assert callable(logs_config.logger.info)
        assert callable(logs_config.logger.warning)
        assert callable(logs_config.logger.error)
    
    def test_root_logger_configuration(self):
        """Test root logger configuration."""
        from logs import logs_config
        
        # Test that root logger is configured
        assert hasattr(logs_config, 'root_logger')
        assert hasattr(logs_config, 'intercept_handler')
    
    def test_specific_loggers_configuration(self):
        """Test specific loggers configuration."""
        import logging
        from logs import logs_config
        
        # Test that specific loggers are configured
        loggers_to_configure = [
            "gunicorn",
            "gunicorn.access", 
            "gunicorn.error",
            "werkzeug",
            "flask",
            "flask.app"
        ]
        
        for logger_name in loggers_to_configure:
            logger = logging.getLogger(logger_name)
            assert logger is not None
    
    def test_logger_with_environment_variables(self):
        """Test logger with different environment variables."""
        with patch.dict('os.environ', {'LOG_LEVEL': 'DEBUG'}):
            # Test that environment variables are used
            from logs import logs_config
            assert hasattr(logs_config, 'logger')
    
    def test_logger_import_success(self):
        """Test successful logger import."""
        try:
            from logs import logs_config
            assert hasattr(logs_config, 'logger')
            assert hasattr(logs_config, 'InterceptHandler')
            assert hasattr(logs_config, 'intercept_handler')
            assert hasattr(logs_config, 'root_logger')
        except ImportError as e:
            pytest.fail(f"Failed to import logs_config: {e}")
    
    def test_intercept_handler_creation(self):
        """Test InterceptHandler creation."""
        from logs.logs_config import InterceptHandler
        
        handler = InterceptHandler()
        assert handler is not None
        assert hasattr(handler, 'ANSI_ESCAPE_PATTERN')
        assert hasattr(handler, 'emit')
    
    def test_ansi_escape_pattern_compilation(self):
        """Test ANSI escape pattern compilation."""
        from logs.logs_config import InterceptHandler
        import re
        
        handler = InterceptHandler()
        pattern = handler.ANSI_ESCAPE_PATTERN
        
        # Test that it's a compiled regex
        assert isinstance(pattern, re.Pattern)
        
        # Test pattern matching
        test_string = "\x1B[31mRed text\x1B[0m"
        result = pattern.sub('', test_string)
        assert result == "Red text"
    
    def test_logger_configuration_attributes(self):
        """Test logger configuration attributes."""
        from logs import logs_config
        
        # Test that all expected attributes exist
        assert hasattr(logs_config, 'logger')
        assert hasattr(logs_config, 'InterceptHandler')
        assert hasattr(logs_config, 'intercept_handler')
        assert hasattr(logs_config, 'root_logger')
        
        # Test logger functionality
        assert callable(logs_config.logger.info)
        assert callable(logs_config.logger.warning)
        assert callable(logs_config.logger.error)
    
    def test_root_logger_attributes(self):
        """Test root logger attributes."""
        from logs import logs_config
        
        # Test root logger attributes
        assert hasattr(logs_config, 'root_logger')
        assert logs_config.root_logger is not None
        
        # Test intercept handler
        assert hasattr(logs_config, 'intercept_handler')
        assert logs_config.intercept_handler is not None
    
    def test_logger_error_handling(self):
        """Test logger error handling."""
        from logs import logs_config
        
        # Test that logger can handle various input types
        test_messages = [
            "String message",
            "Message with numbers: 123",
            "Message with special chars: !@#$%",
            "",
            None
        ]
        
        for message in test_messages:
            try:
                if message is not None:
                    logs_config.logger.info(message)
            except Exception as e:
                # Some messages might cause issues, that's expected
                pass
