#!/usr/bin/env python3
"""
JWT Token Management CLI Tool using Click and Flask CLI.

This CLI provides complete token lifecycle management:
- Generate new JWT tokens with registry
- List and query existing tokens
- Revoke tokens (add to blacklist)
- Unrevoke tokens (remove from blacklist)
- View statistics

Usage:
    flask tokens generate --issued-to client-name --issuer api-service
    flask tokens list
    flask tokens query --jti <jti>
    flask tokens revoke --jti <jti> --reason "Security breach"
    flask tokens unrevoke --jti <jti>
    flask tokens stats
"""

import datetime
import json
import uuid
from typing import Optional

import click
import jwt
from flask.cli import AppGroup, with_appcontext

from core.token_blacklist import get_blacklist
from core.token_registry import TokenRegistry

# Create Flask CLI group for tokens
tokens_cli = AppGroup('tokens', help='TOKENS CLI - Tokens Management System')


def get_jwt_secret() -> str:
    """
    Get JWT_SECRET_KEY from environment.
    
    Returns:
        JWT secret key.
    
    Raises:
        ValueError: If JWT_SECRET_KEY not found in environment.
    """
    import os
    secret = os.getenv('JWT_SECRET_KEY')
    if not secret:
        raise ValueError(
            "JWT_SECRET_KEY not found in environment. "
            "Please set it in .env file."
        )
    return secret


def generate_token(
    issued_to: str,
    issuer: str,
    token_type: str = "access",
    notes: Optional[str] = None,
    fresh: bool = False
) -> dict:
    """
    Generate a new JWT token and register it.
    
    Args:
        issued_to: Subject (sub) - who the token is for.
        issuer: Issuer (iss) - who issues the token.
        token_type: Type of token.
        notes: Additional notes.
        fresh: Fresh token flag.
    
    Returns:
        Dictionary with token data and metadata.
    """
    # Get JWT secret from environment
    secret_key = get_jwt_secret()
    
    # Generate unique JTI
    jti = str(uuid.uuid4())
    
    # Create JWT payload
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "fresh": fresh,
        "iat": now,
        "jti": jti,
        "type": token_type,
        "sub": issued_to,
        "nbf": now,
        "iss": issuer,
    }
    
    # Encode JWT token
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    # Register token
    registry = TokenRegistry("data/token_registry.json")
    token_record = registry.register_token(
        jti=jti,
        issued_to=issued_to,
        issuer=issuer,
        token=token,
        secret_key=secret_key,
        algorithm="HS256",
        issued_at=now,
        not_before=now,
        expires_at=None,
        token_type=token_type,
        additional_claims={"fresh": fresh},
        notes=notes
    )
    
    return {
        "token": token,
        "jti": jti,
        "issued_to": issued_to,
        "issuer": issuer,
        "issued_at": now.isoformat(),
        "type": token_type,
        "secret_key_hash": token_record.get('secret_key_hash'),
        "notes": notes
    }


def list_tokens(
    issued_to: Optional[str] = None,
    issuer: Optional[str] = None,
    active_only: bool = False
) -> list:
    """
    List registered tokens with optional filters.
    
    Args:
        issued_to: Filter by subject.
        issuer: Filter by issuer.
        active_only: Show only active tokens.
    
    Returns:
        List of token records.
    """
    registry = TokenRegistry("data/token_registry.json")
    
    if issued_to or issuer:
        tokens = registry.search_tokens(
            issued_to=issued_to,
            issuer=issuer,
            is_active=True if active_only else None
        )
    else:
        tokens = registry.search_tokens(
            is_active=True if active_only else None
        )
    
    return tokens


def query_token(jti: str) -> Optional[dict]:
    """
    Query a specific token by JTI.
    
    Args:
        jti: JWT ID to query.
    
    Returns:
        Token record if found, None otherwise.
    """
    registry = TokenRegistry("data/token_registry.json")
    token_record = registry.get_by_jti(jti)
    
    if token_record:
        # Check if revoked
        blacklist = get_blacklist()
        token_record['is_revoked'] = blacklist.is_revoked(jti)
    
    return token_record


