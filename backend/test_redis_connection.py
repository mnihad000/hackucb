#!/usr/bin/env python
"""
Test Redis Cloud connection
Run this after updating IP allowlist in Redis Cloud
"""

import redis
import sys

# Your Redis Cloud connection
REDIS_URL = "redis://default:ODX3F5VhiFdhPHjagloEyfo0ksl47jbe@lunch-excited-discussion-77297.db.redis.io:13122"

print("=" * 60)
print("Testing Redis Cloud Connection")
print("=" * 60)
print(f"\nConnection URL: {REDIS_URL[:60]}...")

try:
    print("\n1. Creating Redis client...")
    r = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_timeout=10,
        socket_connect_timeout=10
    )

    print("2. Attempting to ping...")
    response = r.ping()
    print(f"✅ PING successful! Response: {response}")

    print("\n3. Testing SET operation...")
    r.set('test_key', 'test_value')
    print("✅ SET successful!")

    print("4. Testing GET operation...")
    value = r.get('test_key')
    print(f"✅ GET successful! Value: {value}")

    print("5. Cleaning up...")
    r.delete('test_key')
    print("✅ DELETE successful!")

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\n✅ Redis Cloud is connected and working!")
    print("\nYou can now run: python setup_redis.py")
    sys.exit(0)

except redis.ConnectionError as e:
    print(f"\n❌ Connection Error: {e}")
    print("\n🔧 Fix this:")
    print("1. Go to: https://redis.io/login")
    print("2. Click your database → Security tab")
    print("3. Add your IP to allowlist (or 0.0.0.0/0 for testing)")
    print("4. Make sure database status is 'Active'")
    sys.exit(1)

except redis.TimeoutError as e:
    print(f"\n❌ Timeout Error: {e}")
    print("\n🔧 Fix this:")
    print("1. Check your internet connection")
    print("2. Verify database is active in Redis Cloud")
    print("3. Check firewall isn't blocking port 13122")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Unexpected Error: {type(e).__name__}: {e}")
    sys.exit(1)
