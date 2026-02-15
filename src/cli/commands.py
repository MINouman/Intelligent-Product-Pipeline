import typer
import asyncio
import json
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from pathlib import Path
from typing import Optional

from src.services.normalizer import ProductNormalizer
from src.services.enricher import ProductEnricher
from src.services.duplicate_detector import DuplicateDetector
from src.config.logging_config import setup_logging
from loguru import logger

app = typer.Typer(help="Rokomari Product Processing Pipeline CLI")
console = Console()
setup_logging()


@app.command()
def pipeline(
    input_file: str = typer.Option(
        "data/input/messy_products.json",
        "--input", "-i",
        help="Input JSON file"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    console.print(Panel.fit("Rokomari Product Pipeline", style="bold blue"))
    
    try:
        console.print("\n[bold cyan]Step 1: Normalizing products...[/bold cyan]")
        normalize_result = _run_normalize(input_file, "data/output/normalized_products.json")
        
        if not normalize_result["success"]:
            console.print(f"[bold red]Normalization failed: {normalize_result['error']}[/bold red]")
            return
        
        console.print("\n[bold cyan]Step 2: Enriching with AI features...[/bold cyan]")
        enrich_result = _run_enrich("data/output/normalized_products.json", "data/output/enriched_products.json")
        
        if not enrich_result["success"]:
            console.print(f"[bold red]Enrichment failed: {enrich_result['error']}[/bold red]")
            return

        console.print("\n[bold cyan]Step 3: Detecting duplicates...[/bold cyan]")
        dup_result = _run_duplicates("data/output/enriched_products.json", "data/output/duplicates.json", 0.60)
        
        if not dup_result["success"]:
            console.print(f"[bold red]Duplicate detection failed: {dup_result['error']}[/bold red]")
            return
        
        console.print("\n[bold cyan]Step 4: Validating product quality...[/bold cyan]")
        validate_result = _run_validate("data/output/enriched_products.json", "data/output/validated_products.json")
        
        if not validate_result["success"]:
            console.print(f"[bold red]Validation failed: {validate_result['error']}[/bold red]")
            return
        
        console.print("\n[bold green]Pipeline completed successfully![/bold green]")
        _display_pipeline_summary(normalize_result, enrich_result, dup_result, validate_result)
        
    except Exception as e:
        console.print(f"[bold red]Pipeline failed: {e}[/bold red]")
        logger.exception("Pipeline error")


@app.command()
def normalize(
    input_file: str = typer.Option(
        "data/input/messy_products.json",
        "--input", "-i",
        help="Input JSON file with messy products"
    ),
    output_file: str = typer.Option(
        "data/output/normalized_products.json",
        "--output", "-o",
        help="Output file for normalized products"
    )
):
    console.print(Panel.fit("Product Normalization", style="bold cyan"))
    
    result = _run_normalize(input_file, output_file)
    
    if result["success"]:
        console.print(f"\n[bold green]Normalization complete![/bold green]")
        console.print(f"   Processed: {result['stats']['total']} products")
        console.print(f"   Success: {result['stats']['success']} ({result['stats']['success_rate']:.1f}%)")
        console.print(f"   Failed: {result['stats']['failed']}")
        console.print(f"   Output: {output_file}")
    else:
        console.print(f"[bold red]Normalization failed: {result['error']}[/bold red]")


@app.command()
def enrich(
    input_file: str = typer.Option(
        "data/output/normalized_products.json",
        "--input", "-i",
        help="Input file with normalized products"
    ),
    output_file: str = typer.Option(
        "data/output/enriched_products.json",
        "--output", "-o",
        help="Output file for enriched products"
    )
):
    """Enrich products with AI-generated features"""
    console.print(Panel.fit("AI Product Enrichment", style="bold cyan"))
    
    result = _run_enrich(input_file, output_file)
    
    if result["success"]:
        console.print(f"\n[bold green]Enrichment complete![/bold green]")
        console.print(f"   Processed: {result['stats']['total']} products")
        console.print(f"   Success: {result['stats']['success']}")
        console.print(f"   Failed: {result['stats']['failed']}")
        console.print(f"   Output: {output_file}")
    else:
        console.print(f"[bold red]Enrichment failed: {result['error']}[/bold red]")


@app.command()
def duplicates(
    input_file: str = typer.Option(
        "data/output/enriched_products.json",
        "--input", "-i",
        help="Input file with enriched products"
    ),
    output_file: str = typer.Option(
        "data/output/duplicates.json",
        "--output", "-o",
        help="Output file for duplicate groups"
    ),
    threshold: float = typer.Option(
        0.60,
        "--threshold", "-t",
        help="Similarity threshold (0.0-1.0)"
    )
):
    console.print(Panel.fit("🔍 Duplicate Detection", style="bold cyan"))
    
    result = _run_duplicates(input_file, output_file, threshold)
    
    if result["success"]:
        console.print(f"\n[bold green]Duplicate detection complete![/bold green]")
        console.print(f"   Products analyzed: {result['stats']['total_products']}")
        console.print(f"   Duplicate groups: {result['stats']['duplicate_groups']}")
        console.print(f"   Duplicate rate: {result['stats']['duplicate_rate_percent']:.1f}%")
        console.print(f"   Threshold: {threshold}")
        console.print(f"   Output: {output_file}")
    else:
        console.print(f"[bold red]Duplicate detection failed: {result['error']}[/bold red]")


@app.command()
def validate(
    input_file: str = typer.Option(
        "data/output/normalized_products.json",
        "--input", "-i"
    ),
    output_file: str = typer.Option(
        "data/output/validated_products.json",
        "--output", "-o"
    ),
    flag_threshold: int = typer.Option(
        50,
        "--threshold", "-t",
        help="Quality score threshold for flagging"
    )
):
    console.print(Panel.fit("✅ Product Validation", style="bold cyan"))
    
    with open(input_file) as f:
        products = json.load(f)
    
    console.print(f"   Loaded {len(products)} products")
    
    from src.services.product_validator import ProductValidator
    validator = ProductValidator()
    validated = validator.validate_batch(products)
    
    with open(output_file, 'w') as f:
        json.dump(validated, f, indent=2, default=str)
    
    stats = validator.get_stats()
    
    table = Table(title="Validation Results")
    table.add_column("Quality Level", style="cyan")
    table.add_column("Count", style="yellow")
    table.add_column("Percentage", style="green")
    
    table.add_row("Excellent", str(stats['excellent']), f"{stats['excellent_pct']}%")
    table.add_row("Good", str(stats['good']), f"{stats['good_pct']}%")
    table.add_row("Fair", str(stats['fair']), f"{stats['fair_pct']}%")
    table.add_row("Poor (Flagged)", str(stats['poor']), f"{stats['poor_pct']}%")
    
    console.print(table)
    console.print(f"\nValidated products saved to {output_file}")


@app.command()
def status():
    console.print(Panel.fit("Pipeline Status", style="bold cyan"))
    
    files = {
        "Input": "data/input/messy_products.json",
        "Normalized": "data/output/normalized_products.json",
        "Enriched": "data/output/enriched_products.json",
        "Duplicates": "data/output/duplicates.json",
        "Validated": "data/output/validated_products.json" 
    }
    
    table = Table(title="Pipeline Files", show_header=True)
    table.add_column("Stage", style="cyan")
    table.add_column("File", style="white")
    table.add_column("Status", style="green")
    table.add_column("Size", style="yellow")
    
    for stage, filepath in files.items():
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            size_str = _format_size(size)
            
            try:
                with open(path) as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else "N/A"
            except:
                count = "N/A"
            
            table.add_row(
                stage,
                filepath,
                f"Exists ({count} items)",
                size_str
            )
        else:
            table.add_row(stage, filepath, "Missing", "-")
    
    console.print(table)


@app.command()
def export(
    format: str = typer.Option(
        "json",
        "--format", "-f",
        help="Export format (json/csv)"
    ),
    input_file: str = typer.Option(
        "data/output/enriched_products.json",
        "--input", "-i",
        help="Input file to export"
    ),
    output_file: str = typer.Option(
        None,
        "--output", "-o",
        help="Output file"
    )
):
    console.print(Panel.fit(f"Exporting to {format.upper()}", style="bold cyan"))
    
    if output_file is None:
        output_file = f"data/output/export.{format}"
    
    try:
        with open(input_file) as f:
            products = json.load(f)
        
        if format == "json":
            with open(output_file, 'w') as f:
                json.dump(products, f, indent=2, default=str)
        
        elif format == "csv":
            import csv
            
            if not products:
                console.print("[yellow]No products to export[/yellow]")
                return
            
            keys = list(products[0].keys())
            keys = [k for k in keys if k not in ['raw_data', 'name_embedding', 'extracted_features', 'tags']]
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for product in products:
                    row = {k: product.get(k) for k in keys}
                    writer.writerow(row)
        
        else:
            console.print(f"[red]Unsupported format: {format}[/red]")
            return
        
        console.print(f"[green]Exported {len(products)} products to {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        logger.exception("Export error")



def _run_normalize(input_file: str, output_file: str) -> dict:
    try:
        with open(input_file) as f:
            messy_products = json.load(f)
        
        console.print(f"   Loaded {len(messy_products)} products from {input_file}")
        
        normalizer = ProductNormalizer()
        
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Normalizing...", total=len(messy_products))
            
            normalized = []
            failed = []
            
            for messy in messy_products:
                result, errors = normalizer.normalize(messy)
                if result:
                    normalized.append(result.dict())
                else:
                    failed.append({"product": messy, "errors": errors})
                
                progress.advance(task)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(normalized, f, indent=2, default=str)
        
        stats = normalizer.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "output_file": output_file
        }
        
    except Exception as e:
        logger.exception("Normalization error")
        return {
            "success": False,
            "error": str(e)
        }


def _run_enrich(input_file: str, output_file: str) -> dict:
    try:
        with open(input_file) as f:
            products = json.load(f)
        
        console.print(f"   Loaded {len(products)} products from {input_file}")
        
        enricher = ProductEnricher()
        
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Enriching...", total=len(products))
            
            enriched = []
            
            for product in products:
                enrichment = enricher.enrich(product)
                product.update(enrichment)
                enriched.append(product)
                progress.advance(task)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(enriched, f, indent=2, default=str)
        
        return {
            "success": True,
            "stats": enricher.stats,
            "output_file": output_file
        }
        
    except Exception as e:
        logger.exception("Enrichment error")
        return {
            "success": False,
            "error": str(e)
        }


def _run_duplicates(input_file: str, output_file: str, threshold: float) -> dict:
    try:
        with open(input_file) as f:
            products = json.load(f)
        
        console.print(f"   Loaded {len(products)} products from {input_file}")
        
        detector = DuplicateDetector(similarity_threshold=threshold)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("Detecting duplicates..."),
            console=console
        ) as progress:
            task = progress.add_task("Processing...", total=None)
            duplicates = detector.detect_duplicates(products)
            progress.update(task, completed=True)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(duplicates, f, indent=2, default=str)
        
        stats = detector.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "output_file": output_file
        }
        
    except Exception as e:
        logger.exception("Duplicate detection error")
        return {
            "success": False,
            "error": str(e)
        }