def revoke_token(
    jti: str,
    reason: str = "Manual revocation",
    revoked_by: str = "admin"
) -> bool:
    """
    Revoke a token by JTI.
    
    Args:
        jti: JWT ID to revoke.
        reason: Reason for revocation.
        revoked_by: Who revoked the token.
    
    Returns:
        True if revoked, False if already revoked.
    """
    # Get token info from registry
    registry = TokenRegistry("data/token_registry.json")
    token_record = registry.get_by_jti(jti)
    
    issued_to = None
    if token_record:
        issued_to = token_record.get('issued_to')
        # Mark as inactive in registry
        registry.mark_inactive(jti)
    
    # Add to blacklist
    blacklist = get_blacklist()
    success = blacklist.revoke(
        jti=jti,
        reason=reason,
        issued_to=issued_to,
        revoked_by=revoked_by
    )
    
    return success


# Función unrevoke_token eliminada - no funciona correctamente


def get_statistics() -> dict:
    """
    Get comprehensive statistics about tokens.
    
    Returns:
        Dictionary with statistics.
    """
    registry = TokenRegistry("data/token_registry.json")
    blacklist = get_blacklist()
    
    registry_stats = registry.get_statistics()
    
    return {
        "registry": registry_stats,
        "blacklist": {
            "revoked_count": blacklist.count_revoked(),
            "revocations": blacklist.get_revocations()
        }
    }


def print_token_table(tokens: list) -> None:
    """
    Print tokens in a formatted table.
    
    Args:
        tokens: List of token records.
    """
    if not tokens:
        click.echo("No tokens found.")
        return
    
    click.echo(f"\n{'JTI':<38} {'Issued To':<25} {'Issuer':<20} {'Type':<10} {'Active'}")
    click.echo("-" * 110)
    
    for token in tokens:
        jti = token.get('jti', '')[:36]
        issued_to = token.get('issued_to', 'unknown')[:23]
        issuer = token.get('issuer', 'unknown')[:18]
        token_type = token.get('token_type', 'access')[:8]
        is_active = "Yes" if token.get('is_active', True) else "No"
        
        click.echo(f"{jti:<38} {issued_to:<25} {issuer:<20} {token_type:<10} {is_active}")
    
    click.echo(f"\nTotal: {len(tokens)} token(s)\n")


def print_token_details(token: dict) -> None:
    """
    Print detailed token information.
    
    Args:
        token: Token record.
    """
    click.echo("\n" + "=" * 80)
    click.echo("TOKEN DETAILS")
    click.echo("=" * 80)
    
    click.echo(f"\nJTI:           {token.get('jti')}")
    click.echo(f"Issued To:     {token.get('issued_to')}")
    click.echo(f"Issuer:        {token.get('issuer')}")
    click.echo(f"Type:          {token.get('token_type')}")
    click.echo(f"Algorithm:     {token.get('algorithm')}")
    click.echo(f"Issued At:     {token.get('issued_at')}")
    click.echo(f"Not Before:    {token.get('not_before')}")
    click.echo(f"Expires At:    {token.get('expires_at', 'Never')}")
    click.echo(f"Active:        {'Yes' if token.get('is_active', True) else 'No'}")
    click.echo(f"Revoked:       {'Yes' if token.get('is_revoked', False) else 'No'}")
    click.echo(f"Secret Hash:   {token.get('secret_key_hash')}")
    click.echo(f"Notes:         {token.get('notes', 'None')}")
    click.echo(f"\nToken:\n{token.get('token', 'N/A')}")
    click.echo("\n" + "=" * 80 + "\n")


def print_statistics(stats: dict) -> None:
    """
    Print formatted statistics.
    
    Args:
        stats: Statistics dictionary.
    """
    click.echo("\n" + "=" * 80)
    click.echo("TOKEN STATISTICS")
    click.echo("=" * 80)
    
    registry = stats.get('registry', {})
    blacklist = stats.get('blacklist', {})
    
    click.echo("\nREGISTRY:")
    click.echo(f"  Total Tokens:      {registry.get('total_tokens', 0)}")
    click.echo(f"  Active Tokens:     {registry.get('active_tokens', 0)}")
    click.echo(f"  Inactive Tokens:   {registry.get('inactive_tokens', 0)}")
    click.echo(f"  Unique Issuers:    {registry.get('unique_issuers', 0)}")
    click.echo(f"  Unique Subjects:   {registry.get('unique_subjects', 0)}")
    
    click.echo("\nBLACKLIST:")
    click.echo(f"  Revoked Tokens:    {blacklist.get('revoked_count', 0)}")
    
    if registry.get('issuers'):
        click.echo(f"\nISSUERS: {', '.join(registry.get('issuers', []))}")
    
    if registry.get('subjects'):
        click.echo(f"\nSUBJECTS: {', '.join(registry.get('subjects', []))}")
    
    click.echo("\n" + "=" * 80 + "\n")


