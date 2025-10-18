"""
Pytest configuration for the project.

This file contains global fixtures and configuration for all tests.
"""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def disable_hot_reload():
    """
    Automatically disable hot-reload for all tests to prevent logging issues.
    
    This fixture runs before every test and patches the _start_hot_reload method
    to prevent the creation of file system observers that cause logging errors.
    """
    with patch('core.token_blacklist.TokenBlacklist._start_hot_reload'):
        yield


@pytest.fixture(autouse=True)
def disable_logging_errors():
    """
    Automatically disable problematic logging during tests.
    
    This fixture prevents logging errors from appearing in test output.
    """
    with patch('core.token_blacklist.logs_config.logger.error'):
        with patch('core.token_blacklist.logs_config.logger.warning'):
            yield
