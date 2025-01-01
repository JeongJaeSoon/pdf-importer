from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseExtractor(ABC):
    """Base abstract class for PDF data extraction"""

    def __init__(self, file_path: str | Path, password: Optional[str] = None):
        self.file_path = Path(file_path)
        self.password = password

    @abstractmethod
    def extract_text(self) -> str:
        """Method to extract text from PDF"""
        pass

    @abstractmethod
    def extract_metadata(self) -> Dict[str, Any]:
        """Method to extract metadata from PDF"""
        pass
