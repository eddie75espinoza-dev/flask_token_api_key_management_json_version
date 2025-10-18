"""
Token Blacklist Management System with Hot-Reload Support.

This module provides functionality to manage revoked JWT tokens using a JSON file
as storage. It includes hot-reload capabilities to detect changes without restarting
the application.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from logs import logs_config


class BlacklistFileHandler(FileSystemEventHandler):
    """
    File system event handler for blacklist file changes.
    
    Triggers reload when the blacklist file is modified.
    """
    
    def __init__(self, blacklist_instance: 'TokenBlacklist') -> None:
        """
        Initialize the file handler.
        
        Args:
            blacklist_instance: TokenBlacklist instance to reload on changes.
        """
        self.blacklist = blacklist_instance
        super().__init__()
    
    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Handle file modification events.
        
        Args:
            event: File system event containing modified file info.
        """
        if not event.is_directory and event.src_path == str(self.blacklist.filepath):
            logs_config.logger.info(
                f"Blacklist file modified, reloading: {event.src_path}"
            )
            self.blacklist.load()


class TokenBlacklist:
    """
    Manages revoked JWT tokens using a JSON file as storage.
    
    Features:
    - Load/save revoked JTIs from/to JSON file
    - Check if a token is revoked
    - Add tokens to blacklist
    - Hot-reload on file changes (optional)
    - Thread-safe operations
    
    Attributes:
        filepath: Path to the JSON blacklist file
        _blacklist: Set of revoked JTIs in memory
        _lock: Thread lock for safe concurrent access
        _observer: File system observer for hot-reload
    """
    
    def __init__(
        self, 
        filepath: str = "data/revoked_tokens.json",
        enable_hot_reload: bool = True
    ) -> None:
        """
        Initialize the TokenBlacklist.
        
        Args:
            filepath: Path to JSON file storing revoked tokens.
            enable_hot_reload: Enable automatic reload on file changes.
        """
        self.filepath = Path(filepath)
        self._blacklist: Set[str] = set()
        self._revocations: List[Dict] = []
        self._lock = threading.Lock()
        self._observer: Optional[Observer] = None
        self.enable_hot_reload = enable_hot_reload
        
        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if doesn't exist
        if not self.filepath.exists():
            self._create_initial_file()
        
        # Load existing blacklist
        self.load()
        
        # Start hot-reload if enabled
        if self.enable_hot_reload:
            self._start_hot_reload()
    
    def _create_initial_file(self) -> None:
        """Create initial blacklist file with empty structure."""
        initial_data = {
            "revoked_jtis": [],
            "last_updated": None,
            "revocations": []
        }
        with open(self.filepath, 'w') as f:
            json.dump(initial_data, f, indent=2)
        
        logs_config.logger.info(f"Created initial blacklist file: {self.filepath}")
    
    def load(self) -> None:
        """
        Load blacklist from JSON file.
        
        Thread-safe operation that reloads all revoked JTIs into memory.
        """
        try:
            with self._lock:
                if not self.filepath.exists():
                    logs_config.logger.warning(
                        f"Blacklist file not found: {self.filepath}"
                    )
                    return
                
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    self._blacklist = set(data.get('revoked_jtis', []))
                    self._revocations = data.get('revocations', [])
                
                logs_config.logger.info(
                    f"Loaded {len(self._blacklist)} revoked tokens from blacklist"
                )
        
        except json.JSONDecodeError as error:
            logs_config.logger.error(
                f"Failed to parse blacklist JSON: {error}"
            )
        except Exception as error:
            logs_config.logger.error(
                f"Failed to load blacklist: {error}"
            )
    
    def is_revoked(self, jti: str) -> bool:
        """
        Check if a token (by JTI) is revoked.
        
        Args:
            jti: JWT ID to check.
        
        Returns:
            True if token is revoked, False otherwise.
        """
        with self._lock:
            return jti in self._blacklist
    
    def revoke(
        self, 
        jti: str, 
        reason: str = "Manual revocation",
        issued_to: Optional[str] = None,
        revoked_by: str = "admin"
    ) -> bool:
        """
        Revoke a token by adding its JTI to the blacklist.
        
        Args:
            jti: JWT ID to revoke.
            reason: Reason for revocation.
            issued_to: Original token holder (sub field).
            revoked_by: Who revoked the token.
        
        Returns:
            True if token was revoked, False if already revoked.
        """
        with self._lock:
            if jti in self._blacklist:
                logs_config.logger.warning(f"Token {jti} already revoked")
                return False
            
            self._blacklist.add(jti)
            
            # Add revocation record
            revocation_record = {
                "jti": jti,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "issued_to": issued_to,
                "revoked_by": revoked_by
            }
            self._revocations.append(revocation_record)
            
            self._save()
            
            logs_config.logger.warning(
                f"Token revoked - JTI: {jti}, Reason: {reason}, By: {revoked_by}"
            )
            
            return True
    
    def unrevoke(self, jti: str) -> bool:
        """
        Remove a token from the blacklist (restore access).
        
        Args:
            jti: JWT ID to restore.
        
        Returns:
            True if token was unrevoked, False if not found.
        """
        with self._lock:
            if jti not in self._blacklist:
                logs_config.logger.warning(f"Token {jti} not in blacklist")
                return False
            
            self._blacklist.discard(jti)
            
            # Remove from revocations list
            self._revocations = [
                r for r in self._revocations if r.get('jti') != jti
            ]
            
            self._save()
            
            logs_config.logger.info(f"Token unrevoked - JTI: {jti}")
            
            return True
    
    def get_revocations(self) -> List[Dict]:
        """
        Get list of all revocations with metadata.
        
        Returns:
            List of revocation records.
        """
        with self._lock:
            return self._revocations.copy()
    
    def count_revoked(self) -> int:
        """
        Get count of revoked tokens.
        
        Returns:
            Number of tokens in blacklist.
        """
        with self._lock:
            return len(self._blacklist)
    
    def _save(self) -> None:
        """
        Save blacklist to JSON file.
        
        Private method called after modifications.
        """
        try:
            data = {
                "revoked_jtis": list(self._blacklist),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "revocations": self._revocations
            }
            
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logs_config.logger.debug(f"Blacklist saved to {self.filepath}")
        
        except Exception as error:
            logs_config.logger.error(f"Failed to save blacklist: {error}")
    
    def _start_hot_reload(self) -> None:
        """
        Start file system observer for hot-reload.
        
        Monitors blacklist file for changes and automatically reloads.
        """
        try:
            event_handler = BlacklistFileHandler(self)
            self._observer = Observer()
            self._observer.schedule(
                event_handler, 
                str(self.filepath.parent), 
                recursive=False
            )
            self._observer.start()
            
            logs_config.logger.info(
                f"Hot-reload enabled for blacklist: {self.filepath}"
            )
        
        except Exception as error:
            logs_config.logger.error(
                f"Failed to start hot-reload observer: {error}"
            )
    
    def stop_hot_reload(self) -> None:
        """Stop the file system observer."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logs_config.logger.info("Hot-reload observer stopped")
    
    def __del__(self) -> None:
        """Cleanup observer on deletion."""
        self.stop_hot_reload()


# Global blacklist instance
_blacklist_instance: Optional[TokenBlacklist] = None


def get_blacklist(
    filepath: str = "data/revoked_tokens.json",
    enable_hot_reload: bool = True
) -> TokenBlacklist:
    """
    Get or create global TokenBlacklist instance.
    
    Singleton pattern to ensure single instance across application.
    
    Args:
        filepath: Path to blacklist JSON file.
        enable_hot_reload: Enable hot-reload feature.
    
    Returns:
        Global TokenBlacklist instance.
    """
    global _blacklist_instance
    
    if _blacklist_instance is None:
        _blacklist_instance = TokenBlacklist(
            filepath=filepath,
            enable_hot_reload=enable_hot_reload
        )
    
    return _blacklist_instance

