#!/usr/bin/env python3
"""
Test script for GPU Sticker Generation Service
"""
import requests
import base64
import json
import sys
import time
from pathlib import Path


BASE_URL = "http://localhost:5000"


def test_health():
    """Test health endpoint"""
    print("=" * 70)
    print("TEST 1: Health Check")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        
        print("✅ Health check response:")
        print(json.dumps(data, indent=2))
        print()
        
        if data.get("status") == "healthy" and data.get("is_loaded"):
            print("✅ Service is healthy and models are loaded")
            return True
        else:
            print("⚠️  Service is running but models may not be loaded")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_info():
    """Test info endpoint"""
    print("=" * 70)
    print("TEST 2: Service Info")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/api/info")
        data = response.json()
        
        print("✅ Service info:")
        print(json.dumps(data, indent=2))
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Info check failed: {e}")
        return False


def test_generate_stickers(image_path: str):
    """Test sticker generation"""
    print("=" * 70)
    print("TEST 3: Generate Stickers")
    print("=" * 70)
    
    try:
        # Read and encode image
        print(f"📤 Loading image: {image_path}")
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
        
        print(f"📤 Sending request (image size: {len(base64_image)} chars)...")
        print("⏳ This will take 12-20 seconds...")
        print()
        
        start_time = time.time()
        
        # Send request
        response = requests.post(
            f"{BASE_URL}/api/generate-stickers",
            json={
                "image": base64_image,
                "seed": 42
            },
            timeout=120  # 2 minute timeout
        )
        
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            print("=" * 70)
            print("✅ SUCCESS!")
            print("=" * 70)
            print(f"Processing time: {data['processing_time']}s")
            print(f"Total request time: {request_time:.2f}s")
            print(f"Number of stickers: {len(data['stickers'])}")
            print()
            
            # Save stickers
            for sticker in data['stickers']:
                mood = sticker['mood']
                sticker_data = base64.b64decode(sticker['image'])
                
                output_path = f"test_output_{mood}.png"
                with open(output_path, 'wb') as f:
                    f.write(sticker_data)
                
                print(f"💾 Saved: {output_path}")
            
            print()
            print("Expressions generated:")
            for sticker in data['stickers']:
                print(f"  - {sticker['mood']}")
            
            print()
            return True
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_expressions(image_path: str):
    """Test generating specific expressions"""
    print("=" * 70)
    print("TEST 4: Generate Specific Expressions")
    print("=" * 70)
    
    try:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Request only happy and sad
        print("📤 Requesting only 'happy' and 'sad' expressions...")
        
        response = requests.post(
            f"{BASE_URL}/api/generate-stickers",
            json={
                "image": base64_image,
                "seed": 42,
                "expressions": ["happy", "sad"]
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Generated {len(data['stickers'])} stickers")
            print("Expressions:")
            for sticker in data['stickers']:
                print(f"  - {sticker['mood']}")
            
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "GPU Sticker Service - Test Suite" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = []
    
    # Test 1: Health check
    health_ok = test_health()
    results.append(("Health Check", health_ok))
    
    if not health_ok:
        print()
        print("❌ Service is not healthy. Please check:")
        print("   1. Is the service running? (./run.sh)")
        print("   2. Are models loaded? (check logs)")
        print("   3. Is GPU available? (nvidia-smi)")
        sys.exit(1)
    
    print()
    
    # Test 2: Info
    info_ok = test_info()
    results.append(("Service Info", info_ok))
    print()
    
    # Test 3 & 4: Generation tests
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if Path(image_path).exists():
            # Test all expressions
            generate_ok = test_generate_stickers(image_path)
            results.append(("Generate All Stickers", generate_ok))
            print()
            
            # Test specific expressions
            if generate_ok:
                specific_ok = test_specific_expressions(image_path)
                results.append(("Generate Specific Stickers", specific_ok))
        else:
            print(f"❌ Image file not found: {image_path}")
    else:
        print("⏭️  Skipping generation tests (no image provided)")
        print("   Usage: python test_service.py <path_to_test_image>")
    
    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print()
        print("✅ All tests passed!")
        print()
        print("Service is ready to use!")
        print(f"API endpoint: http://139.84.132.3:5000/api/generate-stickers")
        print(f"Documentation: http://139.84.132.3:5000/docs")
    else:
        print()
        print("❌ Some tests failed. Please check the logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()