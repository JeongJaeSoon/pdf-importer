from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseExtractor(ABC):
    """PDF 데이터 추출을 위한 기본 추상 클래스"""

    def __init__(self, file_path: str | Path, password: Optional[str] = None):
        self.file_path = Path(file_path)
        self.password = password

    @abstractmethod
    def extract_text(self) -> str:
        """PDF에서 텍스트를 추출하는 메서드"""
        pass

    @abstractmethod
    def extract_metadata(self) -> Dict[str, Any]:
        """PDF의 메타데이터를 추출하는 메서드"""
        pass
