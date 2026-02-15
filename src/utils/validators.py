import aiohttp
import asyncio
from typing import Tuple, List
from loguru import logger
from src.models.product import ImageStatus

class ImageValidator:
    
    def __init__(self, timeout: int = 5):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def validate_url(self, url: str) -> ImageStatus:
        if not url:
            return ImageStatus.MISSING
        
        try:
            async with self.session.head(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'image' in content_type:
                        return ImageStatus.VALID
                    else:
                        return ImageStatus.BROKEN
                else:
                    return ImageStatus.BROKEN
        except Exception as e:
            logger.debug(f"Image validation failed for {url}: {e}")
            return ImageStatus.BROKEN
    
    async def validate_batch(self, urls: List[str]) -> List[ImageStatus]:
        tasks = [self.validate_url(url) for url in urls]
        return await asyncio.gather(*tasks)