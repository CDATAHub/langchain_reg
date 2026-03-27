#!/usr/bin/env python3
"""Test CORS and WebSocket configuration"""

import asyncio
import websockets
import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/ws/"

async def test_websocket():
    """Test WebSocket connection"""
    print("\n=== Testing WebSocket Connection ===")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket connected successfully")

            # Send a ping
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("✅ Sent ping message")

            # Receive response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            print(f"✅ Received response: {response_data}")

            if response_data.get("type") == "connected":
                print("✅ WebSocket connection is working properly!")
                return True
            elif response_data.get("type") == "pong":
                print("✅ Ping/pong successful")
                return True

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    print("\n=== Testing CORS Headers ===")
    try:
        # Test OPTIONS request (preflight)
        response = requests.options(
            f"{API_URL}/api/documents",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )

        print(f"✅ OPTIONS request status: {response.status_code}")

        # Check CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
        }

        print("\nCORS Headers:")
        for key, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")

        # Test GET request
        response = requests.get(
            f"{API_URL}/api/documents",
            headers={"Origin": "http://localhost:5173"}
        )

        print(f"\n✅ GET request status: {response.status_code}")
        print(f"✅ Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")

        return all(cors_headers.values())

    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"✅ Health check status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def main():
    print("Testing LangChain + LlamaIndex Backend")
    print("=" * 50)

    # Test health
    health_ok = test_health()

    # Test CORS
    cors_ok = test_cors()

    # Test WebSocket
    ws_ok = await test_websocket()

    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Health Check:    {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"  CORS:           {'✅ PASS' if cors_ok else '❌ FAIL'}")
    print(f"  WebSocket:       {'✅ PASS' if ws_ok else '❌ FAIL'}")

    if all([health_ok, cors_ok, ws_ok]):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import websockets
        import requests
    except ImportError as e:
        print(f"Missing required packages: {e}")
        print("Please install: pip install websockets requests")
        exit(1)

    asyncio.run(main())
