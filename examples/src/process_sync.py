import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from pdf_processor import PDFProcessor, PDFProcessType
from pdf_processor.utils.constants import PACKAGE_BANNER

load_dotenv()
console = Console()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def process_single_pdf(processor: PDFProcessor, pdf_path: Path) -> Dict:
    """Process single PDF file

    Args:
        processor: PDF processor
        pdf_path: PDF file path

    Returns:
        Processing result
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task1 = progress.add_task(
            f"[cyan]{pdf_path.name} - Step 1: Analyzing PDF...[/]", total=None
        )
        task2 = progress.add_task(
            f"[cyan]{pdf_path.name} - Step 2: Extracting Data...[/]", visible=False
        )

        try:
            results = await processor.process_pdf(
                pdf_path=str(pdf_path),
                process_type=PDFProcessType.INVOICE.value,
                num_pages=1,  # Process each file as a single invoice
            )

            progress.update(
                task1,
                description=f"[green]{pdf_path.name} - Step 1: PDF Analysis Complete[/]",
                completed=True,
            )
            progress.update(
                task2,
                description=f"[green]{pdf_path.name} - Step 2: Data Extraction Complete[/]",
                completed=True,
            )

            console.print(f"\n[bold green]{pdf_path.name} - Processing Result:[/]")
            result_json = json.dumps(results, ensure_ascii=False, indent=2)
            console.print(Panel(JSON(result_json), title="Extracted Data", border_style="green"))

            return results

        except Exception as e:
            console.print(f"\n[bold red]{pdf_path.name} - Error Occurred:[/] {str(e)}")
            logger.error(f"Error processing PDF {pdf_path.name}: {e}")
            raise


async def process_pdfs(processor: PDFProcessor, pdf_files: List[Path]) -> List[Dict]:
    """Process multiple PDF files

    Args:
        processor: PDF processor
        pdf_files: List of PDF file paths

    Returns:
        List of processing results
    """
    results = []
    for pdf_path in pdf_files:
        try:
            result = await process_single_pdf(processor, pdf_path)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
        console.print("\n" + "=" * 80 + "\n")
    return results


async def main():
    """Example of synchronous processing"""
    console.print(PACKAGE_BANNER, style="bold blue")

    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required.")

    samples_dir = Path(__file__).parent.parent / "samples" / "text"
    pdf_files = sorted(samples_dir.glob("sample_invoice_*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"PDF files not found: {samples_dir}")

    info_text = [
        "[bold cyan]Starting PDF Processing (Synchronous)[/]",
        f"Files to process: [yellow]{', '.join(f.name for f in pdf_files)}[/]",
        f"Processing type: [blue]{PDFProcessType.INVOICE.value}[/]",
    ]
    console.print(Panel("\n".join(info_text), title="Job Information", border_style="blue"))

    try:
        processor = PDFProcessor(openai_api_key=openai_api_key)
        await process_pdfs(processor, pdf_files)

    except Exception as e:
        console.print(f"\n[bold red]Error Occurred:[/] {str(e)}")
        logger.error(f"Error processing PDFs: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
