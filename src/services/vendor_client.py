import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
from loguru import logger
from src.config.settings import get_settings

settings = get_settings()

class RateLimitedVendorClient:
    
    def __init__(self, vendor_id: str, rate_limit: int, window_seconds: int = 60):
        self.vendor_id = vendor_id
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        
        self.safe_rate_limit = int(rate_limit * 0.8)
        
        self.request_delay = window_seconds / self.safe_rate_limit
        
        self.request_times = deque()
        self.total_requests = 0
        self.total_blocks = 0
        
        self.semaphore = asyncio.Semaphore(self.safe_rate_limit)
        
        self.session = None
        
        logger.info(
            f"Vendor {vendor_id}: Rate limit {rate_limit}/{window_seconds}s, "
            f"Safe limit {self.safe_rate_limit}, Delay {self.request_delay:.2f}s"
        )
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def _wait_for_capacity(self):
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()
        
        if len(self.request_times) >= self.safe_rate_limit:
            oldest = self.request_times[0]
            wait_time = (oldest + timedelta(seconds=self.window_seconds) - now).total_seconds()
            if wait_time > 0:
                logger.debug(f"Vendor {self.vendor_id}: Waiting {wait_time:.2f}s for capacity")
                await asyncio.sleep(wait_time + 0.1) 
    
    async def fetch_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        async with self.semaphore:
            await self._wait_for_capacity()
            
            await asyncio.sleep(self.request_delay)
            
            url = self._get_vendor_url()
            self.total_requests += 1
            
            try:
                self.request_times.append(datetime.utcnow())
                
                async with self.session.get(f"{url}/product/{product_id}") as response:
                    if response.status == 429:
                        self.total_blocks += 1
                        retry_after = int(response.headers.get('Retry-After', self.window_seconds))
                        logger.warning(
                            f"Vendor {self.vendor_id}: Rate limited! Block #{self.total_blocks}. "
                            f"Waiting {retry_after}s"
                        )
                        await asyncio.sleep(retry_after)
                        # Retry once
                        return await self.fetch_product(product_id)
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    logger.debug(
                        f"Vendor {self.vendor_id}: Fetched product {product_id}",
                        extra={
                            "vendor_id": self.vendor_id,
                            "product_id": product_id,
                            "status": "success"
                        }
                    )
                    return data
                    
            except asyncio.TimeoutError:
                logger.error(f"Vendor {self.vendor_id}: Timeout for product {product_id}")
                return None
            except Exception as e:
                logger.error(f"Vendor {self.vendor_id}: Error fetching {product_id}: {e}")
                return None
    
    def _get_vendor_url(self) -> str:
        vendor_urls = {
            "A": settings.VENDOR_A_URL,
            "B": settings.VENDOR_B_URL,
            "C": settings.VENDOR_C_URL,
            "D": settings.VENDOR_D_URL,
        }
        return vendor_urls[self.vendor_id]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "total_requests": self.total_requests,
            "total_blocks": self.total_blocks,
            "current_queue_size": len(self.request_times),
            "rate_limit": self.rate_limit,
            "safe_rate_limit": self.safe_rate_limit,
        }

class MultiVendorOrchestrator:
    
    def __init__(self):
        self.vendors = {
            "A": RateLimitedVendorClient("A", settings.VENDOR_A_RATE_LIMIT),
            "B": RateLimitedVendorClient("B", settings.VENDOR_B_RATE_LIMIT),
            "C": RateLimitedVendorClient("C", settings.VENDOR_C_RATE_LIMIT),
            "D": RateLimitedVendorClient("D", settings.VENDOR_D_RATE_LIMIT),
        }
    
    async def __aenter__(self):
        for vendor in self.vendors.values():
            await vendor.__aenter__()
        return self
    
    async def __aexit__(self, *args):
        for vendor in self.vendors.values():
            await vendor.__aexit__(*args)
    
    async def fetch_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = datetime.utcnow()
        
        vendor_products = {}
        for product in products:
            vendor_id = product["vendor_id"]
            if vendor_id not in vendor_products:
                vendor_products[vendor_id] = []
            vendor_products[vendor_id].append(product)
        
        logger.info(f"Starting parallel vendor fetching for {len(products)} products")
        logger.info(f"Distribution: {[(v, len(ps)) for v, ps in vendor_products.items()]}")
        
        tasks = []
        for vendor_id, vendor_prods in vendor_products.items():
            if vendor_id in self.vendors:
                task = self._fetch_vendor_batch(vendor_id, vendor_prods)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        all_results = {}
        for result in results:
            all_results.update(result)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        total_blocks = sum(v.total_blocks for v in self.vendors.values())
        
        logger.info(
            f"Vendor fetching complete: {len(all_results)}/{len(products)} succeeded "
            f"in {duration:.2f}s with {total_blocks} blocks"
        )
        
        return {
            "results": all_results,
            "stats": {
                "duration_seconds": duration,
                "total_products": len(products),
                "successful": len(all_results),
                "total_blocks": total_blocks,
                "vendor_stats": [v.get_stats() for v in self.vendors.values()]
            }
        }
    
    async def _fetch_vendor_batch(self, vendor_id: str, products: List[Dict]) -> Dict[str, Any]:
        client = self.vendors[vendor_id]
        results = {}
        
        tasks = [client.fetch_product(p["id"]) for p in products]
        vendor_results = await asyncio.gather(*tasks)
        
        for product, result in zip(products, vendor_results):
            if result:
                results[product["id"]] = result
        
        return results
