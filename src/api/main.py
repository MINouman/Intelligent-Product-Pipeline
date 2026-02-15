from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database.connection import get_db
from src.database.repositories.product_repo import ProductRepository
from src.models.product import NormalizedProduct
from src.services.pipeline import ProductPipeline

app = FastAPI(
    title="Rokomari Product API",
    description="AI-powered product processing pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def root():
    return {"message": "Rokomari Product API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/products", response_model=List[NormalizedProduct])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    vendor_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    repo = ProductRepository(db)
    if vendor_id:
        products = await repo.get_by_vendor(vendor_id)
    else:
        products = await repo.get_all(limit=limit, offset=skip)
    return products

@app.get("/products/{product_id}")
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/pipeline/run")
async def run_pipeline(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_pipeline_background)
    return {"message": "Pipeline started", "status": "processing"}

async def _run_pipeline_background():
    pipeline = ProductPipeline()
    await pipeline.run("data/input/messy_products.json")

@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    total = await repo.count()
    return {
        "total_products": total,
    }

@app.get("/duplicates")
async def get_duplicates():
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


