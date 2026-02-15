import pytest
import json
import asyncio
from pathlib import Path

from src.services.normalizer import ProductNormalizer
from src.services.enricher import ProductEnricher
from src.services.duplicate_detector import DuplicateDetector
from src.services.product_validator import ProductValidator


def run_if_async(result):
    if asyncio.iscoroutine(result):
        return asyncio.run(result)
    return result


def to_dict_list(products):
    result = []
    for p in products:
        if hasattr(p, '__dict__'):
            result.append(vars(p))
        elif isinstance(p, dict):
            result.append(p)
        else:
            result.append(dict(p))
    return result


class TestPipelineIntegration:
    
    @pytest.fixture
    def sample_products(self):
        return [
            {
                "vendor_id": "A",
                "productTitle": "iPhone 15 Pro",
                "brand": "Apple",
                "categoryPath": "Electronics > Phones",
                "pricing": {"amount": "999.00"},
                "image": "https://example.com/iphone.jpg"
            },
            {
                "vendor_id": "B",
                "name": "iPhone 15Pro",
                "manufacturer": "Apple Inc",
                "dept": "Electronics",
                "price": "৳999.00",
                "img": ""
            },
            {
                "vendor_id": "C",
                "title": "Samsung Galaxy S24",
                "brand": "Samsung",
                "category": "Smartphones",
                "cost": "899.00 EUR",
                "imageUrl": "https://fakeimg.com/galaxy.jpg"
            }
        ]
    
    def test_normalization_step(self, sample_products):
        normalizer = ProductNormalizer()
        
        result = normalizer.normalize_batch(sample_products)
        result = run_if_async(result)
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        
        assert len(normalized) == 3
        assert all('id' in p for p in normalized)
        assert all('normalized_name' in p for p in normalized)
        assert normalized[0]['vendor_id'] == 'A'
    
    def test_enrichment_step(self, sample_products):
        normalizer = ProductNormalizer()
        enricher = ProductEnricher()
        
        result = normalizer.normalize_batch(sample_products)
        result = run_if_async(result)
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        
        result = enricher.enrich_batch(normalized)
        enriched = run_if_async(result)
        
        assert len(enriched) == 3
        assert all('name_embedding' in p for p in enriched)
        assert all(len(p['name_embedding']) == 384 for p in enriched)
    
    def test_duplicate_detection_step(self, sample_products):
        normalizer = ProductNormalizer()
        enricher = ProductEnricher()
        detector = DuplicateDetector(similarity_threshold=0.60)
        
        result = run_if_async(normalizer.normalize_batch(sample_products))
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        enriched = run_if_async(enricher.enrich_batch(normalized))
        duplicates = detector.detect_duplicates(enriched)
        
        assert isinstance(duplicates, list)
    
    def test_validation_step(self, sample_products):
        normalizer = ProductNormalizer()
        validator = ProductValidator()
        
        result = run_if_async(normalizer.normalize_batch(sample_products))
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        validated = validator.validate_batch(normalized)
        
        assert len(validated) == 3
        assert all('quality_score' in p for p in validated)
        assert all(0 <= p['quality_score'] <= 100 for p in validated)
    
    def test_full_pipeline_e2e(self, sample_products):
        normalizer = ProductNormalizer()
        enricher = ProductEnricher()
        detector = DuplicateDetector(similarity_threshold=0.60)
        validator = ProductValidator()
        
        result = run_if_async(normalizer.normalize_batch(sample_products))
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        assert len(normalized) == 3
        
        enriched = run_if_async(enricher.enrich_batch(normalized))
        assert len(enriched) == 3
        
        duplicates = detector.detect_duplicates(enriched)
        assert isinstance(duplicates, list)
        
        validated = validator.validate_batch(enriched)
        assert len(validated) == 3
        
        # All products preserved
        assert len(validated) == len(sample_products)
    
    def test_pipeline_with_real_data(self, tmp_path):
        input_file = Path("data/input/messy_products.json")
        
        if not input_file.exists():
            pytest.skip("messy_products.json not found")
        
        with open(input_file) as f:
            products = json.load(f)
        
        test_products = products[:10]
        
        normalizer = ProductNormalizer()
        enricher = ProductEnricher()
        detector = DuplicateDetector(similarity_threshold=0.60)
        validator = ProductValidator()
        
        result = run_if_async(normalizer.normalize_batch(test_products))
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        enriched = run_if_async(enricher.enrich_batch(normalized))
        duplicates = detector.detect_duplicates(enriched)
        validated = validator.validate_batch(enriched)
        
        # At least 80% success
        assert len(normalized) >= 8
        assert len(enriched) == len(normalized)
        assert len(validated) == len(enriched)


