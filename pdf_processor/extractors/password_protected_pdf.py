from typing import Any, Dict

import fitz  # PyMuPDF

from pdf_processor.extractors.base import BaseExtractor


class PasswordProtectedPDFExtractor(BaseExtractor):
    """Class for extracting data from password-protected PDFs"""

    def extract_text(self) -> str:
        try:
            if not self.password:
                raise ValueError("Password is required for this PDF.")

            # Open PDF using PyMuPDF (password required)
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
                raise ValueError("Password is required for this PDF.")

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
