import asyncio
import json
import logging
from typing import Any, Dict, Optional, Tuple

import fitz
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLM:
    """LLM을 사용한 데이터 추출 프로세서"""

    _instance: Optional["LLM"] = None
    _client: Optional[AsyncOpenAI] = None
    _semaphore: Optional[asyncio.Semaphore] = None
    _model_name: Optional[str] = None

    def __new__(cls, api_key: Optional[str] = None) -> "LLM":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: Optional[str] = None):
        # __new__에서 이미 처리되었으므로 초기화 생략
        pass

    @classmethod
    def initialize(cls, api_key: str, model_name: str = "gpt-4", max_concurrent: int = 2) -> "LLM":
        """LLM 초기화 (처리 시작 시 한 번만 호출)

        Args:
            api_key: OpenAI API 키
            model_name: 사용할 모델 이름 (기본값: "gpt-4")
            max_concurrent: 최대 동시 실행 수 (기본값: 2)
        """
        if not cls._instance:
            cls._instance = cls(api_key)
            cls._client = AsyncOpenAI(api_key=api_key)
            cls._semaphore = asyncio.Semaphore(max_concurrent)
            cls._model_name = model_name
        return cls._instance

    @classmethod
    def get_instance(cls) -> "LLM":
        """LLM 인스턴스 반환"""
        if not cls._instance or not cls._client or not cls._semaphore:
            raise RuntimeError("LLM가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return cls._instance

    def _create_function_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """스키마를 OpenAI function 형식으로 변환"""
        return {
            "name": "extract_data",
            "description": "텍스트에서 구조화된 데이터를 추출합니다.",
            "parameters": schema,
        }

    async def extract_data(
        self,
        pdf_path: str,
        page_range: Tuple[int, int],
        schema: Dict[str, Any],
        system_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """PDF 파일의 특정 페이지 범위에서 데이터 추출

        Args:
            pdf_path: PDF 파일 경로
            page_range: 처리할 페이지 범위 (시작, 끝)
            schema: 추출할 데이터의 스키마
            system_message: 사용자 정의 시스템 메시지 (기본값: None)

        Returns:
            추출된 데이터를 담은 딕셔너리
        """
        try:
            # PDF 파일 열기
            pdf_document = fitz.open(pdf_path)
            text = ""

            # 지정된 페이지 범위의 텍스트 추출
            for page_num in range(page_range[0], page_range[1] + 1):
                if 0 <= page_num < len(pdf_document):
                    page = pdf_document[page_num]
                    text += page.get_text()

            # Function calling 설정
            function_schema = self._create_function_schema(schema)

            # 기본 시스템 메시지
            default_system_message = (
                "You are a helpful assistant that extracts structured "
                "data from PDF documents. Always extract data according "
                "to the provided schema."
            )

            # 세마포어를 사용하여 동시 실행 제한
            async with self._semaphore:
                # LLM을 사용하여 데이터 추출
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

            # 응답 파싱
            try:
                function_call = response.choices[0].message.function_call
                result = json.loads(function_call.arguments)
                return result
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"JSON 파싱 오류: {e}")
                logger.error(f"원본 응답: {response.choices[0].message}")
                raise ValueError(f"LLM 응답을 JSON으로 파싱할 수 없습니다: {e}")

        except Exception as e:
            logger.error(f"데이터 추출 중 오류 발생: {e}")
            raise

        finally:
            if "pdf_document" in locals():
                pdf_document.close()
