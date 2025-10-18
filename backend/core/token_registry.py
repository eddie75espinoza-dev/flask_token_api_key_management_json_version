"""
Token Registry System - Versión Ultra Simple Sin Threading

This module provides functionality to register and track all JWT tokens issued
by the application, including metadata for auditing and security purposes.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class TokenRegistry:
    """
    TokenRegistry Ultra Simple - Sin threading para evitar deadlocks.
    
    Para tests: Sin threading
    Para producción: Se puede agregar threading si es necesario
    """
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self._tokens: List[Dict] = []
        self._load()
    
    def _load(self) -> None:
        """Load token registry from JSON file."""
        if not self.filepath.exists():
            self._save()
            return
        
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
                self._tokens = data.get('tokens', [])
        except (json.JSONDecodeError, Exception):
            self._tokens = []
    
    def _save(self) -> None:
        """Save token registry to JSON file."""
        try:
            data = {
                "tokens": self._tokens,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_issued": len(self._tokens)
            }
            
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def register_token(
        self,
        jti: str,
        issued_to: str,
        issuer: str,
        token: str,
        secret_key: str,
        algorithm: str = "HS256",
        issued_at: Optional[datetime] = None,
        not_before: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        token_type: str = "access",
        additional_claims: Optional[Dict] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """Register a newly issued token with full metadata."""
        # Verificar si JTI ya existe
        existing = self.get_by_jti(jti)
        if existing:
            return existing
        
        # Crear token record
        token_record = {
            "jti": jti,
            "issued_to": issued_to,
            "issuer": issuer,
            "token": token,
            "secret_key_hash": self._hash_secret(secret_key),
            "algorithm": algorithm,
            "issued_at": (issued_at or datetime.now(timezone.utc)).isoformat(),
            "not_before": not_before.isoformat() if not_before else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "token_type": token_type,
            "additional_claims": additional_claims or {},
            "notes": notes,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
        
        # Agregar y guardar
        self._tokens.append(token_record)
        self._save()
        
        return token_record
    
    def get_by_jti(self, jti: str) -> Optional[Dict]:
        """Get token record by JTI."""
        for token in self._tokens:
            if token.get('jti') == jti:
                return token.copy()
        return None
    
    def get_by_issued_to(self, issued_to: str) -> List[Dict]:
        """Get all tokens issued to a specific subject."""
        return [token.copy() for token in self._tokens 
               if token.get('issued_to') == issued_to]
    
    def get_by_issuer(self, issuer: str) -> List[Dict]:
        """Get all tokens issued by a specific issuer."""
        return [token.copy() for token in self._tokens 
               if token.get('issuer') == issuer]
    
    def mark_inactive(self, jti: str) -> bool:
        """Mark a token as inactive."""
        for token in self._tokens:
            if token.get('jti') == jti:
                token['is_active'] = False
                token['deactivated_at'] = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False
    
    def get_statistics(self) -> Dict:
        """Get registry statistics."""
        active_tokens = [t for t in self._tokens if t.get('is_active', True)]
        inactive_tokens = [t for t in self._tokens if not t.get('is_active', True)]
        
        issuers = set(t.get('issuer') for t in self._tokens)
        subjects = set(t.get('issued_to') for t in self._tokens)
        
        return {
            "total_tokens": len(self._tokens),
            "active_tokens": len(active_tokens),
            "inactive_tokens": len(inactive_tokens),
            "unique_issuers": len(issuers),
            "unique_subjects": len(subjects)
        }
    
    def search_tokens(
        self,
        issued_to: Optional[str] = None,
        issuer: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict]:
        """Search tokens with filters."""
        results = []
        for token in self._tokens:
            if issued_to and token.get('issued_to') != issued_to:
                continue
            if issuer and token.get('issuer') != issuer:
                continue
            if is_active is not None and token.get('is_active', True) != is_active:
                continue
            results.append(token.copy())
        return results
    
    def count_tokens(self) -> int:
        """Get total number of registered tokens."""
        return len(self._tokens)
    
    def _hash_secret(self, secret: str) -> str:
        """Create a hash of the secret key for storage."""
        import hashlib
        return hashlib.sha256(secret.encode()).hexdigest()[:16]