import json
from typing import Any, Dict

from openai import OpenAI

from ..core.base import BaseDataProcessor


class LLMDataProcessor(BaseDataProcessor):
    """LLM을 사용하여 추출된 텍스트를 구조화된 데이터로 변환하는 클래스"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def process(self, data: str) -> Dict[str, Any]:
        """LLM을 사용하여 텍스트를 구조화된 데이터로 변환"""
        prompt = f"""
        다음 텍스트를 분석하여 구조화된 JSON 형식으로 변환해주세요:

        {data}

        주의사항:
        1. 모든 중요한 정보를 포함해주세요
        2. 날짜, 금액, 이름 등 주요 필드는 별도로 구분해주세요
        3. 계층 구조가 있다면 적절히 표현해주세요
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured data from text.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    def validate(self, processed_data: Dict[str, Any]) -> bool:
        """처리된 데이터의 유효성 검증"""
        # 기본적인 JSON 구조 검증
        try:
            json.dumps(processed_data)
            return True
        except Exception as e:
            print(f"Error validating processed data: {e}")
            return False

    def transform(self, processed_data: Dict[str, Any], output_format: str = "json") -> Any:
        """데이터를 지정된 형식으로 변환"""
        if output_format == "json":
            return json.dumps(processed_data, ensure_ascii=False, indent=2)
        elif output_format == "dict":
            return processed_data
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
