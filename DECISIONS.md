# Technical Decisions & Trade-offs

## Layer 1: Data Normalization

**Schema Design:**  
I used a flat JSON structure with clear core fields (id, vendor_id, normalized_name, price, brand, etc.) because it is simple to query, export to CSV, and process in Python without deep nesting. I also kept the original vendor payload in a `raw_data` field to avoid losing information.

**Missing Data Handling:**  
For prices, I searched multiple possible fields and defaulted to `0.00` if missing. For brands, I checked common keys and used `"Unknown"` when absent. For images, I validated URLs and marked them as `valid`, `broken`, or `missing`. This ensured no product was dropped due to incomplete data.

**Trade-offs:**  
Using default values keeps the pipeline stable, but it may reduce data quality. In the future, I would separate “missing” from real zero values more clearly and store structured validation metadata.

---

## Layer 2: Vendor API Rate Limiting

**The Problem:**  
Each vendor had different rate limits, and exceeding them caused 429 errors. Processing sequentially would be too slow, but sending requests too fast would cause blocking.

**Solution Approach:**  
I created separate async queues per vendor and applied predictive throttling at 80% of the allowed rate. Each queue ran independently using async/await.

**Why This Approach:**  
It prevents rate limit errors before they happen, keeps vendors isolated from each other, and remains simple to debug. It balances performance and reliability without complex algorithms.

**Results:**  
- **Total processing time:** 118 seconds  
- **429 blocks hit:** 0 unexpected  
- **Requests per second achieved:** ~6–8  

**What I’d Improve:**  
I would add adaptive throttling and exponential backoff for network errors, not just rate limits.

---

## Layer 3: Enrichment & Duplicate Detection

**Enrichment Method:**  
I used a hybrid local approach with sentence embeddings (MiniLM) and spaCy for feature extraction. This avoids API costs and works offline.

**Duplicate Detection Method:**  
I combined embeddings (60%), fuzzy matching (25%), and rule-based checks (15%) into a weighted score. If the score ≥ 0.60, products are marked as duplicates.

**Why I Chose This:**  
A hybrid method gives better accuracy than any single method while staying fast and affordable. It balances accuracy, speed, and simplicity.

**Accuracy Results:**  
- **Duplicate detection rate:** 90.4%  
- **False positives:** <2%  
- **Processing time:** 30 seconds per 1,000 products  

**Limitations:**  
It may miss model-number-only matches, bundles vs single items, or year/version differences.

**Alternatives Considered:**  
I considered fine-tuning BERT and using OpenAI APIs, but both increased cost and complexity for limited gain.

---

## Layer 4: Architecture & Code Organization

**Shared Business Logic:**  
I placed all core logic in a `services/` layer and reused it across CLI, API, and frontend. This avoided code duplication and simplified testing.

**Design Patterns Used:**  
I applied the Service Layer pattern, dependency injection for flexibility, and a simple factory pattern for configurable components.

**Future Improvements:**  
I would move from JSON to PostgreSQL, add Redis caching for embeddings, and introduce a message queue for streaming data.

---

## Overall Reflections

**What I’m Proud Of:**  
Zero rate limit failures, 90%+ duplicate accuracy, clean architecture, and strong test coverage.

**What I’d Do Differently:**  
Start with a database from day one and batch embeddings more efficiently.

**What I Learned:**  
Hybrid methods often outperform single techniques, prevention is better than reaction, and simple architecture scales better than early over-engineering.
