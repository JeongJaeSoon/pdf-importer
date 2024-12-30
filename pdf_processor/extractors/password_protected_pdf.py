from typing import Any, Dict

import fitz  # PyMuPDF

from ..core.base import BasePDFExtractor


class PasswordProtectedPDFExtractor(BasePDFExtractor):
    """비밀번호로 보호된 PDF에서 데이터를 추출하는 클래스"""

    def extract_text(self) -> str:
        try:
            if not self.password:
                raise ValueError("비밀번호가 필요한 PDF입니다.")

            # PyMuPDF를 사용하여 PDF 열기 (비밀번호 필수)
            doc = fitz.open(self.file_path, password=self.password)
            text = ""

            for page in doc:
                text += page.get_text() + "\n"

            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from password-protected PDF: {e}")
            return ""

    def extract_metadata(self) -> Dict[str, Any]:
        try:
            if not self.password:
                raise ValueError("비밀번호가 필요한 PDF입니다.")

            doc = fitz.open(self.file_path, password=self.password)
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "encryption": doc.is_encrypted,
                "needs_password": True,
            }
            doc.close()
            return metadata
        except Exception as e:
            print(f"Error extracting metadata from password-protected PDF: {e}")
            return {}
