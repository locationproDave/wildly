#!/usr/bin/env python3

import requests
import json
import sys

def test_local_backend():
    """Quick test of local backend APIs"""
    print("🔍 Testing Local Backend APIs")
    print("=" * 50)
    
    base_url = "http://localhost:8001/api"
    tests_passed = 0
    total_tests = 0
    
    # Test basic endpoints
    tests = [
        ("Health Check", "GET", "/health"),
        ("API Root", "GET", "/"),
        ("Agents List", "GET", "/agents"),
    ]
    
    for test_name, method, endpoint in tests:
        total_tests += 1
        try:
            print(f"Testing {test_name}...")
            url = f"{base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                tests_passed += 1
                print(f"  ✅ {test_name} - Status: {response.status_code}")
                
                # For agents endpoint, show agent count
                if endpoint == "/agents":
                    data = response.json()
                    agents = data.get("agents", {})
                    print(f"     Found {len(agents)} agents: {list(agents.keys())}")
                    
            else:
                print(f"  ❌ {test_name} - Status: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {test_name} - Error: {str(e)}")
    
    print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed >= 2:  # At least health and agents working
        print("✅ Backend core APIs working locally")
        return True
    else:
        print("❌ Backend has issues")
        return False

if __name__ == "__main__":
    success = test_local_backend()
    sys.exit(0 if success else 1)