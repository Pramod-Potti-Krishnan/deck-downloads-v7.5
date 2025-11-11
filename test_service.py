#!/usr/bin/env python3
"""
Test script for v7.5 Download Service

This script tests the download service endpoints locally.
"""

import httpx
import sys

# Configuration
DOWNLOAD_SERVICE_URL = "http://localhost:8010"
V75_MAIN_URL = "http://localhost:8504"  # Or use Railway URL

# Test presentation (replace with actual presentation ID from v7.5-main)
TEST_PRESENTATION_ID = "test-presentation-id"


async def test_health_check():
    """Test health check endpoint"""
    print("\n" + "=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{DOWNLOAD_SERVICE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False


async def test_pdf_conversion():
    """Test PDF conversion endpoint"""
    print("\n" + "=" * 60)
    print("TEST 2: PDF Conversion")
    print("=" * 60)

    presentation_url = f"{V75_MAIN_URL}/p/{TEST_PRESENTATION_ID}"
    print(f"Presentation URL: {presentation_url}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{DOWNLOAD_SERVICE_URL}/convert/pdf",
            json={
                "presentation_url": presentation_url,
                "landscape": True,
                "print_background": True,
                "quality": "high"
            }
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            pdf_size = len(response.content)
            print(f"PDF Size: {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")

            # Save PDF
            with open("test_output.pdf", "wb") as f:
                f.write(response.content)

            print("✅ PDF saved to test_output.pdf")
            return True
        else:
            print(f"❌ PDF conversion failed: {response.text}")
            return False


async def test_pptx_conversion():
    """Test PPTX conversion endpoint"""
    print("\n" + "=" * 60)
    print("TEST 3: PPTX Conversion")
    print("=" * 60)

    presentation_url = f"{V75_MAIN_URL}/p/{TEST_PRESENTATION_ID}"
    print(f"Presentation URL: {presentation_url}")

    # You need to know the slide count
    slide_count = 7  # Adjust based on your test presentation

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{DOWNLOAD_SERVICE_URL}/convert/pptx",
            json={
                "presentation_url": presentation_url,
                "slide_count": slide_count,
                "aspect_ratio": "16:9",
                "quality": "high"
            }
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            pptx_size = len(response.content)
            print(f"PPTX Size: {pptx_size:,} bytes ({pptx_size/1024:.1f} KB)")

            # Save PPTX
            with open("test_output.pptx", "wb") as f:
                f.write(response.content)

            print("✅ PPTX saved to test_output.pptx")
            return True
        else:
            print(f"❌ PPTX conversion failed: {response.text}")
            return False


async def run_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 v7.5 Download Service Test Suite")
    print("=" * 60)
    print(f"Download Service: {DOWNLOAD_SERVICE_URL}")
    print(f"v7.5-main Service: {V75_MAIN_URL}")
    print(f"Test Presentation ID: {TEST_PRESENTATION_ID}")

    results = []

    # Test 1: Health Check
    try:
        result = await test_health_check()
        results.append(("Health Check", result))
    except Exception as e:
        print(f"❌ Health check error: {e}")
        results.append(("Health Check", False))

    # Test 2: PDF Conversion
    try:
        result = await test_pdf_conversion()
        results.append(("PDF Conversion", result))
    except Exception as e:
        print(f"❌ PDF conversion error: {e}")
        results.append(("PDF Conversion", False))

    # Test 3: PPTX Conversion
    try:
        result = await test_pptx_conversion()
        results.append(("PPTX Conversion", result))
    except Exception as e:
        print(f"❌ PPTX conversion error: {e}")
        results.append(("PPTX Conversion", False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import asyncio

    print("\n⚠️  INSTRUCTIONS:")
    print("1. Make sure v7.5-main is running on port 8504")
    print("2. Make sure download service is running on port 8010")
    print("3. Update TEST_PRESENTATION_ID with a valid presentation ID")
    print("\nPress Enter to continue or Ctrl+C to cancel...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(0)

    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
