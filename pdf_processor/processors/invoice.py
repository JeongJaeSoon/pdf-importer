import logging
from typing import Dict, Optional, Tuple

from pdf_processor.processors.base import BaseProcessor
from pdf_processor.schemas.extraction_schemas import INVOICE_SCHEMA
from pdf_processor.utils.prompts import get_invoice_processor_prompt

logger = logging.getLogger(__name__)


class Invoice(BaseProcessor):
    """Processor for invoice data extraction"""

    async def execute(
        self,
        pdf_path: str,
        page_range: Tuple[int, int],
        analysis_reason: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Extract invoice data

        Args:
            pdf_path: Path to PDF file
            page_range: Page range to process (start, end) - 0-based index
            analysis_reason: Reason for page range determination provided by PDF analyzer (optional)
            metadata: PDF file related metadata (optional)

        Returns:
            Extracted invoice data or None (if failed)
        """
        try:
            # Generate prompt (including analysis reason and metadata)
            system_message = get_invoice_processor_prompt(
                analysis_reason=analysis_reason, metadata=metadata
            )

            # Extract data using LLM
            result = await self.llm.extract_data(
                pdf_path=pdf_path,
                page_range=page_range,
                schema=INVOICE_SCHEMA,
                system_message=system_message,
            )

            if not result:
                logger.error("Failed to extract invoice data")
                return None

            logger.info("Successfully extracted invoice data")
            return result

        except Exception as e:
            logger.error(f"Error occurred during invoice processing: {e}")
            return None
