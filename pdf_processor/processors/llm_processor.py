import json
import logging
from typing import Any, Dict

from openai import OpenAI

from ..core.base import BaseDataProcessor

logger = logging.getLogger(__name__)


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
        try:
            # 작업 데이터에서 스키마 추출
            task_data = json.loads(data) if isinstance(data, str) else data
            text = task_data.get("text", "")
            schema = task_data.get("extraction_schema", {})
            page_ranges = task_data.get("page_ranges")
            invoice_count = task_data.get("invoice_count")

            # Function calling 설정
            function_schema = self._create_function_schema(schema)

            # 시스템 메시지 준비
            system_message = """
당신은 PDF에서 인보이스 데이터를 추출하는 전문가입니다.
당신의 역할은 주어진 텍스트에서 인보이스 데이터를 정확하게 추출하는 것입니다.

절대적 원칙:
1. 데이터 무결성
   - 텍스트에 명시적으로 존재하는 데이터만 추출
   - 추측이나 가정 절대 금지
   - 불확실한 정보는 모두 빈 값으로 처리

2. 사용자 지정값 준수
   - invoice_count 지정 시:
     * 정확히 지정된 수의 인보이스만 처리
     * 더 적은 수의 인보이스만 있다면 발견된 것만 반환
     * 더 많은 인보이스가 있어도 지정된 수만큼만 반환

   - page_ranges 지정 시:
     * 지정된 페이지 범위 내의 데이터만 처리
     * 범위를 벗어난 데이터는 완전히 무시
     * 범위 내 인보이스가 없다면 빈 배열([]) 반환

   - 두 값 모두 지정 시:
     * page_ranges 우선 적용 후 invoice_count 적용
     * 범위 내에서 지정된 수만큼만 처리
     * 조건을 만족하는 인보이스가 없으면 빈 배열([]) 반환

3. 빈 값 처리 규칙
   문자열 필드 = ""
   숫자 필드 = null
   날짜 필드 = ""
   배열 필드 = []
   객체 필드 = {}

4. 인보이스 식별 기준
   - 새로운 인보이스 번호
   - 새로운 발행일자
   - 새로운 거래처 정보
   - 명확한 페이지 구분
   * 모호한 경우 별도 인보이스로 취급하지 않음

5. 데이터 검증
   - 모든 필수 필드 존재 확인
   - 금액 계산 정확성 검증
   - 날짜 형식 검증 (YYYY-MM-DD)
   - 검증 실패 시 해당 필드 빈 값 처리

6. 오류 처리
   - 인보이스 아닌 경우: []
   - 형식 불일치: 최대한 빈 값 처리
   - 불완전한 데이터: 검증 가능한 부분만 추출

7. 특수 필드 처리
   - 품목(items):
     * 명확한 품목 정보만 포함
     * 불완전한 품목은 제외
     * 금액/수량 불명확 시 null

   - 세금 정보:
     * 명시적인 세금 정보만 포함
     * 세율/세액 불명확 시 null
     * 세금 유형 불명확 시 ""

   - 거래처 정보:
     * 모든 하위 필드 개별 검증
     * 불명확한 필드는 개별적으로 빈 값 처리

결과 반환 시 최종 검증:
1. 지정된 invoice_count/page_ranges 준수 여부
2. 모든 빈 값이 올바른 타입으로 설정되었는지 확인
3. 날짜 형식의 일관성
4. 금액 필드의 숫자 타입 확인
"""

            # 사용자 메시지 준비
            user_message = f"""다음 텍스트에서 인보이스 데이터를 추출해주세요.

[제약 조건]
- 페이지 범위: {page_ranges if page_ranges else '자동 감지'}
- 인보이스 수: {invoice_count if invoice_count else '자동 감지'}

위 제약 조건을 반드시 준수하세요:
1. 페이지 범위가 지정된 경우 범위를 벗어난 데이터는 절대 포함하지 마세요
2. 인보이스 수가 지정된 경우 정확히 그 수만큼만 처리하세요
3. 조건을 만족하는 데이터가 부족하면 발견된 것만 반환하세요
4. 텍스트에 명시적으로 존재하지 않는 정보는 절대 포함하지 마세요

텍스트:
{text}
"""

            try:
                # LLM 호출
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    functions=[function_schema],
                    function_call={"name": "extract_data"},
                    temperature=0.0,  # 결정적인 출력을 위해 temperature를 0으로 설정
                )

                # 결과 파싱
                function_call = response.choices[0].message.function_call
                try:
                    # JSON 문자열 정리
                    json_str = function_call.arguments.strip()
                    # 이스케이프되지 않은 특수 문자 처리
                    json_str = json_str.replace("\n", "\\n").replace("\r", "\\r")

                    extracted_data = json.loads(json_str)
                    return extracted_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 파싱 오류: {str(e)}")
                    logger.error(f"원본 JSON 문자열: {function_call.arguments}")

                    # JSON 파싱 실패 시 기본값 반환
                    return {
                        "invoices": [],
                        "error": f"JSON 파싱 오류: {str(e)}",
                        "original_response": function_call.arguments,
                    }

            except Exception as e:
                logger.error(f"LLM 처리 중 오류 발생: {str(e)}")
                return {"invoices": [], "error": f"처리 오류: {str(e)}"}

        except Exception as e:
            logger.error(f"입력 데이터 처리 중 오류 발생: {str(e)}")
            return {"invoices": [], "error": f"입력 데이터 오류: {str(e)}"}

    def validate(self, processed_data: Dict[str, Any]) -> bool:
        """처리된 데이터의 유효성 검증"""
        try:
            # 기본적인 JSON 구조 검증
            json.dumps(processed_data)

            # 필수 필드 존재 여부 검증
            if not processed_data:
                return False

            # 인보이스 배열 검증
            if "invoices" in processed_data:
                if not isinstance(processed_data["invoices"], list):
                    return False
                if not processed_data["invoices"]:
                    return False
                for invoice in processed_data["invoices"]:
                    if not isinstance(invoice, dict):
                        return False
                    if "invoice_number" not in invoice:
                        return False

            return True
        except Exception as e:
            logger.error(f"데이터 검증 중 오류 발생: {str(e)}")
            return False

    def transform(self, processed_data: Dict[str, Any], output_format: str = "json") -> Any:
        """데이터를 지정된 형식으로 변환"""
        if output_format == "json":
            return json.dumps(processed_data, ensure_ascii=False, indent=2)
        elif output_format == "dict":
            return processed_data
        else:
            raise ValueError(f"지원하지 않는 출력 형식: {output_format}")
