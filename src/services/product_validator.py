from typing import Dict, Any, List, Tuple
from decimal import Decimal
from enum import Enum
import re
from loguru import logger


class QualityLevel(str, Enum):
    """Product quality levels."""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"            # 70-89
    FAIR = "fair"            # 50-69
    POOR = "poor"            # Below 50


class ValidationSeverity(str, Enum):
    CRITICAL = "critical" 
    WARNING = "warning" 
    INFO = "info"


class ProductValidator:
    """
    Enhanced validator with quality scoring.
    
    Scores products based on:
    - Required fields presence (40%)
    - Data quality (30%)
    - Completeness (30%)
    """
    
    def __init__(self):
        self.stats = {
            "total": 0,
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "poor": 0,
            "flagged": 0
        }
    
    def validate(self, product: Dict[str, Any]) -> Tuple[int, QualityLevel, List[Dict]]:
        self.stats["total"] += 1
        
        score = 100
        issues = []
        
        required_score, required_issues = self._validate_required_fields(product)
        score -= (40 - required_score)
        issues.extend(required_issues)
        
        quality_score, quality_issues = self._validate_data_quality(product)
        score -= (30 - quality_score)
        issues.extend(quality_issues)
        
        completeness_score, completeness_issues = self._validate_completeness(product)
        score -= (30 - completeness_score)
        issues.extend(completeness_issues)
        
        if score >= 90:
            quality_level = QualityLevel.EXCELLENT
            self.stats["excellent"] += 1
        elif score >= 70:
            quality_level = QualityLevel.GOOD
            self.stats["good"] += 1
        elif score >= 50:
            quality_level = QualityLevel.FAIR
            self.stats["fair"] += 1
        else:
            quality_level = QualityLevel.POOR
            self.stats["poor"] += 1
            self.stats["flagged"] += 1
        
        return max(0, score), quality_level, issues
    
    def _validate_required_fields(self, product: Dict) -> Tuple[int, List[Dict]]:
        """
        Validate required fields (40 points).
        
        Required fields:
        - id (10 points)
        - vendor_id (5 points)
        - name (15 points)
        - normalized_name (5 points)
        - category (5 points)
        """
        score = 40
        issues = []
        
        if not product.get("id"):
            score -= 10
            issues.append({
                "field": "id",
                "severity": ValidationSeverity.CRITICAL,
                "message": "Missing product ID"
            })
        
        if not product.get("vendor_id"):
            score -= 5
            issues.append({
                "field": "vendor_id",
                "severity": ValidationSeverity.CRITICAL,
                "message": "Missing vendor ID"
            })
        
        if not product.get("name"):
            score -= 15
            issues.append({
                "field": "name",
                "severity": ValidationSeverity.CRITICAL,
                "message": "Missing product name"
            })
        elif len(product["name"]) < 3:
            score -= 5
            issues.append({
                "field": "name",
                "severity": ValidationSeverity.WARNING,
                "message": f"Name too short: '{product['name']}'"
            })
        
        if not product.get("normalized_name"):
            score -= 5
            issues.append({
                "field": "normalized_name",
                "severity": ValidationSeverity.WARNING,
                "message": "Missing normalized name"
            })
        
        if not product.get("category"):
            score -= 5
            issues.append({
                "field": "category",
                "severity": ValidationSeverity.WARNING,
                "message": "Missing category"
            })
        
        return max(0, score), issues
    
    def _validate_data_quality(self, product: Dict) -> Tuple[int, List[Dict]]:
        score = 30
        issues = []
        
        price = product.get("price")
        if price is None:
            score -= 10
            issues.append({
                "field": "price",
                "severity": ValidationSeverity.CRITICAL,
                "message": "Missing price"
            })
        else:
            try:
                price_val = float(price)
                if price_val <= 0:
                    score -= 5
                    issues.append({
                        "field": "price",
                        "severity": ValidationSeverity.WARNING,
                        "message": f"Invalid price: {price_val}"
                    })
                elif price_val > 100000:
                    score -= 2
                    issues.append({
                        "field": "price",
                        "severity": ValidationSeverity.WARNING,
                        "message": f"Unusually high price: {price_val}"
                    })
            except (ValueError, TypeError):
                score -= 10
                issues.append({
                    "field": "price",
                    "severity": ValidationSeverity.CRITICAL,
                    "message": f"Invalid price format: {price}"
                })
        
        currency = product.get("currency")
        valid_currencies = ["USD", "EUR", "GBP", "BDT", "INR", "JPY", "CNY"]
        if not currency:
            score -= 5
            issues.append({
                "field": "currency",
                "severity": ValidationSeverity.WARNING,
                "message": "Missing currency"
            })
        elif currency not in valid_currencies:
            score -= 3
            issues.append({
                "field": "currency",
                "severity": ValidationSeverity.WARNING,
                "message": f"Unknown currency: {currency}"
            })
        
        brand = product.get("brand")
        if not brand:
            score -= 10
            issues.append({
                "field": "brand",
                "severity": ValidationSeverity.WARNING,
                "message": "Missing brand"
            })
        elif len(brand) < 2:
            score -= 5
            issues.append({
                "field": "brand",
                "severity": ValidationSeverity.WARNING,
                "message": f"Brand name too short: '{brand}'"
            })
        
        image_url = product.get("image_url")
        image_status = product.get("image_status", "missing")
        
        if not image_url:
            score -= 3
            issues.append({
                "field": "image_url",
                "severity": ValidationSeverity.INFO,
                "message": "No image URL"
            })
        elif image_status == "broken":
            score -= 5
            issues.append({
                "field": "image_url",
                "severity": ValidationSeverity.WARNING,
                "message": "Broken image URL"
            })
        elif not image_url.startswith(("http://", "https://")):
            score -= 4
            issues.append({
                "field": "image_url",
                "severity": ValidationSeverity.WARNING,
                "message": f"Invalid image URL format: {image_url[:50]}"
            })
        
        return max(0, score), issues
    
    def _validate_completeness(self, product: Dict) -> Tuple[int, List[Dict]]:
        score = 30
        issues = []
        
        if not product.get("brand_normalized"):
            score -= 5
            issues.append({
                "field": "brand_normalized",
                "severity": ValidationSeverity.INFO,
                "message": "Brand not normalized"
            })
        
        if not product.get("vendor_product_id"):
            score -= 5
            issues.append({
                "field": "vendor_product_id",
                "severity": ValidationSeverity.INFO,
                "message": "No vendor product ID"
            })
        
        if not product.get("raw_data"):
            score -= 10
            issues.append({
                "field": "raw_data",
                "severity": ValidationSeverity.WARNING,
                "message": "No raw data preserved"
            })
        
        if not product.get("normalized_at"):
            score -= 5
            issues.append({
                "field": "normalized_at",
                "severity": ValidationSeverity.INFO,
                "message": "No normalization timestamp"
            })
        
        if "validation_errors" not in product:
            score -= 5
            issues.append({
                "field": "validation_errors",
                "severity": ValidationSeverity.INFO,
                "message": "Validation errors not tracked"
            })
        
        return max(0, score), issues
    
    def get_stats(self) -> Dict[str, Any]:
        if self.stats["total"] == 0:
            return self.stats
        
        return {
            **self.stats,
            "excellent_pct": round(self.stats["excellent"] / self.stats["total"] * 100, 1),
            "good_pct": round(self.stats["good"] / self.stats["total"] * 100, 1),
            "fair_pct": round(self.stats["fair"] / self.stats["total"] * 100, 1),
            "poor_pct": round(self.stats["poor"] / self.stats["total"] * 100, 1),
            "flagged_pct": round(self.stats["flagged"] / self.stats["total"] * 100, 1)
        }
    
    def validate_batch(self, products: List[Dict]) -> List[Dict]:
        validated = []
        
        for product in products:
            score, level, issues = self.validate(product)
            
            product["quality_score"] = score
            product["quality_level"] = level.value
            product["quality_issues"] = issues
            product["is_flagged"] = (level == QualityLevel.POOR)
            
            validated.append(product)
        
        logger.info(f"Validated {len(products)} products: {self.get_stats()}")
        
        return validated