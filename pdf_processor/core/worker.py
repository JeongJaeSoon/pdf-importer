import asyncio
import logging
from typing import Any, Dict, Type

from pdf_processor.core.llm import LLM
from pdf_processor.core.queue import BaseQueue, TaskStatus
from pdf_processor.processors.base import BaseProcessor
from pdf_processor.processors.invoice import Invoice
from pdf_processor.processors.pdf_analyzer import PDFAnalyzer
from pdf_processor.utils.constants import PDFProcessType

logger = logging.getLogger(__name__)


class Worker:
    """Asynchronous PDF Processing Worker"""

    # Processor mapping by process type
    PROCESSORS = {
        PDFProcessType.INVOICE: Invoice,
        # Add other process types here after implementation
    }

    def __init__(self, queue: BaseQueue):
        self.queue = queue
        self.running = False
        # Initialize LLM
        self.llm = LLM.get_instance()

    def _get_processor_class(self, process_type: str) -> Type[BaseProcessor]:
        """Return processor class for the given process type"""
        try:
            process_type_enum = PDFProcessType(process_type.lower())
            processor_class = self.PROCESSORS.get(process_type_enum)
            if not processor_class:
                available_types = ", ".join(PDFProcessType.values())
                raise ValueError(
                    f"Unsupported process type: {process_type}. "
                    f"Available types: {available_types}"
                )
            return processor_class
        except ValueError:
            available_types = ", ".join(PDFProcessType.values())
            raise ValueError(f"Invalid process type. Available types: {available_types}")

    async def process_task(self, task_data: Dict[str, Any]) -> None:
        """Process task"""
        task_id = task_data.get("task_id")
        if not task_id:
            logger.error("Task ID is missing.")
            return

        try:
            # Update task status to processing
            await self.queue.update_task_status(task_id, TaskStatus.PROCESSING)

            # Check required fields
            required_fields = ["pdf_path", "process_type", "num_pages"]
            for field in required_fields:
                if field not in task_data:
                    raise ValueError(f"Required field is missing: {field}")

            # Analyze and process PDF
            pdf_path = task_data["pdf_path"]
            process_type = task_data["process_type"]
            num_pages = task_data["num_pages"]
            metadata = task_data.get("metadata")  # Get metadata

            # Initialize PDF analyzer
            analyzer = PDFAnalyzer()
            page_ranges_with_reasons = await analyzer.execute(
                pdf_path=pdf_path, num_pages=num_pages, metadata=metadata  # Pass metadata
            )

            # Initialize processor for the process type
            processor_class = self._get_processor_class(process_type)
            processor = processor_class()

            # Process each page range
            results = []
            for start_page, end_page, reason in page_ranges_with_reasons:
                try:
                    # Pass analysis reason and metadata when calling existing execute method
                    result = await processor.execute(
                        pdf_path=pdf_path,
                        page_range=(start_page, end_page),
                        analysis_reason=reason,
                        metadata=metadata,  # Pass metadata
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing page range {(start_page+1, end_page+1)}: {e}")
                    # Record individual page range failure and continue
                    results.append(
                        {
                            "error": f"Processing failed: {str(e)}",
                            "page_range": (start_page + 1, end_page + 1),
                        }
                    )

            # Save results
            await self.queue.store_result(task_id, results)

            # If at least one result exists, mark as success
            if any(not isinstance(r, dict) or "error" not in r for r in results):
                await self.queue.update_task_status(task_id, TaskStatus.COMPLETED)
            else:
                # If all page ranges failed
                await self.queue.update_task_status(task_id, TaskStatus.FAILED)
                error_message = "All page ranges failed"
                await self.queue.store_result(task_id, {"error": error_message})

        except Exception as e:
            logger.error(f"Error processing task: {e}")
            await self.queue.update_task_status(task_id, TaskStatus.FAILED)
            await self.queue.store_result(task_id, {"error": str(e)})

    async def start(self, poll_interval: float = 1.0):
        """Start worker"""
        self.running = True
        logger.info("Starting PDF processing worker")

        while self.running:
            try:
                # Get next task from queue
                task_data = await self.queue.dequeue()
                if task_data:
                    logger.info(f"New task received: {task_data.get('task_id')}")
                    # Process task
                    await self.process_task(task_data)
                else:
                    # If no task, wait
                    await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(poll_interval)

    async def stop(self):
        """Stop worker"""
        logger.info("Stopping PDF processing worker")
        self.running = False
