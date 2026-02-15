import numpy as np
from scipy.spatial.distance import cosine
from rapidfuzz import fuzz
from typing import List, Dict, Any, Tuple
from loguru import logger

class DuplicateDetector:
    
    def __init__(self, similarity_threshold: float = 0.60):
        self.threshold = similarity_threshold
        self.stats = {
            "total_products": 0,
            "duplicate_groups": 0,
            "method_breakdown": {
                "embedding": 0,
                "fuzzy": 0,
                "rule_based": 0,
                "hybrid": 0,
                "none": 0
            }
        }
        
        logger.info(f"DuplicateDetector initialized with threshold {self.threshold}")
    
    def detect_duplicates(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.stats["total_products"] = len(products)
        logger.info(f"Starting duplicate detection on {len(products)} products")
        
        duplicate_groups = []
        visited = set()
        
        for i, product_a in enumerate(products):
            if product_a["id"] in visited:
                continue
            
            group = [product_a["id"]]
            group_scores = [] 
            group_methods = []  
            
            for j, product_b in enumerate(products[i+1:], start=i+1):
                if product_b["id"] in visited:
                    continue
                
                score, method = self._calculate_similarity(product_a, product_b)
                
                if score >= self.threshold:
                    group.append(product_b["id"])
                    visited.add(product_b["id"])
                    group_scores.append(score)  
                    group_methods.append(method)  
            
            if len(group) > 1:
                visited.add(product_a["id"])
                
                group_confidence = sum(group_scores) / len(group_scores) if group_scores else 0.0
                
                group_method = self._determine_group_method(group_methods, group_confidence)
                
                duplicate_groups.append({
                    "group_id": f"dup_{len(duplicate_groups)+1:03d}",
                    "products": group,
                    "confidence": round(group_confidence, 3),
                    "method": group_method,
                    "group_size": len(group),
                    "method_breakdown": self._count_methods(group_methods)
                })
                
                self.stats["method_breakdown"][group_method] += 1
        
        self.stats["duplicate_groups"] = len(duplicate_groups)
        
        logger.info(
            f"Duplicate detection complete: {len(duplicate_groups)} groups found. "
            f"Methods: {self.stats['method_breakdown']}"
        )
        
        return duplicate_groups
    
    def _determine_group_method(self, methods: List[str], confidence: float) -> str:
        if not methods:
            return "none"
        
        method_counts = {}
        for method in methods:
            method_counts[method] = method_counts.get(method, 0) + 1
        
        dominant_method = max(method_counts, key=method_counts.get)
        dominant_count = method_counts[dominant_method]
        
        if len(method_counts) > 1 and dominant_count / len(methods) < 0.7:
            return "hybrid"
        
        return dominant_method
    
    def _count_methods(self, methods: List[str]) -> Dict[str, int]:
        counts = {}
        for method in methods:
            counts[method] = counts.get(method, 0) + 1
        return counts
    
    def _calculate_similarity(self, product_a: Dict, product_b: Dict) -> Tuple[float, str]:
        EMBEDDING_WEIGHT = 0.60
        FUZZY_WEIGHT = 0.25
        RULE_WEIGHT = 0.15
        
        scores = {}
        
        if "name_embedding" in product_a and "name_embedding" in product_b:
            emb_a = np.array(product_a["name_embedding"])
            emb_b = np.array(product_b["name_embedding"])
            embedding_sim = 1 - cosine(emb_a, emb_b)
            scores["embedding"] = max(0, embedding_sim)
        else:
            scores["embedding"] = 0
        
        name_a = product_a.get("normalized_name", "")
        name_b = product_b.get("normalized_name", "")
        if name_a and name_b:
            fuzzy_score = fuzz.token_sort_ratio(name_a, name_b) / 100.0
            scores["fuzzy"] = fuzzy_score
        else:
            scores["fuzzy"] = 0
        
        rule_score = 0
        brand_a = product_a.get("brand_normalized", "")
        brand_b = product_b.get("brand_normalized", "")
        
        try:
            price_a = float(product_a.get("price", 0)) if product_a.get("price") else 0
        except (ValueError, TypeError):
            price_a = 0
        
        try:
            price_b = float(product_b.get("price", 0)) if product_b.get("price") else 0
        except (ValueError, TypeError):
            price_b = 0

        if brand_a and brand_b and brand_a == brand_b:
            rule_score += 0.5

        if price_a > 0 and price_b > 0:
            price_diff = abs(price_a - price_b) / max(price_a, price_b)
            if price_diff < 0.1:
                rule_score += 0.5
        
        scores["rule_based"] = rule_score
        
        final_score = (
            scores["embedding"] * EMBEDDING_WEIGHT +
            scores["fuzzy"] * FUZZY_WEIGHT +
            scores["rule_based"] * RULE_WEIGHT
        )
        
        if final_score >= self.threshold:
            if scores["embedding"] > 0.8:
                method = "embedding"
            elif scores["fuzzy"] > 0.9:
                method = "fuzzy"
            elif scores["rule_based"] == 1.0:
                method = "rule_based"
            else:
                method = "hybrid"
        else:
            method = "none"
        
        return final_score, method
    
    def get_stats(self) -> Dict[str, Any]:
        if self.stats["total_products"] > 0:
            duplicate_rate = (
                sum(self.stats["method_breakdown"].values()) * 2 /
                self.stats["total_products"] * 100
            )
        else:
            duplicate_rate = 0
        
        return {
            **self.stats,
            "duplicate_rate_percent": round(duplicate_rate, 2),
            "threshold": self.threshold
        }