@tokens_cli.command()
@click.option('--issued-to', required=True, help='Subject (sub) - who the token is for')
@click.option('--issuer', required=True, help='Issuer (iss) - who issues the token')
@click.option('--type', default='access', help='Token type (default: access)')
@click.option('--notes', help='Additional notes')
@click.option('--fresh', is_flag=True, help='Mark token as fresh')
@click.option('--json', is_flag=True, help='Output as JSON')
@with_appcontext
def generate(issued_to: str, issuer: str, type: str, notes: str, fresh: bool, json: bool):
    """Generate a new JWT token."""
    try:
        result = generate_token(
            issued_to=issued_to,
            issuer=issuer,
            token_type=type,
            notes=notes,
            fresh=fresh
        )
        
        if json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo("\nToken generated successfully!")
            click.echo(f"\nJTI:        {result['jti']}")
            click.echo(f"Issued To:  {result['issued_to']}")
            click.echo(f"Issuer:     {result['issuer']}")
            click.echo(f"Type:       {result['type']}")
            click.echo(f"Issued At:  {result['issued_at']}")
            click.echo(f"\nToken:\n{result['token']}\n")
    
    except Exception as error:
        click.echo(f"\nError: {error}\n", err=True)
        raise click.Abort()


@tokens_cli.command()
@click.option('--issued-to', help='Filter by subject')
@click.option('--issuer', help='Filter by issuer')
@click.option('--active-only', is_flag=True, help='Show only active tokens')
@click.option('--json', is_flag=True, help='Output as JSON')
@with_appcontext
def list(issued_to: str, issuer: str, active_only: bool, json: bool):
    """List registered tokens."""
    try:
        tokens = list_tokens(
            issued_to=issued_to,
            issuer=issuer,
            active_only=active_only
        )
        
        if json:
            import json
            click.echo(json.dumps(tokens, indent=2))
        else:
            print_token_table(tokens)
    
    except Exception as error:
        click.echo(f"\nError: {error}\n", err=True)
        raise click.Abort()


@tokens_cli.command()
@click.option('--jti', required=True, help='JWT ID to query')
@click.option('--json', is_flag=True, help='Output as JSON')
@with_appcontext
def query(jti: str, json: bool):
    """Query a specific token."""
    try:
        token = query_token(jti)
        
        if not token:
            click.echo(f"\nToken not found: {jti}\n", err=True)
            raise click.Abort()
        
        if json:
            import json
            click.echo(json.dumps(token, indent=2))
        else:
            print_token_details(token)
    
    except Exception as error:
        click.echo(f"\nError: {error}\n", err=True)
        raise click.Abort()


@tokens_cli.command()
@click.option('--jti', required=True, help='JWT ID to revoke')
@click.option('--reason', default='Manual revocation', help='Reason for revocation')
@click.option('--revoked-by', default='admin', help='Who is revoking the token')
@with_appcontext
def revoke(jti: str, reason: str, revoked_by: str):
    """Revoke a token."""
    try:
        success = revoke_token(
            jti=jti,
            reason=reason,
            revoked_by=revoked_by
        )
        
        if success:
            click.echo(f"\nToken revoked successfully: {jti}")
            click.echo(f"Reason: {reason}\n")
        else:
            click.echo(f"\nToken already revoked: {jti}\n")
    
    except Exception as error:
        click.echo(f"\nError: {error}\n", err=True)
        raise click.Abort()


# Comando unrevoke eliminado - no funciona correctamente


@tokens_cli.command()
@click.option('--json', is_flag=True, help='Output as JSON')
@with_appcontext
def stats(json: bool):
    """Show token statistics."""
    try:
        stats = get_statistics()
        
        if json:
            import json
            click.echo(json.dumps(stats, indent=2))
        else:
            print_statistics(stats)
    
    except Exception as error:
        click.echo(f"\nError: {error}\n", err=True)
        raise click.Abort()