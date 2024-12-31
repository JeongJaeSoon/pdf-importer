import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from pdf_processor.processors.llm_processor import LLMProcessor

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """모든 PDF 프로세서의 기본 클래스"""

    def __init__(self, openai_api_key: str):
        """프로세서 초기화

        Args:
            openai_api_key: OpenAI API 키
        """
        self.llm_processor = LLMProcessor.initialize(openai_api_key)

    @abstractmethod
    async def process(self, pdf_path: str, page_range: Tuple[int, int]) -> Dict[str, Any]:
        """PDF 파일의 특정 페이지 범위를 처리

        Args:
            pdf_path: PDF 파일 경로
            page_range: 처리할 페이지 범위 (시작, 끝)

        Returns:
            추출된 데이터를 담은 딕셔너리
        """
        pass
