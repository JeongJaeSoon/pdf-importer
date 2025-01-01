import logging
import uuid
from typing import Any, Dict, Optional

from pdf_processor.core.queue_redis import RedisQueue
from pdf_processor.core.worker import Worker
from pdf_processor.utils.constants import PDFProcessType

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Main class for PDF processing"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        redis_encryption_key: Optional[str] = None,
        model_name: str = "gpt-4",
        max_concurrent: int = 2,
    ):
        """Initialize PDF processor

        Args:
            redis_url: Redis server URL (required for async processing)
            openai_api_key: OpenAI API key (required)
            redis_encryption_key: Redis encryption key (required for async processing)
            model_name: OpenAI model name to use (default: "gpt-4")
            max_concurrent: Maximum number of concurrent executions (default: 2)
        """
        self.pdf_analyzer = None
        self.processor = None
        self.redis_queue = None
        self.openai_api_key = openai_api_key
        self.worker = None

        if not openai_api_key:
            raise ValueError("OpenAI API key is required.")

        # Initialize LLM processor
        from pdf_processor.core.llm import LLM

        LLM.initialize(api_key=openai_api_key, model_name=model_name, max_concurrent=max_concurrent)

        # Initialize Redis for async processing
        if redis_url and redis_encryption_key:
            self.redis_queue = RedisQueue.initialize(redis_url, redis_encryption_key)
            self.worker = Worker(self.redis_queue)

    async def process_pdf(
        self,
        pdf_path: str,
        process_type: PDFProcessType,
        num_pages: int,
        metadata: Optional[Dict] = None,
        async_processing: bool = False,
    ) -> Any:
        """Start PDF processing

        Args:
            pdf_path: Path to PDF file
            process_type: Processing type (PDFProcessType)
            num_pages: Expected number of invoices
            metadata: PDF file metadata (optional)
            async_processing: Whether to process asynchronously (default: False)

        Returns:
            Synchronous processing: processing result
            Asynchronous processing: task ID
        """
        # Asynchronous processing
        if async_processing:
            if not self.redis_queue or not self.worker:
                raise ValueError("Redis configuration is required for asynchronous processing.")

            # Generate task ID
            task_id = f"task_{uuid.uuid4()}"

            # Prepare task data
            task_data = {
                "task_id": task_id,
                "pdf_path": pdf_path,
                "process_type": process_type,
                "num_pages": num_pages,
                "metadata": metadata,
            }

            # Add task to queue
            await self.redis_queue.enqueue(task_data)
            return task_id

        # Synchronous processing
        worker = Worker(None)
        task_data = {
            "task_id": f"task_{uuid.uuid4()}",
            "pdf_path": pdf_path,
            "process_type": process_type,
            "num_pages": num_pages,
            "metadata": metadata,
        }
        await worker.process_task(task_data)
        return task_data["task_id"]

    async def get_task_status(self, task_id: str) -> Optional[str]:
        """Get task status"""
        if not self.redis_queue:
            raise ValueError("Redis configuration is required to get task status.")
        status = await self.redis_queue.get_task_status(task_id)
        return status.value if status else None

    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get task result"""
        if not self.redis_queue:
            raise ValueError("Redis configuration is required to get task result.")
        return await self.redis_queue.get_result(task_id)

    async def start_worker(self) -> None:
        """Start worker"""
        if not self.worker:
            raise ValueError("Redis configuration is required to start worker.")
        await self.worker.start()

    async def stop_worker(self) -> None:
        """Stop worker"""
        if self.worker:
            await self.worker.stop()
