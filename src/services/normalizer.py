# from typing import Dict, Any, Optional, List, Tuple
# from decimal import Decimal, InvalidOperation
# from loguru import logger
# from src.models.product import MessyProduct, NormalizedProduct, ImageStatus
# import re
# from datetime import datetime

# class ProductNormalizer:
    
#     def __init__(self):
#         self.stats = {
#             "total": 0,
#             "success": 0,
#             "failed": 0,
#             "missing_fields": {}
#         }
    
#     def normalize(self, messy_product: Dict[str, Any]) -> Tuple[Optional[NormalizedProduct], List[str]]:
#         self.stats["total"] += 1
#         errors = []
        
#         try:
#             vendor_id = messy_product.get("vendor_id")
#             if not vendor_id:
#                 errors.append("Missing vendor_id")
#                 self.stats["failed"] += 1
#                 return None, errors
            
#             name = self._extract_name(messy_product, errors)
#             if not name:
#                 errors.append("Could not extract product name")
#                 self.stats["failed"] += 1
#                 return None, errors
            
#             brand = self._extract_brand(messy_product, errors)
            
#             category = self._extract_category(messy_product, errors)
            
#             price = self._extract_price(messy_product, errors)
            
#             image_url, image_status = self._extract_image(messy_product, errors)
            
#             normalized = NormalizedProduct(
#                 vendor_id=vendor_id,
#                 name=name,
#                 brand=brand,
#                 category=category,
#                 price=price,
#                 image_url=image_url,
#                 image_status=image_status,
#                 raw_data=messy_product,
#                 normalized_at=datetime.utcnow(),
#                 validation_errors=errors
#             )
            
#             if errors:
#                 logger.warning(f"Product normalized with {len(errors)} warnings: {name[:50]}")
#             else:
#                 logger.debug(f"Product normalized successfully: {name[:50]}")
            
#             self.stats["success"] += 1
#             return normalized, errors
            
#         except Exception as e:
#             errors.append(f"Unexpected error: {str(e)}")
#             logger.error(f"Normalization failed: {e}", exc_info=True)
#             self.stats["failed"] += 1
#             return None, errors
    
#     def _extract_name(self, data: Dict, errors: List[str]) -> Optional[str]:
#         possible_fields = ["name", "title", "productTitle", "product_name", "item_name"]
        
#         for field in possible_fields:
#             if field in data and data[field]:
#                 name = str(data[field]).strip()
#                 if name:
#                     return name
        
#         errors.append("Missing product name")
#         self._track_missing("name")
#         return None
    
#     def _extract_brand(self, data: Dict, errors: List[str]) -> Optional[str]:
#         possible_fields = ["brand", "brandName", "brand_name", "manufacturer"]
        
#         for field in possible_fields:
#             if field in data and data[field]:
#                 brand = str(data[field]).strip()
#                 brand = re.sub(r'\s+Inc\.?$', '', brand, flags=re.IGNORECASE)
#                 brand = re.sub(r'\s+', ' ', brand)
#                 if brand:
#                     return brand
        
#         errors.append("Missing brand")
#         self._track_missing("brand")
#         return None
    
#     def _extract_category(self, data: Dict, errors: List[str]) -> Optional[str]:
#         if "category_path" in data and isinstance(data["category_path"], list):
#             return data["category_path"][-1] if data["category_path"] else None
        
#         possible_fields = ["category", "dept", "department", "cat"]
#         for field in possible_fields:
#             if field in data and data[field]:
#                 return str(data[field]).strip()
        
#         errors.append("Missing category")
#         self._track_missing("category")
#         return None
    
#     def _extract_price(self, data: Dict, errors: List[str]) -> Optional[Decimal]:
#         if "pricing" in data and isinstance(data["pricing"], dict):
#             if "value" in data["pricing"]:
#                 try:
#                     return Decimal(str(data["pricing"]["value"]))
#                 except (InvalidOperation, ValueError):
#                     errors.append(f"Invalid price value: {data['pricing']['value']}")
        
#         possible_fields = ["price", "cost", "amount", "value"]
#         for field in possible_fields:
#             if field in data and data[field]:
#                 try:
#                     price_str = str(data[field])
#                     match = re.search(r'(\d+\.?\d*)', price_str)
#                     if match:
#                         price = Decimal(match.group(1))
#                         if price >= 0:
#                             return price
#                         else:
#                             errors.append(f"Negative price: {price}")
#                 except (InvalidOperation, ValueError, AttributeError):
#                     errors.append(f"Invalid price format: {data[field]}")
        
#         errors.append("Missing or invalid price")
#         self._track_missing("price")
#         return None
    
