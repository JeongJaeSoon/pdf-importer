from typing import Any, Dict

from pypdf import PdfReader

from pdf_processor.extractors.base import BaseExtractor


class TextPDFExtractor(BaseExtractor):
    """Class for extracting data from plain text PDFs"""

    def extract_text(self) -> str:
        reader = PdfReader(self.file_path, password=self.password)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

    def extract_metadata(self) -> Dict[str, Any]:
        reader = PdfReader(self.file_path, password=self.password)
        return dict(reader.metadata) if reader.metadata else {}
