import logging
from abc import ABC, abstractmethod
from typing import Any

from pdf_processor.core.llm import LLM

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """모든 PDF 프로세서의 기본 클래스"""

    def __init__(self):
        """프로세서 초기화"""
        self.llm = LLM.get_instance()

    @abstractmethod
    async def execute(self, pdf_path: str, *args: Any, **kwargs: Any) -> Any:
        pass
