#!/usr/bin/env python3
"""
Test script to verify the upload system works
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:5001"

print("=" * 60)
print("TESTING NAGARIKTA UPLOAD SYSTEM")
print("=" * 60)

# Test 1: Health check
print("\n[1] Testing Health Check Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"    ✓ Health check successful")
        print(f"    Model loaded: {data.get('model_loaded')}")
        print(f"    Upload folder exists: {data.get('config', {}).get('upload_folder_exists')}")
    else:
        print(f"    ❌ Health check failed with status {response.status_code}")
except requests.exceptions.ConnectionError:
    print(f"    ❌ Cannot connect to server at {BASE_URL}")
    print(f"    Make sure Flask app is running: python chatgpt.py")
    exit(1)
except Exception as e:
    print(f"    ❌ Error: {e}")
    exit(1)

# Test 2: Check if we can reach the main page
print("\n[2] Testing Main Page...")
try:
    response = requests.get(f"{BASE_URL}/", timeout=10)
    if response.status_code == 200:
        print(f"    ✓ Main page accessible")
    else:
        print(f"    ❌ Main page returned status {response.status_code}")
except Exception as e:
    print(f"    ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ READY TO TEST")
print("=" * 60)
print("\nTo test the upload:")
print("1. Open http://localhost:5001 in your browser")
print("2. Select a front and back image of a citizenship card")
print("3. Click Upload")
print("4. Monitor server logs for detailed processing info")
print("\nServer logs show with tags like:")
print("  [DEBUG] - Processing steps")
print("  [ERROR] - Errors encountered")
print("  [WARN]  - Warnings")
