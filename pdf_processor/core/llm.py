import asyncio
import json
import logging
from typing import Any, Dict, Optional, Tuple

import fitz
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLM:
    """Data extraction processor using LLM"""

    _instance: Optional["LLM"] = None
    _client: Optional[AsyncOpenAI] = None
    _semaphore: Optional[asyncio.Semaphore] = None
    _model_name: Optional[str] = None

    def __new__(cls, api_key: Optional[str] = None) -> "LLM":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: Optional[str] = None):
        # Skip initialization as it's already handled in __new__
        pass

    @classmethod
    def initialize(cls, api_key: str, model_name: str = "gpt-4", max_concurrent: int = 2) -> "LLM":
        """Initialize LLM (called once when starting processing)

        Args:
            api_key: OpenAI API key
            model_name: Model name to use (default: "gpt-4")
            max_concurrent: Maximum number of concurrent executions (default: 2)
        """
        if not cls._instance:
            cls._instance = cls(api_key)
            cls._client = AsyncOpenAI(api_key=api_key)
            cls._semaphore = asyncio.Semaphore(max_concurrent)
            cls._model_name = model_name
        return cls._instance

    @classmethod
    def get_instance(cls) -> "LLM":
        """Return LLM instance"""
        if not cls._instance or not cls._client or not cls._semaphore:
            raise RuntimeError("LLM is not initialized. Call initialize() first.")
        return cls._instance

    def _create_function_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert schema to OpenAI function format"""
        return {
            "name": "extract_data",
            "description": "Extract structured data from text.",
            "parameters": schema,
        }

    async def extract_data(
        self,
        pdf_path: str,
        page_range: Tuple[int, int],
        schema: Dict[str, Any],
        system_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract data from specific page range of PDF file

        Args:
            pdf_path: Path to PDF file
            page_range: Page range to process (start, end)
            schema: Schema for data extraction
            system_message: Custom system message (default: None)

        Returns:
            Dictionary containing extracted data
        """
        try:
            # Open PDF file
            pdf_document = fitz.open(pdf_path)
            text = ""

            # Extract text from specified page range
            for page_num in range(page_range[0], page_range[1] + 1):
                if 0 <= page_num < len(pdf_document):
                    page = pdf_document[page_num]
                    text += page.get_text()

            # Set up function calling
            function_schema = self._create_function_schema(schema)

            # Default system message
            default_system_message = (
                "You are a helpful assistant that extracts structured "
                "data from PDF documents. Always extract data according "
                "to the provided schema."
            )

            # Limit concurrent executions using semaphore
            async with self._semaphore:
                # Extract data using LLM
                response = await self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": system_message or default_system_message,
                        },
                        {"role": "user", "content": text},
                    ],
                    functions=[function_schema],
                    function_call={"name": "extract_data"},
                    temperature=0.0,
                )

            # Parse response
            try:
                function_call = response.choices[0].message.function_call
                result = json.loads(function_call.arguments)
                return result
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Original response: {response.choices[0].message}")
                raise ValueError(f"Cannot parse LLM response as JSON: {e}")

        except Exception as e:
            logger.error(f"Error during data extraction: {e}")
            raise

        finally:
            if "pdf_document" in locals():
                pdf_document.close()
