from typing import Any, Dict

import fitz  # PyMuPDF

from pdf_processor.extractors.base import BaseExtractor


class CopyProtectedPDFExtractor(BaseExtractor):
    """Class for extracting data from copy-protected PDFs"""

    def extract_text(self) -> str:
        try:
            doc = fitz.open(self.file_path)
            text = ""

            for page in doc:
                # Bypass copy protection to extract text
                # PyMuPDF extracts text directly from PDF content
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