def _run_validate(input_file: str, output_file: str) -> dict:
    try:
        from src.services.product_validator import ProductValidator
        
        with open(input_file) as f:
            products = json.load(f)
        
        console.print(f"   Loaded {len(products)} products from {input_file}")
        
        validator = ProductValidator()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("Validating quality..."),
            console=console
        ) as progress:
            task = progress.add_task("Processing...", total=None)
            validated = validator.validate_batch(products)
            progress.update(task, completed=True)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(validated, f, indent=2, default=str)
        
        stats = validator.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "output_file": output_file
        }
        
    except Exception as e:
        logger.exception("Validation error")
        return {
            "success": False,
            "error": str(e)
        }


def _display_pipeline_summary(normalize_result, enrich_result, dup_result, validate_result):
    """Display comprehensive pipeline summary"""
    table = Table(title="Pipeline Summary", show_header=True)
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Processed", style="yellow")
    table.add_column("Success Rate", style="magenta")
    
    table.add_row(
        "1. Normalization",
        "Complete",
        str(normalize_result['stats']['total']),
        f"{normalize_result['stats']['success_rate']:.1f}%"
    )
    
    table.add_row(
        "2. Enrichment",
        "Complete",
        str(enrich_result['stats']['total']),
        f"{(enrich_result['stats']['success'] / enrich_result['stats']['total'] * 100):.1f}%"
    )
    
    table.add_row(
        "3. Duplicate Detection",
        "Complete",
        str(dup_result['stats']['total_products']),
        f"Found {dup_result['stats']['duplicate_groups']} groups"
    )
    
    table.add_row(
        "4. Validation",
        "Complete",
        str(validate_result['stats']['total']),
        f"{validate_result['stats']['excellent_pct']:.1f}% excellent"
    )
    
    console.print(table)


def _format_size(size: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


if __name__ == "__main__":
    app()


# --------------
# for testing
"""
    python -m src.cli.commands pipeline
    python -m src.cli.commands normalize
    python -m src.cli.commands enrich
    python -m src.cli.commands duplicates
"""

