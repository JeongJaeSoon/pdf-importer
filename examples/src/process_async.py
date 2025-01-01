import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from pdf_processor import PDFProcessor, PDFProcessType
from pdf_processor.utils.constants import PACKAGE_BANNER

load_dotenv()
console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        RichHandler(
            console=console, show_time=True, show_path=False, markup=True, rich_tracebacks=True
        )
    ],
)

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def process_single_pdf(
    processor: PDFProcessor, pdf_path: Path, task_id: str
) -> Optional[Dict]:
    """Process single PDF file

    Args:
        processor: PDF processor
        pdf_path: PDF file path
        task_id: Task ID

    Returns:
        Processing result or None (if failed)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}", justify="left"),
        console=console,
        transient=False,
        expand=False,
    ) as progress:
        task = progress.add_task(f"[cyan]{pdf_path.name} - Processing...[/]", total=None)
        status = None
        prev_status = None

        while True:
            status = await processor.get_task_status(task_id)

            if status != prev_status:
                if prev_status:
                    progress.print()
                    console.print()

                progress.update(
                    task,
                    description=f"[bold blue]{pdf_path.name} - Current Status:[/] [yellow]{status}[/]",
                )
                prev_status = status

            if status == "completed":
                progress.print()
                console.print()
                result = await processor.get_task_result(task_id)
                console.print(f"[bold green]{pdf_path.name} - Processing Result:[/]")
                result_json = json.dumps(result, ensure_ascii=False, indent=2)
                console.print(
                    Panel(JSON(result_json), title="Extracted Data", border_style="green")
                )
                return result

            elif status == "failed":
                progress.print()
                console.print()
                error_info = await processor.get_task_result(task_id)
                console.print(f"[bold red]{pdf_path.name} - Processing failed[/]")
                if error_info:
                    console.print(
                        f"[red]Error message:[/] {error_info.get('error', 'Unknown error')}"
                    )
                return None

            await asyncio.sleep(1)


async def process_pdfs(processor: PDFProcessor, pdf_files: List[Path]) -> List[Dict]:
    """Process multiple PDF files

    Args:
        processor: PDF processor
        pdf_files: List of PDF file paths

    Returns:
        List of processing results
    """
    # PDF file information mapping (num_pages is required, metadata is optional)
    pdf_info = {
        "sample_invoice_1.pdf": {
            "num_pages": 1,
            "metadata": {
                "customer_names": ["鶯交通"],
            },
        },
        "sample_invoice_2.pdf": {
            "num_pages": 2,
            "metadata": {
                "customer_names": [
                    "ふつう株式会社",
                    "とてもとてもとてもとてもとてもとてもとてもとてもとても とてもとてもとてもとてもとてもとてもとても株式会社長い長い長い長い長い長い長い長い長い長い長い長 い長い長い長い長い長い長い長い長い長い長い長い 長い長い長い長い長い支社",
                ],
            },
        },
        "sample_invoice_3.pdf": {
            "num_pages": 3,
            "metadata": {
                "customer_names": [
                    "AAA",
                    "[demo]有限会社freee建設",
                    "[demo]株式会社freee企画",
                ],
            },
        },
        "sample_invoice_4.pdf": {
            "num_pages": 4,
            "metadata": {
                "customer_names": [
                    "AAA",
                    "[demo]有限会社freee建設",
                    "[demo]株式会社freee企画",
                    "[demo]株式会社freee開発",
                ],
            },
        },
    }

    # Submit tasks
    tasks = []
    for pdf_path in pdf_files:
        file_info = pdf_info.get(pdf_path.name, {"num_pages": 1})
        num_invoices = file_info["num_pages"]
        metadata = file_info.get("metadata", {})

        task_id = await processor.process_pdf(
            pdf_path=str(pdf_path),
            process_type=PDFProcessType.INVOICE.value,
            num_pages=num_invoices,
            metadata=metadata,
            async_processing=True,
        )
        tasks.append((task_id, pdf_path))
        console.print(
            f"\n[bold green]Task submitted successfully.[/] File: [yellow]{pdf_path.name}[/], "
            f"Task ID: [yellow]{task_id}[/], Estimated number of invoices: [yellow]{num_invoices}[/]"
        )

    # Wait for all tasks to complete
    results = []
    for task_id, pdf_path in tasks:
        result = await process_single_pdf(processor, pdf_path, task_id)
        if result:
            results.append(result)
        console.print("\n" + "=" * 80 + "\n")

    return results


async def main():
    """Asynchronous processing example"""
    console.print(PACKAGE_BANNER, style="bold blue")

    redis_url = os.getenv("REDIS_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    redis_encryption_key = os.getenv("REDIS_ENCRYPTION_KEY")
    max_concurrent = int(os.getenv("MAX_CONCURRENT", "2"))
    model_name = os.getenv("MODEL_NAME", "gpt-4")

    if not redis_url or not openai_api_key or not redis_encryption_key:
        raise ValueError(
            "REDIS_URL, OPENAI_API_KEY, REDIS_ENCRYPTION_KEY environment variables are required."
        )

    samples_dir = Path(__file__).parent.parent / "samples" / "text"
    pdf_files = sorted(samples_dir.glob("sample_invoice_*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"PDF files not found: {samples_dir}")

    info_text = [
        "[bold cyan]PDF Processing Started (Asynchronous Processing)[/]",
        f"Files to process: [yellow]{', '.join(f.name for f in pdf_files)}[/]",
        f"Processing type: [blue]{PDFProcessType.INVOICE.value}[/]",
        f"Maximum number of concurrent executions: [blue]{max_concurrent}[/]",
        f"Using model: [blue]{model_name}[/]",
    ]
    console.print(Panel("\n".join(info_text), title="Task Information", border_style="blue"))

    processor = PDFProcessor(
        redis_url=redis_url,
        openai_api_key=openai_api_key,
        redis_encryption_key=redis_encryption_key,
        model_name=model_name,
        max_concurrent=max_concurrent,
    )

    worker_task = None
    try:
        worker_task = asyncio.create_task(processor.start_worker())
        await process_pdfs(processor, pdf_files)

    except Exception as e:
        console.print(f"\n[bold red]Error occurred:[/] {str(e)}")
        logger.error(f"Error processing PDFs: {e}")
        raise

    finally:
        if worker_task:
            await processor.stop_worker()
            await worker_task


if __name__ == "__main__":
    asyncio.run(main())
