import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from src.services.normalizer import ProductNormalizer
from src.services.vendor_client import MultiVendorOrchestrator
from src.services.enricher import ProductEnricher
from src.services.duplicate_detector import DuplicateDetector
from src.database.connection import get_db
from src.database.repositories.product_repo import ProductRepository
from src.config.settings import get_settings

settings = get_settings()

class ProductPipeline:
    
    def __init__(self):
        self.normalizer = ProductNormalizer()
        self.enricher = ProductEnricher()
        self.detector = DuplicateDetector(settings.DUPLICATE_SIMILARITY_THRESHOLD)
        
        self.pipeline_stats = {
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "phases": {}
        }
    
    async def run(self, input_file: str):
        """Run the complete pipeline."""
        self.pipeline_stats["start_time"] = datetime.utcnow()
        logger.info("="*80)
        logger.info("STARTING PRODUCT PROCESSING PIPELINE")
        logger.info("="*80)
        
        try:
            products = await self._phase1_normalize(input_file)
            
            products = await self._phase2_fetch_vendors(products)
            
            products = await self._phase3_enrich(products)
            
            duplicates = await self._phase4_detect_duplicates(products)
            
            await self._phase5_save_results(products, duplicates)

            self.pipeline_stats["end_time"] = datetime.utcnow()
            duration = (self.pipeline_stats["end_time"] - self.pipeline_stats["start_time"]).total_seconds()
            self.pipeline_stats["duration_seconds"] = duration
            
            logger.info("="*80)
            logger.info(f"PIPELINE COMPLETE in {duration:.2f} seconds")
            logger.info("="*80)
            self._print_summary()
            
            return {
                "success": True,
                "stats": self.pipeline_stats
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _phase1_normalize(self, input_file: str) -> List[Dict]:
        phase_start = datetime.utcnow()
        logger.info("Phase 1: Data Normalization")
        
        with open(input_file, 'r') as f:
            messy_products = json.load(f)
        
        logger.info(f"Loaded {len(messy_products)} messy products")
        
        normalized, failed = await self.normalizer.normalize_batch(messy_products)
        
        async with get_db() as session:
            repo = ProductRepository(session)
            await repo.bulk_create(normalized)
        
        phase_duration = (datetime.utcnow() - phase_start).total_seconds()
        self.pipeline_stats["phases"]["normalization"] = {
            "duration_seconds": phase_duration,
            "total": len(messy_products),
            "success": len(normalized),
            "failed": len(failed),
            "success_rate": len(normalized) / len(messy_products) * 100
        }
        
        logger.info(f"Phase 1 complete in {phase_duration:.2f}s: {len(normalized)}/{len(messy_products)} normalized")
        
        return [p.model_dump() for p in normalized]
    
    async def _phase2_fetch_vendors(self, products: List[Dict]) -> List[Dict]:
        phase_start = datetime.utcnow()
        logger.info("Phase 2: Vendor API Fetching")
        
        async with MultiVendorOrchestrator() as orchestrator:
            result = await orchestrator.fetch_products(products)
        
        vendor_data = result["results"]
        for product in products:
            if product["id"] in vendor_data:
                product["vendor_enrichment"] = vendor_data[product["id"]]
        
        phase_duration = (datetime.utcnow() - phase_start).total_seconds()
        self.pipeline_stats["phases"]["vendor_fetching"] = {
            **result["stats"],
            "duration_seconds": phase_duration
        }
        
        logger.info(f"Phase 2 complete in {phase_duration:.2f}s")
        
        return products
    
    async def _phase3_enrich(self, products: List[Dict]) -> List[Dict]:
        """Phase 3: AI enrichment."""
        phase_start = datetime.utcnow()
        logger.info("Phase 3: AI Enrichment")
        
        enriched = await self.enricher.enrich_batch(products)
        
        async with get_db() as session:
            repo = ProductRepository(session)
            for product in enriched:
                await repo.update_enrichment(product["id"], product)
        
        phase_duration = (datetime.utcnow() - phase_start).total_seconds()
        self.pipeline_stats["phases"]["enrichment"] = {
            "duration_seconds": phase_duration,
            **self.enricher.stats
        }
        
        logger.info(f"Phase 3 complete in {phase_duration:.2f}s")
        
        return enriched
    
    async def _phase4_detect_duplicates(self, products: List[Dict]) -> List[Dict]:
        phase_start = datetime.utcnow()
        logger.info("Phase 4: Duplicate Detection")
        
        duplicates = self.detector.detect_duplicates(products)
        
        phase_duration = (datetime.utcnow() - phase_start).total_seconds()
        self.pipeline_stats["phases"]["duplicate_detection"] = {
            "duration_seconds": phase_duration,
            **self.detector.get_stats()
        }
        
        logger.info(f"Phase 4 complete in {phase_duration:.2f}s: {len(duplicates)} groups found")
        
        return duplicates
    
    async def _phase5_save_results(self, products: List[Dict], duplicates: List[Dict]):
        logger.info("Phase 5: Saving Results")
        
        output_dir = Path(settings.DATA_OUTPUT_PATH)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        normalized_path = output_dir / "normalized_products.json"
        with open(normalized_path, 'w') as f:
            products_clean = [{k: v for k, v in p.items() if k != "name_embedding"} for p in products]
            json.dump(products_clean, f, indent=2, default=str)
        
        enriched_path = output_dir / "enriched_products.json"
        with open(enriched_path, 'w') as f:
            json.dump(products, f, indent=2, default=str)
        
        duplicates_path = output_dir / "duplicates.json"
        with open(duplicates_path, 'w') as f:
            json.dump(duplicates, f, indent=2)
        
        logger.info(f"Results saved to {output_dir}")
    
    def _print_summary(self):
        """Print pipeline summary."""
        print("\n" + "="*80)
        print("PIPELINE SUMMARY")
        print("="*80)
        
        for phase, stats in self.pipeline_stats["phases"].items():
            print(f"\n{phase.upper().replace('_', ' ')}:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        print(f"\nTOTAL DURATION: {self.pipeline_stats['duration_seconds']:.2f} seconds")
        print("="*80 + "\n")