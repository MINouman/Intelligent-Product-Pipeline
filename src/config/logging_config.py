from loguru import logger
import sys 
from pathlib import Path

def setup_logging():
    logger.remove()

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level = "INFO",
        colorize = True
    )

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # logger.add(
    #     log_dir / "pipeline.log",
    #     rotation="10 MB",
    #     retention="7 days",
    #     compression="zip",
    #     format="{time:YYYY-MM-DD HH:mm:ss} | {<level: <8} | {name}:{function} - {message}",
    #     level = "DEBUG"
    # )
    logger.add(
        "logs/pipeline.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level="DEBUG"
    )
    logger.add(
        log_dir / "normalization.log",
        rotation= "5 MB",
        filter=lambda record: "normalizer" in record["name"],
        level="DEBUG"
    )

    logger.add(
        log_dir / "vendor_requests.log",
        rotation = "5 MB",
        filter = lambda record: "vendor_client" in record["name"],
        level = "DEBUG",
        format= "{time:YYYY-MM-DD HH:mm:ss} | {extra[vendor_id]} | {extra[product_id]} | {extra[status]} | {message}"
    )

    logger.add(
        log_dir / "enrichment.log",
        rotation=  "5 MB",
        filter = lambda record: "enrichment" in record["name"] or "duplicate_detecter" in record["name"],
        level="DEBUG"
    )

    return logger