#     def _extract_image(self, data: Dict, errors: List[str]) -> Tuple[Optional[str], ImageStatus]:
#         possible_fields = ["img_url", "image_url", "image", "img", "picture"]
        
#         for field in possible_fields:
#             if field in data:
#                 url = data[field]
#                 if not url or url == "":
#                     return None, ImageStatus.MISSING
                
#                 url = str(url).strip()
                
#                 if not url.startswith(("http://", "https://")):
#                     errors.append(f"Invalid image URL format: {url[:50]}")
#                     return url, ImageStatus.BROKEN
                
#                 if "fakeimg.com" in url or "placeholder" in url.lower():
#                     return url, ImageStatus.PENDING 
                
#                 return url, ImageStatus.PENDING  
        
#         errors.append("Missing image URL")
#         self._track_missing("image_url")
#         return None, ImageStatus.MISSING
    
#     def _track_missing(self, field: str):
#         if field not in self.stats["missing_fields"]:
#             self.stats["missing_fields"][field] = 0
#         self.stats["missing_fields"][field] += 1
    
#     def get_stats(self) -> Dict[str, Any]:
#         success_rate = (self.stats["success"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0
#         return {
#             **self.stats,
#             "success_rate": round(success_rate, 2)
#         }
    
#     async def normalize_batch(self, messy_products: List[Dict[str, Any]]) -> Tuple[List[NormalizedProduct], List[Dict]]:
#         normalized = []
#         failed = []
        
#         for messy in messy_products:
#             result, errors = self.normalize(messy)
#             if result:
#                 normalized.append(result)
#             else:
#                 failed.append({"product": messy, "errors": errors})
        
#         logger.info(f"Normalization complete: {len(normalized)}/{len(messy_products)} succeeded")
#         return normalized, failed

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, InvalidOperation
from loguru import logger
from src.models.product import MessyProduct, NormalizedProduct, ImageStatus
import re
from datetime import datetime
import uuid

