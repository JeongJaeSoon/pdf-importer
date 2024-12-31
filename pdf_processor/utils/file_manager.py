import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

logger = logging.getLogger(__name__)


class TempFileManager:
    """임시 파일 관리를 위한 클래스"""

    def __init__(self):
        self._temp_files: List[Path] = []

    def create_temp_file(self, suffix: str = ".pdf", prefix: Optional[str] = None) -> Path:
        """임시 파일 생성

        Args:
            suffix: 파일 확장자 (기본값: .pdf)
            prefix: 파일 이름 접두사 (선택사항)

        Returns:
            생성된 임시 파일의 경로
        """
        temp_file = Path(tempfile.mktemp(suffix=suffix, prefix=prefix))
        self._temp_files.append(temp_file)
        logger.debug(f"Created temporary file: {temp_file}")
        return temp_file

    def cleanup(self) -> None:
        """모든 임시 파일 삭제"""
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
    """임시 파일 관리를 위한 컨텍스트 매니저

    Example:
        ```python
        with temp_files_scope("invoice_") as file_manager:
            temp_file = file_manager.create_temp_file()
            # 임시 파일 사용
            # 컨텍스트를 벗어나면 자동으로 cleanup 호출
        ```
    """
    manager = TempFileManager()
    try:
        yield manager
    finally:
        manager.cleanup()


class PDFSplitManager:
    """PDF 파일 분할 및 임시 파일 관리를 위한 클래스"""

    def __init__(self, original_pdf: Path):
        self.original_pdf = original_pdf
        self.temp_manager = TempFileManager()

    async def split_pdf(self, page_ranges: List[dict]) -> List[Path]:
        """PDF 파일을 페이지 범위에 따라 분할

        Args:
            page_ranges: 페이지 범위 리스트. 각 항목은 {"start_page": int, "end_page": int} 형식

        Returns:
            분할된 PDF 파일 경로 리스트
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

            # 임시 파일 생성
            temp_file = self.temp_manager.create_temp_file(prefix=f"split_{i}_", suffix=".pdf")

            with open(temp_file, "wb") as output_file:
                writer.write(output_file)

            split_files.append(temp_file)
            logger.info(f"Created split file {temp_file} for pages {start_page+1}-{end_page}")

        return split_files

    def cleanup(self):
        """임시 파일 정리"""
        self.temp_manager.cleanup()

    def __enter__(self) -> "PDFSplitManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
