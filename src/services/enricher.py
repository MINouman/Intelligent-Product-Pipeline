from sentence_transformers import SentenceTransformer
import spacy
from typing import List, Dict, Any
import numpy as np
from loguru import logger
import re

class ProductEnricher:
    
    def __init__(self):
        logger.info("Loading AI models...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load('en_core_web_sm')
        logger.info("AI models loaded successfully")
        
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
    
    def enrich(self, product: Dict[str, Any]) -> Dict[str, Any]:
        self.stats["total"] += 1
        
        try:
            name = product.get("name", "")
            brand = product.get("brand", "")
            category = product.get("category", "")
            
            name_embedding = self.embedding_model.encode(name).tolist()
            
            features = self._extract_features(name)
            
            tags = self._generate_tags(name, brand, category)
            
            # normalized_name = self._normalize_text(name)
            # brand_normalized = self._normalize_text(brand) if brand else None
            
            enrichment = {
                "name_embedding": name_embedding,
                "extracted_features": features,
                "tags": tags,
                # "normalized_name": normalized_name,
                # "brand_normalized": brand_normalized,
            }
            
            self.stats["success"] += 1
            return enrichment
            
        except Exception as e:
            logger.error(f"Enrichment failed for product: {e}")
            self.stats["failed"] += 1
            return {}
    
    def _extract_features(self, text: str) -> List[str]:
        doc = self.nlp(text)
        features = []
        
        numbers = re.findall(r'\d+(?:GB|TB|MP|inch|")', text, re.IGNORECASE)
        features.extend(numbers)
        
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE"]:
                features.append(ent.text)
        
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2:
                features.append(token.text)
        
        return list(set(features))[:10]  
    
    def _generate_tags(self, name: str, brand: str, category: str) -> List[str]:
        tags = []

        if brand:
            tags.append(brand.lower())
        
        if category:
            tags.append(category.lower())

        keywords = ["pro", "plus", "max", "mini", "air", "ultra"]
        name_lower = name.lower()
        for keyword in keywords:
            if keyword in name_lower:
                tags.append(keyword)
        
        return list(set(tags))
    
    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = text.lower()
        
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def enrich_batch(self, products: List[Dict]) -> List[Dict]:
        enriched = []
        
        for product in products:
            enrichment = self.enrich(product)
            product.update(enrichment)
            enriched.append(product)
        
        logger.info(f"Enrichment complete: {self.stats['success']}/{self.stats['total']} succeeded")
        return enriched


