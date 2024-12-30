import json
from typing import Any, Dict

from openai import OpenAI

from ..core.base import BaseDataProcessor


class LLMDataProcessor(BaseDataProcessor):
    """LLM을 사용하여 추출된 텍스트를 구조화된 데이터로 변환하는 클래스"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _create_function_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """스키마를 OpenAI function 형식으로 변환"""

        def _convert_to_json_schema(data: Dict[str, Any]) -> Dict[str, Any]:
            result = {"type": "object", "properties": {}}

            for key, value in data.items():
                if isinstance(value, dict):
                    result["properties"][key] = _convert_to_json_schema(value)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # 객체 배열인 경우
                    result["properties"][key] = {
                        "type": "array",
                        "items": _convert_to_json_schema(value[0]),
                    }
                elif isinstance(value, list):
                    # 단순 배열인 경우
                    result["properties"][key] = {"type": "array", "items": {"type": "string"}}
                else:
                    # 문자열 필드인 경우
                    result["properties"][key] = {"type": "string", "description": value}

            return result

        return {
            "name": "extract_data",
            "description": "텍스트에서 구조화된 데이터를 추출합니다.",
            "parameters": _convert_to_json_schema(schema),
        }

    def process(self, data: str) -> Dict[str, Any]:
        """LLM을 사용하여 텍스트를 구조화된 데이터로 변환"""
        # 작업 데이터에서 스키마 추출
        task_data = json.loads(data) if isinstance(data, str) else data
        text = task_data.get("text", "")
        schema = task_data.get("extraction_schema", {})

        # Function calling 설정
        function_schema = self._create_function_schema(schema)

        # LLM 호출
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "주어진 텍스트에서 요청된 형식에 맞게 데이터를 추출하는 전문가입니다.",
                },
                {
                    "role": "user",
                    "content": f"다음 텍스트에서 필요한 정보를 추출해주세요:\n\n{text}",
                },
            ],
            functions=[function_schema],
            function_call={"name": "extract_data"},
        )

        # 결과 파싱
        function_call = response.choices[0].message.function_call
        extracted_data = json.loads(function_call.arguments)

        return extracted_data

    def validate(self, processed_data: Dict[str, Any]) -> bool:
        """처리된 데이터의 유효성 검증"""
        try:
            # 기본적인 JSON 구조 검증
            json.dumps(processed_data)

            # 필수 필드 존재 여부 검증
            if not processed_data:
                return False

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
