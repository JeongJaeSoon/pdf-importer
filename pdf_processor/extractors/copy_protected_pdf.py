from typing import Any, Dict

import fitz  # PyMuPDF

from pdf_processor.extractors.base import BaseExtractor


class CopyProtectedPDFExtractor(BaseExtractor):
    """복사 방지 기능이 설정된 PDF에서 데이터를 추출하는 클래스"""

    def extract_text(self) -> str:
        try:
            doc = fitz.open(self.file_path)
            text = ""

            for page in doc:
                # 복사 방지 설정을 우회하여 텍스트 추출
                # PyMuPDF는 PDF의 실제 콘텐츠에서 직접 텍스트를 추출하므로
                # 복사 방지 설정을 우회할 수 있음
                text += page.get_text(sort=True) + "\n"

            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from copy-protected PDF: {e}")
            return ""

    def extract_metadata(self) -> Dict[str, Any]:
        try:
            doc = fitz.open(self.file_path)
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "permissions": doc.permissions,
                "copy_protected": True,
            }
            doc.close()
            return metadata
        except Exception as e:
            print(f"Error extracting metadata from copy-protected PDF: {e}")
            return {}
