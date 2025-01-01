from typing import Any, Dict

import pytesseract
from pdf2image import convert_from_path

from pdf_processor.extractors.base import BaseExtractor


class ScannedPDFExtractor(BaseExtractor):
    """스캔된 PDF에서 OCR을 통해 데이터를 추출하는 클래스"""

    def extract_text(self) -> str:
        # PDF를 이미지로 변환
        images = convert_from_path(self.file_path)
        text = ""

        # 각 페이지에 대해 OCR 수행
        for image in images:
            text += pytesseract.image_to_string(image, lang="kor+eng") + "\n"

        return text.strip()

    def extract_metadata(self) -> Dict[str, Any]:
        # 스캔된 PDF의 경우 메타데이터가 제한적일 수 있음
        try:
            from pypdf import PdfReader

            reader = PdfReader(self.file_path, password=self.password)
            return dict(reader.metadata) if reader.metadata else {}
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
