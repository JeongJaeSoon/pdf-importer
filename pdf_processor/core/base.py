from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BasePDFExtractor(ABC):
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


class BaseDataProcessor(ABC):
    """추출된 데이터 처리를 위한 기본 추상 클래스"""

    @abstractmethod
    def process(self, data: str) -> Dict[str, Any]:
        """추출된 데이터를 처리하는 메서드"""
        pass

    @abstractmethod
    def validate(self, processed_data: Dict[str, Any]) -> bool:
        """처리된 데이터의 유효성을 검증하는 메서드"""
        pass

    @abstractmethod
    def transform(self, processed_data: Dict[str, Any], output_format: str) -> Any:
        """처리된 데이터를 지정된 형식으로 변환하는 메서드"""
        pass
