from pathlib import Path
from typing import Any, Dict, Optional, Type

from .core.base import BaseDataProcessor, BasePDFExtractor
from .extractors.scanned_pdf import ScannedPDFExtractor
from .extractors.text_pdf import TextPDFExtractor
from .processors.llm_processor import LLMDataProcessor


class PDFProcessor:
    """PDF 처리를 위한 주요 인터페이스"""

    def __init__(
        self,
        file_path: str | Path,
        extractor_class: Optional[Type[BasePDFExtractor]] = None,
        password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.file_path = Path(file_path)
        self.password = password

        # 적절한 추출기 선택
        if extractor_class is None:
            # TODO: 파일 분석을 통한 자동 추출기 선택 로직 구현
            extractor_class = TextPDFExtractor

        self.extractor = extractor_class(self.file_path, password=password)
        self.processor = LLMDataProcessor(api_key=openai_api_key) if openai_api_key else None

    def extract_and_process(self, output_format: str = "json") -> Dict[str, Any]:
        """PDF에서 텍스트를 추출하고 처리"""
        if not self.processor:
            raise ValueError("LLM 처리를 위해 OpenAI API 키가 필요합니다.")

        # 텍스트 추출
        text = self.extractor.extract_text()
        metadata = self.extractor.extract_metadata()

        # 데이터 처리
        processed_data = self.processor.process(text)

        # 메타데이터 추가
        processed_data["metadata"] = metadata

        # 데이터 검증
        if not self.processor.validate(processed_data):
            raise ValueError("처리된 데이터가 유효하지 않습니다.")

        # 지정된 형식으로 변환
        return self.processor.transform(processed_data, output_format)
