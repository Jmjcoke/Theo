#!/usr/bin/env python3
"""
Simple test script for Theo API

This script provides basic testing functionality for the API endpoints.
Run this to verify the API is working correctly.
"""

import requests
import sys
import time


def test_api(base_url: str = "http://localhost:8001") -> bool:
    """
    Test the Theo API endpoints.
    
    Args:
        base_url: Base URL of the API server
        
    Returns:
        bool: True if all tests pass, False otherwise
    """
    tests_passed = 0
    total_tests = 0
    
    print(f"🧪 Testing Theo API at {base_url}")
    print("=" * 50)
    
    # Test 1: Root endpoint
    total_tests += 1
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "version" in data:
                print("✅ Root endpoint test PASSED")
                tests_passed += 1
            else:
                print("❌ Root endpoint test FAILED - Missing expected fields")
        else:
            print(f"❌ Root endpoint test FAILED - Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Root endpoint test FAILED - Cannot connect to server")
    except Exception as e:
        print(f"❌ Root endpoint test FAILED - Error: {e}")
    
    # Test 2: Health endpoint
    total_tests += 1
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("✅ Health endpoint test PASSED")
                tests_passed += 1
            else:
                print(f"❌ Health endpoint test FAILED - Unexpected response: {data}")
        else:
            print(f"❌ Health endpoint test FAILED - Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Health endpoint test FAILED - Cannot connect to server")
    except Exception as e:
        print(f"❌ Health endpoint test FAILED - Error: {e}")
    
    # Test 3: Documentation endpoints
    total_tests += 1
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ Documentation endpoint test PASSED")
            tests_passed += 1
        else:
            print(f"❌ Documentation endpoint test FAILED - Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Documentation endpoint test FAILED - Error: {e}")
    
    print("=" * 50)
    print(f"📊 Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests PASSED!")
        return True
    else:
        print("💥 Some tests FAILED!")
        return False


if __name__ == "__main__":
    # Allow custom base URL as command line argument
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    success = test_api(base_url)
    sys.exit(0 if success else 1)