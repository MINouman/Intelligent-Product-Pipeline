from sqlalchemy import Column, String, Numeric, DateTime, JSON, Enum, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
import uuid

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    vendor_id = Column(String(10), nullable=False, index=True)
    vendor_product_id = Column(String(255), nullable=True)
    
    name = Column(Text, nullable=False)
    normalized_name = Column(Text, nullable=True)
    brand = Column(String(255), nullable=True, index=True)
    brand_normalized = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True, index=True)
    
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), nullable=False, default="BDT")
    
    image_url = Column(Text, nullable=True)
    image_status = Column(
        Enum("valid", "broken", "missing", "pending", name="image_status_enum"),
        nullable=False,
        default="pending"
    )
    
    extracted_features = Column(ARRAY(String), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    name_embedding = Column(ARRAY(Numeric), nullable=True) 
    
    raw_data = Column(JSONB, nullable=False)
    validation_errors = Column(JSONB, nullable=True)
    
    status = Column(
        Enum("raw", "normalized", "enriched", "failed", name="processing_status_enum"),
        nullable=False,
        default="raw"
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    normalized_at = Column(DateTime(timezone=True), nullable=True)
    enriched_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_vendor_brand', 'vendor_id', 'brand'),
        Index('idx_category_price', 'category', 'price'),
        Index('idx_normalized_name_gin', 'normalized_name', postgresql_using='gin', postgresql_ops={'normalized_name': 'gin_trgm_ops'}),  # For fuzzy search
    )

class DuplicateGroupDB(Base):
    __tablename__ = "duplicate_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(String(50), unique=True, nullable=False, index=True)
    
    product_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    
    confidence_score = Column(Numeric(5, 4), nullable=False)
    method = Column(String(50), nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


