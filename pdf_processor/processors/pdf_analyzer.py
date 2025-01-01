import logging
from typing import Dict, List, Optional, Tuple

import fitz

from pdf_processor.processors.base import BaseProcessor
from pdf_processor.schemas.extraction_schemas import PDF_ANALYZER_SCHEMA
from pdf_processor.utils.prompts import get_pdf_analysis_prompt

logger = logging.getLogger(__name__)


class PDFAnalyzer(BaseProcessor):
    """Class for PDF file analysis and splitting"""

    async def execute(
        self, pdf_path: str, num_pages: int, metadata: Optional[Dict] = None
    ) -> List[Tuple[int, int, Optional[str]]]:
        """Analyze PDF file to determine page ranges

        Args:
            pdf_path: Path to PDF file
            num_pages: Expected number of invoice documents
            metadata: PDF file related metadata (optional)

        Returns:
            List of page ranges and analysis reasons [(start, end, reason), ...] (0-based index)
            For default splitting, reason is None
        """
        try:
            # Open PDF file
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)

            if total_pages == 0:
                raise ValueError("PDF file is empty.")

            if num_pages <= 0:
                raise ValueError("Number of documents must be greater than 0.")

            # Extract all text
            text = ""
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                text += f"\n=== Page {page_num + 1} ===\n"  # 1-based page number
                text += page.get_text()

            # Generate prompt (including metadata)
            system_message = get_pdf_analysis_prompt(
                total_pages=total_pages, num_pages=num_pages, metadata=metadata
            )

            # Extract data using LLM
            result = await self.llm.extract_data(
                pdf_path=pdf_path,
                page_range=(0, total_pages - 1),
                schema=PDF_ANALYZER_SCHEMA,
                system_message=system_message,
            )

            page_ranges = []
            if not result or "page_ranges" not in result or not result["page_ranges"]:
                logger.warning("No LLM analysis result, using default splitting method.")
                pages_per_doc = max(1, total_pages // num_pages)
                for i in range(num_pages):
                    start_page = i * pages_per_doc
                    if start_page >= total_pages:
                        break
                    end_page = min((i + 1) * pages_per_doc - 1, total_pages - 1)
                    page_ranges.append(
                        (start_page, end_page, None)
                    )  # No reason for default splitting
                    logger.info(f"Default split - Invoice {i+1}: Pages {start_page+1}-{end_page+1}")
            else:
                # Use LLM analysis result (convert 1-based to 0-based)
                for range_info in result["page_ranges"]:
                    # Convert 1-based to 0-based and validate range
                    start_page = max(0, min(total_pages - 1, range_info["start_page"] - 1))
                    end_page = max(0, min(total_pages - 1, range_info["end_page"] - 1))
                    reason = range_info.get("reason", "No information")

                    if start_page <= end_page:
                        page_ranges.append((start_page, end_page, reason))
                        logger.info(
                            f"Invoice page range: {start_page+1}-{end_page+1}\n" f"Reason: {reason}"
                        )

                # Validate results
                if len(page_ranges) != num_pages:
                    logger.warning(
                        "Number of invoices returned by LLM differs from expected. "
                        f"(Returned: {len(page_ranges)}, Expected: {num_pages}) "
                        "Using default splitting method."
                    )
                    page_ranges = []
                    pages_per_doc = max(1, total_pages // num_pages)
                    for i in range(num_pages):
                        start_page = i * pages_per_doc
                        if start_page >= total_pages:
                            break
                        end_page = min((i + 1) * pages_per_doc - 1, total_pages - 1)
                        page_ranges.append(
                            (start_page, end_page, None)
                        )  # No reason for default splitting
                        logger.info(
                            f"Default split - Invoice {i+1}: Pages {start_page+1}-{end_page+1}"
                        )

            logger.info(
                f"PDF analysis complete - Page ranges: {[(s+1, e+1) for s, e, _ in page_ranges]}"
            )
            return page_ranges

        except Exception as e:
            logger.error(f"Error during PDF analysis: {e}")
            raise

        finally:
            if "pdf_document" in locals():
                pdf_document.close()
