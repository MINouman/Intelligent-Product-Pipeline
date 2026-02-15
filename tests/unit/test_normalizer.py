"""
Unit Tests for ProductNormalizer

This test suite provides comprehensive coverage of the ProductNormalizer class,
testing all vendor formats, edge cases, error handling, and statistics tracking.

Run with:
    pytest tests/unit/test_normalizer.py -v
    pytest tests/unit/test_normalizer.py -v --cov=src.services.normalizer --cov-report=html

Coverage target: 90%+ for normalizer module
"""
import pytest
from decimal import Decimal
from datetime import datetime
from src.services.normalizer import ProductNormalizer
from src.models.product import NormalizedProduct, ImageStatus


class TestVendorAFormat:
    """Test normalization of Vendor A format."""
    
    @pytest.fixture
    def normalizer(self):
        """Create normalizer instance."""
        return ProductNormalizer()
    
    def test_vendor_a_complete_product(self, normalizer):
        """Test normalizing a complete Vendor A product."""
        messy = {
            "vendor_id": "A",
            "productTitle": "iPhone 15 Pro",
            "brandName": "Apple Inc.",
            "category_path": ["Electronics", "Phones"],
            "pricing": {"value": 999.99, "currency": "BDT"},
            "img_url": "http://example.com/iphone.jpg"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is not None
        assert result.name == "iPhone 15 Pro"
        assert result.brand == "Apple"  # "Inc." should be removed
        assert result.category == "Phones"  # Last item in category_path
        assert result.price == Decimal("999.99")
        assert result.currency == "BDT"
        assert result.vendor_id == "A"
        assert result.image_url == "http://example.com/iphone.jpg"
        assert result.image_status == ImageStatus.PENDING
        assert len(errors) == 0
    
    def test_vendor_a_brand_normalization(self, normalizer):
        """Test brand name normalization (removes Inc., Ltd., etc.)."""
        test_cases = [
            ("Apple Inc.", "Apple"),
            ("Samsung Inc", "Samsung"),
            ("Sony Corporation", "Sony Corporation"),  # Only Inc. is removed
            ("Microsoft  Inc.", "Microsoft"),  # Extra spaces
        ]
        
        for input_brand, expected_brand in test_cases:
            messy = {
                "vendor_id": "A",
                "productTitle": "Test Product",
                "brandName": input_brand,
                "pricing": {"value": 100}
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.brand == expected_brand, f"Failed for {input_brand}"
    
    def test_vendor_a_category_path_extraction(self, normalizer):
        """Test category extraction from array path."""
        test_cases = [
            (["Electronics"], "Electronics"),
            (["Electronics", "Phones"], "Phones"),
            (["Home", "Kitchen", "Appliances"], "Appliances"),
            ([], None),
        ]
        
        for category_path, expected in test_cases:
            messy = {
                "vendor_id": "A",
                "productTitle": "Test",
                "category_path": category_path,
                "pricing": {"value": 100}
            }
            
            result, errors = normalizer.normalize(messy)
            
            if expected:
                assert result.category == expected
            else:
                assert result.category is None
                assert any("category" in e.lower() for e in errors)
    
    def test_vendor_a_pricing_object(self, normalizer):
        """Test pricing object extraction."""
        test_cases = [
            ({"value": 999.99, "currency": "BDT"}, Decimal("999.99")),
            ({"value": 100, "currency": "USD"}, Decimal("100")),
            ({"value": 0.99}, Decimal("0.99")),
            ({"value": "123.45"}, Decimal("123.45")),  # String value
        ]
        
        for pricing, expected_price in test_cases:
            messy = {
                "vendor_id": "A",
                "productTitle": "Test",
                "pricing": pricing
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.price == expected_price
    
    def test_vendor_a_missing_optional_fields(self, normalizer):
        """Test handling missing optional fields."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Minimal Product",
            "pricing": {"value": 50}
            # Missing: brand, category_path, img_url
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is not None
        assert result.name == "Minimal Product"
        assert result.brand is None
        assert result.category is None
        assert result.price == Decimal("50")
        assert result.image_url is None
        assert result.image_status == ImageStatus.MISSING
        
        # Should have warnings for missing fields
        assert len(errors) >= 3  # brand, category, image


class TestVendorBFormat:
    """Test normalization of Vendor B format."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_vendor_b_complete_product(self, normalizer):
        """Test normalizing a complete Vendor B product."""
        messy = {
            "vendor_id": "B",
            "name": "Samsung Galaxy S24",
            "brand": "Samsung",
            "dept": "Electronics",
            "price": "899.50 BDT",
            "img_url": "http://example.com/samsung.jpg"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is not None
        assert result.name == "Samsung Galaxy S24"
        assert result.brand == "Samsung"
        assert result.category == "Electronics"  # dept → category
        assert result.price == Decimal("899.50")
        assert result.vendor_id == "B"
        assert result.image_url == "http://example.com/samsung.jpg"
    
    def test_vendor_b_price_string_with_currency(self, normalizer):
        """Test parsing price strings with currency suffix."""
        test_cases = [
            ("899.50 BDT", Decimal("899.50")),
            ("1234.99 BDT", Decimal("1234.99")),
            ("99 BDT", Decimal("99")),
            ("0.99 BDT", Decimal("0.99")),
            ("1,234.56 BDT", Decimal("1234.56")),  # With comma
        ]
        
        for price_str, expected in test_cases:
            messy = {
                "vendor_id": "B",
                "name": "Test",
                "price": price_str
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.price == expected, f"Failed for {price_str}"
    
    def test_vendor_b_empty_image_url(self, normalizer):
        """Test handling empty image URL."""
        messy = {
            "vendor_id": "B",
            "name": "Test Product",
            "price": "100 BDT",
            "img_url": ""  # Empty string
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result.image_url is None
        assert result.image_status == ImageStatus.MISSING
        assert any("image" in e.lower() for e in errors)
    
    def test_vendor_b_dept_to_category_mapping(self, normalizer):
        """Test department field maps to category."""
        departments = ["Electronics", "Home", "Kitchen", "Books"]
        
        for dept in departments:
            messy = {
                "vendor_id": "B",
                "name": "Test",
                "dept": dept,
                "price": "100 BDT"
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.category == dept


class TestVendorCFormat:
    """Test normalization of Vendor C format."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_vendor_c_complete_product(self, normalizer):
        """Test normalizing a complete Vendor C product."""
        messy = {
            "vendor_id": "C",
            "title": "Sony WH-1000XM5",
            "brand": "Sony",
            "category": "Audio",
            "cost": "399.99 BDT",
            "img_url": "http://example.com/sony.jpg"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is not None
        assert result.name == "Sony WH-1000XM5"
        assert result.brand == "Sony"
        assert result.category == "Audio"
        assert result.price == Decimal("399.99")
        assert result.vendor_id == "C"
    
    def test_vendor_c_title_field(self, normalizer):
        """Test 'title' field maps to name."""
        messy = {
            "vendor_id": "C",
            "title": "Product Title Here",
            "cost": "50 BDT"
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.name == "Product Title Here"
    
    def test_vendor_c_cost_field(self, normalizer):
        """Test 'cost' field maps to price."""
        test_cases = [
            ("299.99 BDT", Decimal("299.99")),
            ("100 BDT", Decimal("100")),
            ("1234.56 BDT", Decimal("1234.56")),
        ]
        
        for cost_str, expected in test_cases:
            messy = {
                "vendor_id": "C",
                "title": "Test",
                "cost": cost_str
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.price == expected
    
    def test_vendor_c_fakeimg_url(self, normalizer):
        """Test handling of fakeimg.com URLs."""
        messy = {
            "vendor_id": "C",
            "title": "Test",
            "cost": "100 BDT",
            "img_url": "http://fakeimg.com/abc123.jpg"
        }
        
        result, _ = normalizer.normalize(messy)
        
        # fakeimg.com URLs should be marked as PENDING (needs validation)
        assert result.image_url == "http://fakeimg.com/abc123.jpg"
        assert result.image_status == ImageStatus.PENDING


class TestVendorDFormat:
    """Test normalization of Vendor D format."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_vendor_d_complete_product(self, normalizer):
        """Test normalizing a complete Vendor D product."""
        messy = {
            "vendor_id": "D",
            "name": "ASUS ROG Laptop",
            "brand": "Asus",
            "category": "Computers",
            "price": "1500",
            "img_url": "https://example.com/laptop.jpg"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is not None
        assert result.name == "ASUS ROG Laptop"
        assert result.brand == "Asus"
        assert result.category == "Computers"
        assert result.price == Decimal("1500")
    
    def test_vendor_d_numeric_price(self, normalizer):
        """Test numeric price without currency string."""
        test_cases = [
            ("1500", Decimal("1500")),
            ("99.99", Decimal("99.99")),
            ("0.50", Decimal("0.50")),
        ]
        
        for price_str, expected in test_cases:
            messy = {
                "vendor_id": "D",
                "name": "Test",
                "price": price_str
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.price == expected


class TestFieldExtraction:
    """Test field extraction logic for all vendors."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_name_field_priority(self, normalizer):
        """Test name extraction tries multiple fields in order."""
        # Priority: name > title > productTitle
        test_cases = [
            ({"name": "Name", "title": "Title"}, "Name"),
            ({"title": "Title", "productTitle": "ProductTitle"}, "Title"),
            ({"productTitle": "ProductTitle"}, "ProductTitle"),
            ({"product_name": "ProductName"}, "ProductName"),
            ({"item_name": "ItemName"}, "ItemName"),
        ]
        
        for fields, expected_name in test_cases:
            messy = {"vendor_id": "A", **fields, "pricing": {"value": 100}}
            result, _ = normalizer.normalize(messy)
            assert result.name == expected_name
    
    def test_brand_field_priority(self, normalizer):
        """Test brand extraction tries multiple fields."""
        test_cases = [
            ({"brand": "Brand1", "brandName": "Brand2"}, "Brand1"),
            ({"brandName": "BrandName"}, "BrandName"),
            ({"brand_name": "brand_name"}, "brand_name"),
        ]
        
        for fields, expected_brand in test_cases:
            messy = {"vendor_id": "A", "productTitle": "Test", **fields}
            result, _ = normalizer.normalize(messy)
            assert result.brand == expected_brand
    
    def test_category_field_priority(self, normalizer):
        """Test category extraction tries multiple fields."""
        test_cases = [
            ({"category": "Cat1", "dept": "Dept1"}, "Cat1"),
            ({"dept": "Department"}, "Department"),
            ({"department": "Full Department"}, "Full Department"),
        ]
        
        for fields, expected_category in test_cases:
            messy = {"vendor_id": "A", "productTitle": "Test", **fields}
            result, _ = normalizer.normalize(messy)
            assert result.category == expected_category
    
    def test_price_field_priority(self, normalizer):
        """Test price extraction tries multiple fields."""
        test_cases = [
            ({"price": "100 BDT", "cost": "200 BDT"}, Decimal("100")),
            ({"cost": "150 BDT"}, Decimal("150")),
            ({"amount": "75.50"}, Decimal("75.50")),
            ({"value": "99"}, Decimal("99")),
        ]
        
        for fields, expected_price in test_cases:
            messy = {"vendor_id": "A", "productTitle": "Test", **fields}
            result, _ = normalizer.normalize(messy)
            assert result.price == expected_price
    
    def test_image_url_field_priority(self, normalizer):
        """Test image URL extraction tries multiple fields."""
        test_cases = [
            ({"img_url": "url1", "image_url": "url2"}, "url1"),
            ({"image_url": "image_url"}, "image_url"),
            ({"image": "image"}, "image"),
            ({"img": "img"}, "img"),
        ]
        
        for fields, expected_url in test_cases:
            messy = {"vendor_id": "A", "productTitle": "Test", **fields}
            result, _ = normalizer.normalize(messy)
            assert result.image_url == expected_url


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_missing_vendor_id(self, normalizer):
        """Test that missing vendor_id causes failure."""
        messy = {
            "name": "Product",
            "price": "100"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is None
        assert any("vendor_id" in e.lower() for e in errors)
    
    def test_missing_product_name(self, normalizer):
        """Test that missing product name causes failure."""
        messy = {
            "vendor_id": "A",
            "price": "100"
            # No name/title/productTitle
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is None
        assert any("name" in e.lower() for e in errors)
    
    def test_empty_product_name(self, normalizer):
        """Test that empty product name causes failure."""
        messy = {
            "vendor_id": "A",
            "name": "",  # Empty string
            "price": "100"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is None
        assert any("name" in e.lower() for e in errors)
    
    def test_whitespace_only_name(self, normalizer):
        """Test that whitespace-only name causes failure."""
        messy = {
            "vendor_id": "A",
            "name": "   ",  # Only whitespace
            "price": "100"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is None
        assert any("name" in e.lower() for e in errors)
    
    def test_invalid_price_format(self, normalizer):
        """Test handling of invalid price formats."""
        test_cases = [
            "not a number",
            "abc123",
            "BDT 100",  # Currency before number
            "##.##",
        ]
        
        for invalid_price in test_cases:
            messy = {
                "vendor_id": "A",
                "name": "Test",
                "price": invalid_price
            }
            
            result, errors = normalizer.normalize(messy)
            
            # Should succeed but with None price and error
            assert result is not None
            assert result.price is None
            assert any("price" in e.lower() for e in errors)
    
    def test_negative_price(self, normalizer):
        """Test handling of negative prices."""
        messy = {
            "vendor_id": "A",
            "name": "Test",
            "price": "-100"
        }
        
        result, errors = normalizer.normalize(messy)
        
        # Should fail validation or set to None
        assert result is not None
        assert any("price" in e.lower() or "negative" in e.lower() for e in errors)
    
    def test_zero_price(self, normalizer):
        """Test handling of zero price (should be allowed)."""
        messy = {
            "vendor_id": "A",
            "name": "Free Product",
            "price": "0"
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is not None
        assert result.price == Decimal("0")
    
    def test_invalid_image_url_format(self, normalizer):
        """Test handling of invalid URL formats."""
        test_cases = [
            "not-a-url",
            "ftp://wrong-protocol.com",
            "just-text",
            "www.missing-protocol.com",
        ]
        
        for invalid_url in test_cases:
            messy = {
                "vendor_id": "A",
                "name": "Test",
                "img_url": invalid_url
            }
            
            result, errors = normalizer.normalize(messy)
            
            assert result is not None
            assert result.image_status == ImageStatus.BROKEN
            assert any("image" in e.lower() or "url" in e.lower() for e in errors)
    
    def test_valid_url_formats(self, normalizer):
        """Test valid URL formats are accepted."""
        valid_urls = [
            "http://example.com/image.jpg",
            "https://secure.example.com/photo.png",
            "http://cdn.example.com/path/to/image.gif",
        ]
        
        for url in valid_urls:
            messy = {
                "vendor_id": "A",
                "name": "Test",
                "img_url": url
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.image_url == url
            assert result.image_status == ImageStatus.PENDING
    
    def test_unexpected_exception_handling(self, normalizer):
        """Test that unexpected exceptions are caught and reported."""
        # This should cause an exception during normalization
        messy = {
            "vendor_id": "A",
            "name": "Test",
            "pricing": {"value": None}  # None value might cause issues
        }
        
        result, errors = normalizer.normalize(messy)
        
        # Should not crash, should return errors
        assert isinstance(errors, list)


class TestPriceExtraction:
    """Test price extraction edge cases."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_price_with_commas(self, normalizer):
        """Test prices with thousand separators."""
        test_cases = [
            ("1,234.56 BDT", Decimal("1234.56")),
            ("10,000 BDT", Decimal("10000")),
            ("999,999.99 BDT", Decimal("999999.99")),
        ]
        
        for price_str, expected in test_cases:
            messy = {
                "vendor_id": "A",
                "name": "Test",
                "price": price_str
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.price == expected
    
    def test_price_without_decimal(self, normalizer):
        """Test whole number prices."""
        test_cases = [
            ("100 BDT", Decimal("100")),
            ("1500", Decimal("1500")),
            ("99", Decimal("99")),
        ]
        
        for price_str, expected in test_cases:
            messy = {
                "vendor_id": "A",
                "name": "Test",
                "price": price_str
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.price == expected
    
    def test_price_with_many_decimals(self, normalizer):
        """Test prices with more than 2 decimal places."""
        messy = {
            "vendor_id": "A",
            "name": "Test",
            "price": "99.999999 BDT"
        }
        
        result, _ = normalizer.normalize(messy)
        
        # Should extract first occurrence of number
        assert result.price is not None
        assert float(result.price) == pytest.approx(99.999999)
    
    def test_price_from_pricing_object_string_value(self, normalizer):
        """Test pricing object with string value."""
        messy = {
            "vendor_id": "A",
            "name": "Test",
            "pricing": {"value": "123.45", "currency": "BDT"}
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.price == Decimal("123.45")
    
    def test_price_from_pricing_object_int_value(self, normalizer):
        """Test pricing object with integer value."""
        messy = {
            "vendor_id": "A",
            "name": "Test",
            "pricing": {"value": 999, "currency": "BDT"}
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.price == Decimal("999")
    
    def test_price_from_pricing_object_float_value(self, normalizer):
        """Test pricing object with float value."""
        messy = {
            "vendor_id": "A",
            "name": "Test",
            "pricing": {"value": 99.99, "currency": "BDT"}
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.price == Decimal("99.99")


class TestBrandNormalization:
    """Test brand name normalization."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_remove_inc_suffix(self, normalizer):
        """Test removal of 'Inc.' suffix."""
        test_cases = [
            ("Apple Inc.", "Apple"),
            ("Apple Inc", "Apple"),
            ("Microsoft Inc.", "Microsoft"),
            ("Samsung Inc", "Samsung"),
        ]
        
        for input_brand, expected in test_cases:
            messy = {
                "vendor_id": "A",
                "name": "Test",
                "brand": input_brand
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.brand == expected
    
    def test_normalize_multiple_spaces(self, normalizer):
        """Test normalization of multiple spaces in brand."""
        messy = {
            "vendor_id": "A",
            "name": "Test",
            "brand": "Sony   Corporation"  # Multiple spaces
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.brand == "Sony Corporation"
    
    def test_preserve_other_suffixes(self, normalizer):
        """Test that other suffixes are preserved."""
        test_cases = [
            ("Sony Corporation", "Sony Corporation"),
            ("Samsung Electronics", "Samsung Electronics"),
            ("Apple LLC", "Apple LLC"),
        ]
        
        for brand in test_cases:
            messy = {
                "vendor_id": "A",
                "name": "Test",
                "brand": brand[0]
            }
            
            result, _ = normalizer.normalize(messy)
            assert result.brand == brand[1]


class TestStatistics:
    """Test statistics tracking."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_stats_initialization(self, normalizer):
        """Test statistics are initialized correctly."""
        stats = normalizer.get_stats()
        
        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["failed"] == 0
        assert "missing_fields" in stats
    
    def test_stats_successful_normalization(self, normalizer):
        """Test stats tracking for successful normalization."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "pricing": {"value": 100}
        }
        
        normalizer.normalize(messy)
        stats = normalizer.get_stats()
        
        assert stats["total"] == 1
        assert stats["success"] == 1
        assert stats["failed"] == 0
    
    def test_stats_failed_normalization(self, normalizer):
        """Test stats tracking for failed normalization."""
        messy = {"vendor_id": "A"}  # Missing name
        
        normalizer.normalize(messy)
        stats = normalizer.get_stats()
        
        assert stats["total"] == 1
        assert stats["success"] == 0
        assert stats["failed"] == 1
    
    def test_stats_success_rate_calculation(self, normalizer):
        """Test success rate calculation."""
        products = [
            {"vendor_id": "A", "productTitle": "P1", "pricing": {"value": 100}},
            {"vendor_id": "A", "productTitle": "P2", "pricing": {"value": 100}},
            {"vendor_id": "A", "productTitle": "P3", "pricing": {"value": 100}},
            {"vendor_id": "A"},  # Will fail
            {"vendor_id": "A"},  # Will fail
        ]
        
        for product in products:
            normalizer.normalize(product)
        
        stats = normalizer.get_stats()
        
        assert stats["total"] == 5
        assert stats["success"] == 3
        assert stats["failed"] == 2
        assert stats["success_rate"] == 60.0  # 3/5 = 60%
    
    def test_stats_missing_fields_tracking(self, normalizer):
        """Test tracking of missing fields."""
        products = [
            {"vendor_id": "A", "productTitle": "P1"},  # Missing price, brand, category, image
            {"vendor_id": "A", "productTitle": "P2"},  # Missing price, brand, category, image
            {"vendor_id": "A", "productTitle": "P3", "pricing": {"value": 100}},  # Missing brand, category, image
        ]
        
        for product in products:
            normalizer.normalize(product)
        
        stats = normalizer.get_stats()
        missing = stats["missing_fields"]
        
        assert missing["price"] == 2
        assert missing["brand"] == 3
        assert missing["category"] == 3
        assert missing["image_url"] == 3


class TestBatchNormalization:
    """Test batch normalization functionality."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    @pytest.mark.asyncio
    async def test_normalize_batch_all_success(self, normalizer):
        """Test batch normalization with all successful products."""
        products = [
            {"vendor_id": "A", "productTitle": f"Product {i}", "pricing": {"value": i * 100}}
            for i in range(1, 6)
        ]
        
        normalized, failed = await normalizer.normalize_batch(products)
        
        assert len(normalized) == 5
        assert len(failed) == 0
        
        for i, product in enumerate(normalized, 1):
            assert product.name == f"Product {i}"
            assert product.price == Decimal(i * 100)
    
    @pytest.mark.asyncio
    async def test_normalize_batch_mixed_results(self, normalizer):
        """Test batch normalization with mixed success/failure."""
        products = [
            {"vendor_id": "A", "productTitle": "Product 1", "pricing": {"value": 100}},
            {"vendor_id": "A"},  # Missing name - will fail
            {"vendor_id": "A", "productTitle": "Product 3", "pricing": {"value": 300}},
            {"vendor_id": "A"},  # Missing name - will fail
            {"vendor_id": "A", "productTitle": "Product 5", "pricing": {"value": 500}},
        ]
        
        normalized, failed = await normalizer.normalize_batch(products)
        
        assert len(normalized) == 3
        assert len(failed) == 2
        
        # Check failed products have error info
        for failure in failed:
            assert "product" in failure
            assert "errors" in failure
            assert len(failure["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_normalize_batch_empty_list(self, normalizer):
        """Test batch normalization with empty list."""
        normalized, failed = await normalizer.normalize_batch([])
        
        assert len(normalized) == 0
        assert len(failed) == 0
    
    @pytest.mark.asyncio
    async def test_normalize_batch_statistics(self, normalizer):
        """Test that batch normalization updates statistics correctly."""
        products = [
            {"vendor_id": "A", "productTitle": f"Product {i}", "pricing": {"value": 100}}
            for i in range(10)
        ]
        
        await normalizer.normalize_batch(products)
        
        stats = normalizer.get_stats()
        assert stats["total"] == 10
        assert stats["success"] == 10
        assert stats["success_rate"] == 100.0


class TestRawDataStorage:
    """Test that raw data is preserved."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_raw_data_preserved(self, normalizer):
        """Test that original messy data is stored in raw_data."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "pricing": {"value": 100},
            "extra_field": "extra_value",
            "another_field": 123
        }
        
        result, _ = normalizer.normalize(messy)
        
        assert result.raw_data == messy
        assert result.raw_data["extra_field"] == "extra_value"
        assert result.raw_data["another_field"] == 123
    
    def test_normalized_at_timestamp(self, normalizer):
        """Test that normalized_at timestamp is set."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "pricing": {"value": 100}
        }
        
        before = datetime.utcnow()
        result, _ = normalizer.normalize(messy)
        after = datetime.utcnow()
        
        assert result.normalized_at is not None
        assert before <= result.normalized_at <= after
    
    def test_validation_errors_stored(self, normalizer):
        """Test that validation errors are stored in the model."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "price": "invalid_price"  # Will cause error
        }
        
        result, errors = normalizer.normalize(messy)
        
        assert result is not None
        assert len(result.validation_errors) > 0
        assert result.validation_errors == errors


class TestImageStatus:
    """Test image status determination."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_missing_image(self, normalizer):
        """Test missing image URL."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "pricing": {"value": 100}
            # No img_url
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.image_status == ImageStatus.MISSING
    
    def test_empty_string_image(self, normalizer):
        """Test empty string image URL."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "img_url": ""
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.image_status == ImageStatus.MISSING
    
    def test_valid_http_url(self, normalizer):
        """Test valid HTTP URL."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "img_url": "http://example.com/image.jpg"
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.image_status == ImageStatus.PENDING
    
    def test_valid_https_url(self, normalizer):
        """Test valid HTTPS URL."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "img_url": "https://secure.example.com/image.png"
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.image_status == ImageStatus.PENDING
    
    def test_invalid_protocol(self, normalizer):
        """Test invalid protocol."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "img_url": "ftp://example.com/image.jpg"
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.image_status == ImageStatus.BROKEN
    
    def test_no_protocol(self, normalizer):
        """Test URL without protocol."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "img_url": "example.com/image.jpg"
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.image_status == ImageStatus.BROKEN
    
    def test_fakeimg_url(self, normalizer):
        """Test fakeimg.com URL (marked as PENDING for validation)."""
        messy = {
            "vendor_id": "A",
            "productTitle": "Test",
            "img_url": "http://fakeimg.com/test.jpg"
        }
        
        result, _ = normalizer.normalize(messy)
        assert result.image_status == ImageStatus.PENDING


# Test fixtures for integration with real data
class TestRealDataScenarios:
    """Test with realistic data scenarios."""
    
    @pytest.fixture
    def normalizer(self):
        return ProductNormalizer()
    
    def test_normalize_mixed_vendor_formats(self, normalizer):
        """Test normalizing products from all vendor formats."""
        products = [
            # Vendor A
            {
                "vendor_id": "A",
                "productTitle": "iPhone 15 Pro",
                "brandName": "Apple Inc.",
                "category_path": ["Electronics", "Phones"],
                "pricing": {"value": 999.99}
            },
            # Vendor B
            {
                "vendor_id": "B",
                "name": "Samsung Galaxy S24",
                "brand": "Samsung",
                "dept": "Electronics",
                "price": "899.50 BDT"
            },
            # Vendor C
            {
                "vendor_id": "C",
                "title": "Sony Headphones",
                "brand": "Sony",
                "category": "Audio",
                "cost": "299.99 BDT"
            },
            # Vendor D
            {
                "vendor_id": "D",
                "name": "ASUS Laptop",
                "brand": "Asus",
                "category": "Computers",
                "price": "1500"
            }
        ]
        
        results = []
        for product in products:
            result, _ = normalizer.normalize(product)
            results.append(result)
        
        # All should succeed
        assert all(r is not None for r in results)
        
        # Verify each vendor's product
        assert results[0].name == "iPhone 15 Pro"
        assert results[1].name == "Samsung Galaxy S24"
        assert results[2].name == "Sony Headphones"
        assert results[3].name == "ASUS Laptop"


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=src.services.normalizer",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])