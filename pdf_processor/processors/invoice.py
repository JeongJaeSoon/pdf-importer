import logging
from typing import Dict, Optional, Tuple

from pdf_processor.processors.base import BaseProcessor
from pdf_processor.schemas.extraction_schemas import INVOICE_SCHEMA
from pdf_processor.utils.prompts import get_invoice_processor_prompt

logger = logging.getLogger(__name__)


class Invoice(BaseProcessor):
    """인보이스 데이터 추출을 위한 프로세서"""

    async def execute(self, pdf_path: str, page_range: Tuple[int, int]) -> Optional[Dict]:
        """인보이스 데이터 추출

        Args:
            pdf_path: PDF 파일 경로
            page_range: 처리할 페이지 범위 (시작, 끝) - 0-based index

        Returns:
            추출된 인보이스 데이터 또는 None (실패 시)
        """
        try:
            # 프롬프트 생성
            system_message = get_invoice_processor_prompt()

            # LLM을 사용하여 데이터 추출
            result = await self.llm.extract_data(
                pdf_path=pdf_path,
                page_range=page_range,
                schema=INVOICE_SCHEMA,
                system_message=system_message,
            )

            if not result:
                logger.error("인보이스 데이터 추출 실패")
                return None

            logger.info("인보이스 데이터 추출 성공")
            return result

        except Exception as e:
            logger.error(f"인보이스 처리 중 오류 발생: {e}")
            return None
