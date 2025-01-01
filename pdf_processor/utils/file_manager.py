import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

logger = logging.getLogger(__name__)


class TempFileManager:
    """Class for temporary file management"""

    def __init__(self):
        self._temp_files: List[Path] = []

    def create_temp_file(self, suffix: str = ".pdf", prefix: Optional[str] = None) -> Path:
        """Create temporary file

        Args:
            suffix: File extension (default: .pdf)
            prefix: File name prefix (optional)

        Returns:
            Path to the created temporary file
        """
        temp_file = Path(tempfile.mktemp(suffix=suffix, prefix=prefix))
        self._temp_files.append(temp_file)
        logger.debug(f"Created temporary file: {temp_file}")
        return temp_file

    def cleanup(self) -> None:
        """Delete all temporary files"""
        for temp_file in self._temp_files:
            try:
                if temp_file.exists():
                    os.remove(temp_file)
                    logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.error(f"Error removing temporary file {temp_file}: {e}")

        self._temp_files.clear()

    def __enter__(self) -> "TempFileManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


@contextmanager
def temp_files_scope(prefix: Optional[str] = None) -> Generator[TempFileManager, None, None]:
    """Context manager for temporary file management

    Example:
        # Use temporary file
        # cleanup is automatically called when exiting context
    """
    manager = TempFileManager()
    try:
        yield manager
    finally:
        manager.cleanup()


class PDFSplitManager:
    """Class for PDF file splitting and temporary file management"""

    def __init__(self, original_pdf: Path):
        self.original_pdf = original_pdf
        self.temp_manager = TempFileManager()

    async def split_pdf(self, page_ranges: List[dict]) -> List[Path]:
        """PDF file split by page range

        Args:
            page_ranges: List of page ranges. Each item is {"start_page": int, "end_page": int} format

        Returns:
            List of paths to split PDF files
        """
        from PyPDF2 import PdfReader, PdfWriter

        logger.info(f"Splitting PDF {self.original_pdf} into {len(page_ranges)} parts")
        reader = PdfReader(str(self.original_pdf))
        split_files = []

        for i, page_range in enumerate(page_ranges, 1):
            writer = PdfWriter()
            start_page = page_range["start_page"] - 1  # 0-based index
            end_page = page_range["end_page"]

            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            # Create temporary file
            temp_file = self.temp_manager.create_temp_file(prefix=f"split_{i}_", suffix=".pdf")

            with open(temp_file, "wb") as output_file:
                writer.write(output_file)

            split_files.append(temp_file)
            logger.info(f"Created split file {temp_file} for pages {start_page+1}-{end_page}")

        return split_files

    def cleanup(self):
        """Clean up temporary files"""
        self.temp_manager.cleanup()

    def __enter__(self) -> "PDFSplitManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
