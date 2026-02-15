from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from src.database.models import Product
from src.models.product import NormalizedProduct, EnrichedProduct
from loguru import logger

class ProductRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, product: NormalizedProduct) -> Product:
        db_product = Product(**product.model_dump(exclude_none=True))
        self.session.add(db_product)
        await self.session.flush()
        return db_product
    
    async def bulk_create(self, products: List[NormalizedProduct]) -> List[Product]:
        db_products = [Product(**p.model_dump(exclude_none=True)) for p in products]
        self.session.add_all(db_products)
        await self.session.flush()
        return db_products
    
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 1000, offset: int = 0) -> List[Product]:
        result = await self.session.execute(
            select(Product).limit(limit).offset(offset)
        )
        return result.scalars().all()
    
    async def update_enrichment(self, product_id: UUID, enrichment_data: dict):
        await self.session.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(**enrichment_data, status="enriched")
        )
    
    async def count(self) -> int:
        result = await self.session.execute(select(func.count(Product.id)))
        return result.scalar()
    
    async def get_by_vendor(self, vendor_id: str) -> List[Product]:
        result = await self.session.execute(
            select(Product).where(Product.vendor_id == vendor_id)
        )
        return result.scalars().all()


