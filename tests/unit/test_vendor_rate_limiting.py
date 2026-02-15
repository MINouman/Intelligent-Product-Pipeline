"""
Test Vendor API Rate Limiting

Tests that rate limiting works correctly for all 4 vendors.

Usage:
    # Make sure vendors are running (docker-compose up)
    python test_vendor_rate_limiting.py
"""

import asyncio
import aiohttp
import time
from typing import Dict, List
from datetime import datetime

class VendorRateLimitTester:
    
    def __init__(self):
        self.vendors = {
            "A": {"url": "http://localhost:8001", "limit": 10, "window": 60},
            "B": {"url": "http://localhost:8002", "limit": 5, "window": 60},
            "C": {"url": "http://localhost:8003", "limit": 20, "window": 60},
            "D": {"url": "http://localhost:8004", "limit": 8, "window": 60}
        }
        self.results = {v: {"success": 0, "blocked": 0, "errors": 0} for v in self.vendors}
    
    async def test_vendor_health(self, vendor_id: str) -> bool:
        """Test if vendor is responding."""
        url = f"{self.vendors[vendor_id]['url']}/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✅ Vendor {vendor_id}: {data.get('status', 'unknown')}")
                        return True
                    else:
                        print(f"❌ Vendor {vendor_id}: HTTP {resp.status}")
                        return False
        except Exception as e:
            print(f"❌ Vendor {vendor_id}: {e}")
            return False
    
    async def test_rate_limit_single_vendor(self, vendor_id: str, num_requests: int) -> Dict:
        """
        Test rate limiting for a single vendor.
        
        Sends num_requests to the vendor and tracks:
        - Success (200)
        - Blocked (429)
        - Errors (other)
        """
        config = self.vendors[vendor_id]
        url = f"{config['url']}/products"
        
        results = {"success": 0, "blocked": 0, "errors": 0, "response_times": []}
        
        print(f"\n🔄 Testing Vendor {vendor_id} ({config['limit']} req/{config['window']}s)")
        print(f"   Sending {num_requests} requests...")
        
        async with aiohttp.ClientSession() as session:
            for i in range(num_requests):
                start = time.time()
                
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        elapsed = time.time() - start
                        results["response_times"].append(elapsed)
                        
                        if resp.status == 200:
                            results["success"] += 1
                            print(f"   [{i+1:3d}] ✅ Success ({elapsed:.2f}s)")
                        elif resp.status == 429:
                            results["blocked"] += 1
                            print(f"   [{i+1:3d}] 🚫 BLOCKED (rate limit)")
                        else:
                            results["errors"] += 1
                            print(f"   [{i+1:3d}] ❌ Error: HTTP {resp.status}")
                
                except asyncio.TimeoutError:
                    results["errors"] += 1
                    print(f"   [{i+1:3d}] ⏱️ Timeout")
                except Exception as e:
                    results["errors"] += 1
                    print(f"   [{i+1:3d}] ❌ Error: {e}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
        
        return results
    
    async def test_all_vendors(self):
        """Test all vendors sequentially."""
        print("\n" + "=" * 70)
        print("🧪 VENDOR API RATE LIMITING TEST")
        print("=" * 70)
        
        # Check health first
        print("\n📋 Health Check:")
        all_healthy = True
        for vendor_id in self.vendors:
            if not await self.test_vendor_health(vendor_id):
                all_healthy = False
        
        if not all_healthy:
            print("\n❌ Some vendors are not responding. Make sure Docker containers are running:")
            print("   docker-compose up -d")
            return
        
        # Test each vendor
        for vendor_id, config in self.vendors.items():
            # Send limit + 5 requests (should get some 429s)
            num_requests = config["limit"] + 5
            results = await self.test_rate_limit_single_vendor(vendor_id, num_requests)
            self.results[vendor_id] = results
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        for vendor_id, results in self.results.items():
            config = self.vendors[vendor_id]
            total = results["success"] + results["blocked"] + results["errors"]
            
            print(f"\n🏢 Vendor {vendor_id} (Limit: {config['limit']} req/{config['window']}s)")
            print(f"   Total Requests: {total}")
            print(f"   ✅ Success: {results['success']}")
            print(f"   🚫 Blocked: {results['blocked']}")
            print(f"   ❌ Errors: {results['errors']}")
            
            if results["response_times"]:
                avg_time = sum(results["response_times"]) / len(results["response_times"])
                print(f"   ⏱️  Avg Response: {avg_time:.3f}s")
            
            # Check if rate limiting worked
            if results["blocked"] > 0:
                print(f"   ✅ Rate limiting working correctly")
            elif results["success"] > config["limit"]:
                print(f"   ⚠️  WARNING: More than {config['limit']} requests succeeded!")
            else:
                print(f"   ℹ️  Not enough requests to trigger rate limit")
        
        # Overall stats
        total_success = sum(r["success"] for r in self.results.values())
        total_blocked = sum(r["blocked"] for r in self.results.values())
        total_errors = sum(r["errors"] for r in self.results.values())
        
        print("\n" + "=" * 70)
        print("🎯 OVERALL RESULTS")
        print("=" * 70)
        print(f"Total Requests: {total_success + total_blocked + total_errors}")
        print(f"✅ Success: {total_success}")
        print(f"🚫 Blocked: {total_blocked}")
        print(f"❌ Errors: {total_errors}")
        
        # Pass/fail
        if total_blocked > 0 and total_errors == 0:
            print("\n✅ TEST PASSED: Rate limiting is working correctly!")
        elif total_errors > 0:
            print(f"\n⚠️  TEST PARTIAL: {total_errors} errors occurred")
        else:
            print("\n⚠️  TEST INCOMPLETE: No rate limits triggered")

async def main():
    tester = VendorRateLimitTester()
    await tester.test_all_vendors()

if __name__ == "__main__":
    asyncio.run(main())