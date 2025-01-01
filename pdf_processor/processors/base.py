import logging
from abc import ABC, abstractmethod
from typing import Any

from pdf_processor.core.llm import LLM

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Base class for all PDF processors"""

    def __init__(self):
        """Initialize processor"""
        self.llm = LLM.get_instance()

    @abstractmethod
    async def execute(self, pdf_path: str, *args: Any, **kwargs: Any) -> Any:
        pass
