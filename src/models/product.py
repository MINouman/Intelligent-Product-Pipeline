from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal
from uuid import UUID

class ImageStatus(str, Enum):
    VALID = "valid"
    BROKEN = "broken"
    MISSING = "missing"
    PENDING = "pending"

class ProcessingStatus(str, Enum):
    RAW = "raw"
    NORMALIZED = "normalized"
    ENRICHED = "enriched"
    FAILED = "failed"

class MessyProduct(BaseModel):
    vendor_id: str
    raw_data: Dict[str, Any]

    model_config = {
        "extra": "allow"
    }

class NormalizedProduct(BaseModel):
    id: Optional[UUID] = None
    vendor_id: str
    vendor_product_id: Optional[str] = None
    
    name: str
    normalized_name: Optional[str] = None
    brand: Optional[str] = None
    brand_normalized: Optional[str] = None
    category: Optional[str] = None

    price: Optional[Decimal] = None
    currency: Optional[str] = None

    image_url: Optional[str] = None
    image_status: ImageStatus = ImageStatus.PENDING

    raw_data: Dict[str, Any]
    normalized_at: Optional[datetime] = None
    status: ProcessingStatus = ProcessingStatus.NORMALIZED

    validation_errors: List[str] = Field(default_factory=list)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v is not None and v<0:
            raise ValueError("Price cannot be negative")
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Product anme cannot be empty')
        return v.strip()
    
class EnrichedProduct(NormalizedProduct):
    extracted_features: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    normalized_name: str = ""
    brand_normalized: Optional[str] = None

    name_embedding: Optional[List[float]] = None
    enriched_at: Optional[datetime] = None

class DuplicateGroup(BaseModel):
    group_id: str
    products: List[str]
    confidence_score: float
    method: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