class ProductNormalizer:
  
   def __init__(self):
       self.stats = {
           "total": 0,
           "success": 0,
           "failed": 0,
           "missing_fields": {}
       }
  
   def normalize(self, messy_product: Dict[str, Any]) -> Tuple[Optional[NormalizedProduct], List[str]]:
       self.stats["total"] += 1
       errors = []
      
       try:
           vendor_id = messy_product.get("vendor_id")
           if not vendor_id:
               errors.append("Missing vendor_id")
               self.stats["failed"] += 1
               return None, errors
           
           product_id = str(uuid.uuid4())

           name = self._extract_name(messy_product, errors)
           if not name:
               errors.append("Could not extract product name")
               self.stats["failed"] += 1
               return None, errors
          
           brand = self._extract_brand(messy_product, errors)
           normalized_name = name.lower().strip() if name else None
           brand_normalized = brand.lower().strip() if brand else None
           category = self._extract_category(messy_product, errors)
           price = self._extract_price(messy_product, errors)
           currency = self._extract_currency(messy_product, errors)
           image_url, image_status = self._extract_image(messy_product, errors)
          
           normalized = NormalizedProduct(
               id=product_id,
               vendor_id=vendor_id,
               name=name,
               normalized_name=normalized_name,
               brand=brand,
               brand_normalized=brand_normalized,
               category=category,
               price=price,
               currency=currency,
               image_url=image_url,
               image_status=image_status,
               raw_data=messy_product,
               normalized_at=datetime.utcnow(),
               validation_errors=errors
           )
          
           if errors:
               logger.warning(f"Product normalized with {len(errors)} warnings: {name[:50]}")
           else:
               logger.debug(f"Product normalized successfully: {name[:50]}")
          
           self.stats["success"] += 1
           return normalized, errors
          
       except Exception as e:
           errors.append(f"Unexpected error: {str(e)}")
           logger.error(f"Normalization failed: {e}", exc_info=True)
           self.stats["failed"] += 1
           return None, errors
  
   def _extract_name(self, data: Dict, errors: List[str]) -> Optional[str]:
       possible_fields = ["name", "title", "productTitle", "product_name", "item_name"]
      
       for field in possible_fields:
           if field in data and data[field]:
               name = str(data[field]).strip()
               if name:
                   return name
      
       errors.append("Missing product name")
       self._track_missing("name")
       return None
  
   def _extract_brand(self, data: Dict, errors: List[str]) -> Optional[str]:
       possible_fields = ["brand", "brandName", "brand_name", "manufacturer"]
      
       for field in possible_fields:
           if field in data and data[field]:
               brand = str(data[field]).strip()
               brand = re.sub(r'\s+Inc\.?$', '', brand, flags=re.IGNORECASE)
               brand = re.sub(r'\s+', ' ', brand)
               if brand:
                   return brand
      
       errors.append("Missing brand")
       self._track_missing("brand")
       return None
  
   def _extract_category(self, data: Dict, errors: List[str]) -> Optional[str]:
       if "category_path" in data and isinstance(data["category_path"], list):
           if data["category_path"]:
               return data["category_path"][-1]
           else:
               errors.append("Missing category")
               self._track_missing("category")
               return None
      
       possible_fields = ["category", "dept", "department", "cat"]
       for field in possible_fields:
           if field in data and data[field]:
               return str(data[field]).strip()
      
       errors.append("Missing category")
       self._track_missing("category")
       return None
   
   def _extract_price(self, data: Dict, errors: List[str]) -> Optional[Decimal]:
       if "pricing" in data and isinstance(data["pricing"], dict):
           if "value" in data["pricing"]:
               try:
                   return Decimal(str(data["pricing"]["value"]))
               except (InvalidOperation, ValueError):
                   errors.append(f"Invalid price value: {data['pricing']['value']}")
      
       possible_fields = ["price", "cost", "amount", "value"]
       for field in possible_fields:
           if field in data and data[field]:
               try:
                   price_str = str(data[field])
                   price_str = price_str.replace(',', '')
                   
                   match = re.search(r'(-?\d+\.?\d*)', price_str)
                   
                   if match:
                       matched_num = match.group(1)
                       start_pos = match.start(1)

                       before = price_str[:start_pos]
                       if re.search(r'[a-zA-Z]', before):
                           errors.append(f"Invalid price format: {data[field]}")
                           continue
                       
                       price = Decimal(matched_num)
                       if price < 0:
                           errors.append(f"Negative price: {price}")
                           continue
                       return price
                   else:
                       errors.append(f"Invalid price format: {data[field]}")
               except (InvalidOperation, ValueError, AttributeError):
                   errors.append(f"Invalid price format: {data[field]}")
      
       errors.append("Missing or invalid price")
       self._track_missing("price")
       return None
   
   def _extract_currency(self, data: Dict, errors: List[str]) -> Optional[str]:
    if "pricing" in data and isinstance(data["pricing"], dict):
        currency = data["pricing"].get("currency")
        if currency:
            return currency.upper()
    
    possible_fields = ["price", "cost", "amount"]
    
    for field in possible_fields:
        if field in data and data[field]:
            value_str = str(data[field]).strip()
            
            currency_pattern = r'\b([A-Z]{3})\b'
            match = re.search(currency_pattern, value_str)
            
            if match:
                currency = match.group(1)
                known_currencies = ['USD', 'EUR', 'GBP', 'BDT', 'INR', 'JPY', 'CNY']
                if currency in known_currencies:
                    return currency
    
    errors.append("Currency not found, defaulting to BDT")
    return "BDT"
  
   def _extract_image(self, data: Dict, errors: List[str]) -> Tuple[Optional[str], ImageStatus]:
       possible_fields = ["img_url", "image_url", "image", "img", "picture"]
      
       for field in possible_fields:
           if field in data:
               url = data[field]
               if not url or url == "":
                   errors.append("Missing image URL")
                   self._track_missing("image_url")
                   return None, ImageStatus.MISSING
              
               url = str(url).strip()
              
               if not url.startswith(("http://", "https://")):
                   errors.append(f"Invalid image URL format: {url[:50]}")
                   return url, ImageStatus.BROKEN
              
               if "fakeimg.com" in url or "placeholder" in url.lower():
                   return url, ImageStatus.PENDING
              
               return url, ImageStatus.PENDING 
      
       errors.append("Missing image URL")
       self._track_missing("image_url")
       return None, ImageStatus.MISSING
  
   def _track_missing(self, field: str):
       if field not in self.stats["missing_fields"]:
           self.stats["missing_fields"][field] = 0
       self.stats["missing_fields"][field] += 1
  
   def get_stats(self) -> Dict[str, Any]:
       success_rate = (self.stats["success"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0
       return {
           **self.stats,
           "success_rate": round(success_rate, 2)
       }
  
   async def normalize_batch(self, messy_products: List[Dict[str, Any]]) -> Tuple[List[NormalizedProduct], List[Dict]]:
       normalized = []
       failed = []
      
       for messy in messy_products:
           result, errors = self.normalize(messy)
           if result:
               normalized.append(result)
           else:
               failed.append({"product": messy, "errors": errors})
      
       logger.info(f"Normalization complete: {len(normalized)}/{len(messy_products)} succeeded")
       return normalized, failed


