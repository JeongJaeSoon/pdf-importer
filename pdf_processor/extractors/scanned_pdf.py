from typing import Any, Dict

import pytesseract
from pdf2image import convert_from_path

from pdf_processor.extractors.base import BaseExtractor


class ScannedPDFExtractor(BaseExtractor):
    """Class for extracting data from scanned PDFs using OCR"""

    def extract_text(self) -> str:
        # Convert PDF to images
        images = convert_from_path(self.file_path)
        text = ""

        # Perform OCR on each page
        for image in images:
            text += pytesseract.image_to_string(image, lang="kor+eng") + "\n"

        return text.strip()

    def extract_metadata(self) -> Dict[str, Any]:
        # Metadata might be limited for scanned PDFs
        try:
            from pypdf import PdfReader

            reader = PdfReader(self.file_path, password=self.password)
            return dict(reader.metadata) if reader.metadata else {}
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
