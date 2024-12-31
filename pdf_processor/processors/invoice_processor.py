import logging
from typing import Any, Dict, Tuple

from pdf_processor.processors.base import BaseProcessor
from pdf_processor.schemas.extraction_schemas import INVOICE_SCHEMA

logger = logging.getLogger(__name__)


class InvoiceProcessor(BaseProcessor):
    """인보이스 처리를 위한 프로세서"""

    async def process(self, pdf_path: str, page_range: Tuple[int, int]) -> Dict[str, Any]:
        """인보이스 PDF의 특정 페이지 범위를 처리

        Args:
            pdf_path: PDF 파일 경로
            page_range: 처리할 페이지 범위 (시작, 끝)

        Returns:
            추출된 인보이스 데이터를 담은 딕셔너리
        """
        try:
            logger.info(f"인보이스 처리 시작 - 페이지 범위: {page_range}")

            # LLM을 사용하여 데이터 추출
            result = await self.llm_processor.extract_data(
                pdf_path=pdf_path,
                page_range=page_range,
                schema=INVOICE_SCHEMA,
            )

            logger.info(f"인보이스 처리 완료 - 페이지 범위: {page_range}")
            return result

        except Exception as e:
            logger.error(f"인보이스 처리 중 오류 발생 - 페이지 범위 {page_range}: {e}")
            raise