class TestErrorHandling:
    """Test error handling throughout pipeline"""
    
    def test_handles_malformed_json(self):
        """Test pipeline handles malformed data gracefully"""
        normalizer = ProductNormalizer()
        
        bad_products = [
            {"vendor_id": "A"},  # Missing name
            {"name": "Test"},     # Missing vendor_id
            {}                    # Empty
        ]
        
        result = normalizer.normalize_batch(bad_products)
        result = run_if_async(result)
        
        if isinstance(result, tuple):
            normalized, failures = result
            # Should have failures
            assert len(failures) > 0
            assert isinstance(normalized, list)
        else:
            assert isinstance(result, list)
    
    def test_handles_missing_embeddings(self):
        detector = DuplicateDetector()
        
        products_no_embeddings = [
            {"id": "1", "name": "Product 1", "normalized_name": "product 1"},
            {"id": "2", "name": "Product 2", "normalized_name": "product 2"}
        ]
        
        duplicates = detector.detect_duplicates(products_no_embeddings)
        assert isinstance(duplicates, list)


class TestLogging:
    
    def test_duplicate_detector_logs_results(self):
        detector = DuplicateDetector()
        products = [
            {"id": "1", "name": "Test", "normalized_name": "test", "name_embedding": [0.1] * 384},
            {"id": "2", "name": "Test", "normalized_name": "test", "name_embedding": [0.1] * 384}
        ]
        
        duplicates = detector.detect_duplicates(products)
        assert isinstance(duplicates, list)
        
        stats = detector.get_stats()
        assert 'total_products' in stats
        assert stats['total_products'] == 2


class TestDataIntegrity:
    
    def test_uuid_generation(self):
        normalizer = ProductNormalizer()
        products = [
            {"vendor_id": "A", "name": "Product 1"},
            {"vendor_id": "A", "name": "Product 2"},
            {"vendor_id": "B", "name": "Product 3"}
        ]
        
        result = run_if_async(normalizer.normalize_batch(products))
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        
        ids = [str(p['id']) for p in normalized]
        assert len(ids) == len(set(ids)) 
        assert all(len(id) > 0 for id in ids)
    
    def test_currency_detection(self):
        normalizer = ProductNormalizer()
        products = [
            {"vendor_id": "A", "name": "Test", "pricing": {"amount": "10.99"}},
            {"vendor_id": "B", "name": "Test", "price": "৳20.00"},
            {"vendor_id": "C", "name": "Test", "cost": "30.00 EUR"}
        ]
        
        result = run_if_async(normalizer.normalize_batch(products))
        
        if isinstance(result, tuple):
            normalized, failures = result
        else:
            normalized = result
        
        normalized = to_dict_list(normalized)
        
        currencies = [p.get('currency') for p in normalized]
        assert 'USD' in currencies or 'BDT' in currencies or 'EUR' in currencies
    
    def test_quality_scoring(self):
        """Test quality scoring assigns valid scores"""
        validator = ProductValidator()
        products = [
            {
                "id": "1",
                "vendor_id": "A",
                "name": "Test Product",
                "normalized_name": "test product",
                "category": "Electronics",
                "price": 99.99,
                "currency": "USD"
            }
        ]
        
        validated = validator.validate_batch(products)
        
        assert len(validated) == 1
        assert 'quality_score' in validated[0]
        assert 0 <= validated[0]['quality_score'] <= 100
        assert 'quality_level' in validated[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])