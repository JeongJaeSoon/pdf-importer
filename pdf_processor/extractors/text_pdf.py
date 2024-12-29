from typing import Any, Dict

from pypdf import PdfReader

from ..core.base import BasePDFExtractor


class TextPDFExtractor(BasePDFExtractor):
    """일반 텍스트 PDF에서 데이터를 추출하는 클래스"""

    def extract_text(self) -> str:
        reader = PdfReader(self.file_path, password=self.password)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

    def extract_metadata(self) -> Dict[str, Any]:
        reader = PdfReader(self.file_path, password=self.password)
        return dict(reader.metadata) if reader.metadata else {}
