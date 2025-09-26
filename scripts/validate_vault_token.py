#!/usr/bin/env python3
"""
Token validation and lifecycle management script for workflow token validation.
"""
import os
import json
from datetime import datetime, timedelta, timezone


def validate_token_ttl():
    """Validate the TTL of the provided token."""
    token = os.getenv('VAULT_TOKEN')
    if not token:
        raise ValueError("VAULT_TOKEN environment variable is required")

    # Use vault CLI to lookup token
    result = os.popen('vault token lookup -format=json').read()
    data = json.loads(result)

    ttl = data['data']['ttl']
    creation_time = datetime.fromtimestamp(data['data']['creation_time'])
    expire_time = creation_time + timedelta(seconds=ttl)

    now = datetime.now(timezone.utc)
    remaining = expire_time - now

    print("\n=== Vault Token Validation ===")
    print(f"Current time: {now.isoformat()}")
    print(f"Token expires: {expire_time.isoformat()}")
    print(f"Remaining TTL: {remaining.total_seconds():.0f} seconds")

    if remaining.total_seconds() <= 0:
        raise Exception("Token has expired!")
    elif remaining.total_seconds() < 3600:  # Less than 1 hour
        print("\n⚠️ Warning: Token expires in less than 1 hour!")
    else:
        print(f"\n✅ Token valid for {remaining.total_seconds() / 3600:.1f} more hours")

    return {
        'current_time': now.isoformat(),
        'expiry_time': expire_time.isoformat(),
        'ttl_seconds': remaining.total_seconds()
    }


if __name__ == '__main__':
    try:
        metadata = validate_token_ttl()
        with open('token_validation.json', 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
