"""프롬프트 관리 모듈"""

from typing import Any, Dict


class BasePromptTemplate:
    """프롬프트 템플릿 기본 클래스"""

    def __init__(self, template: str):
        self.template = template.strip()

    def format(self, **kwargs) -> str:
        """템플릿에 변수를 적용하여 프롬프트 생성"""
        return self.template.format(**kwargs)


class SystemPrompts:
    """시스템 프롬프트 모음"""

    DATA_EXTRACTION = BasePromptTemplate(
        """
당신은 PDF에서 데이터를 추출하는 전문가입니다.
당신의 역할은 주어진 텍스트에서 데이터를 정확하게 추출하는 것입니다.

절대적 원칙:
1. 데이터 무결성
   - 텍스트에 명시적으로 존재하는 데이터만 추출
   - 추측이나 가정 절대 금지
   - 불확실한 정보는 모두 빈 값으로 처리

2. 사용자 지정값 준수
   - 지정된 페이지 범위 내의 데이터만 처리
   - 범위를 벗어난 데이터는 완전히 무시
   - 범위 내 데이터가 없다면 빈 배열([]) 반환

3. 빈 값 처리 규칙
   문자열 필드 = ""
   숫자 필드 = null
   날짜 필드 = ""
   배열 필드 = []
   객체 필드 = {{}}

4. 데이터 검증
   - 모든 필수 필드 존재 확인
   - 금액 계산 정확성 검증
   - 날짜 형식 검증 (YYYY-MM-DD)
   - 검증 실패 시 해당 필드 빈 값 처리

5. 오류 처리
   - 형식 불일치: 최대한 빈 값 처리
   - 불완전한 데이터: 검증 가능한 부분만 추출
"""
    )

    INVOICE_EXTRACTION = BasePromptTemplate(
        """
{base_rules}

추가 규칙:
1. 인보이스 식별 기준
   - 새로운 인보이스 번호
   - 새로운 발행일자
   - 새로운 거래처 정보
   - 명확한 페이지 구분
   * 모호한 경우 별도 인보이스로 취급하지 않음

2. 특수 필드 처리
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
"""
    )


class AnalysisPrompts:
    """분석용 프롬프트 모음"""

    PAGE_RANGE_ANALYSIS = BasePromptTemplate(
        """
이 PDF 파일에는 {count}개의 {doc_type}가 포함되어 있습니다.
각 {doc_type}가 몇 페이지에 걸쳐있는지 분석하고, 각 {doc_type}의 시작과 끝 페이지를 알려주세요.

응답은 다음과 같은 형식으로 해주세요:
[
    {{"start_page": 1, "end_page": 2}},
    {{"start_page": 3, "end_page": 3}},
    ...
]

주의사항:
1. 페이지 번호는 1부터 시작합니다.
2. end_page는 inclusive입니다.
3. 각 {doc_type}의 경계가 명확하지 않은 경우, 가능한 보수적으로 판단하여 분리하세요.
4. {count}개보다 적은 수의 {doc_type}만 발견된 경우, 발견된 것만 반환하세요.
"""
    )


class ExtractionPrompts:
    """데이터 추출용 프롬프트 모음"""

    INVOICE_EXTRACTION = BasePromptTemplate(
        """
이 PDF 파일은 하나의 청구서입니다.
파일에서 모든 청구서 정보를 추출하여 다음 스키마에 맞게 JSON 형식으로 반환해주세요:

{schema}

다음 사항을 지켜주세요:
1. 모든 금액은 숫자 형식으로 변환 (예: "1,234,567" -> 1234567)
2. 날짜는 YYYY-MM-DD 형식으로 변환
3. 비어있는 필드는 null로 표시
4. 금액 관련 필드는 모두 숫자 타입으로 변환
"""
    )


def get_system_prompt(prompt_type: str, **kwargs) -> str:
    """시스템 프롬프트 생성"""
    prompt_template = getattr(SystemPrompts, prompt_type, None)
    if not prompt_template:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    if prompt_type == "INVOICE_EXTRACTION":
        # 기본 규칙을 포함하여 생성
        kwargs["base_rules"] = SystemPrompts.DATA_EXTRACTION.format()

    return prompt_template.format(**kwargs)


def get_analysis_prompt(doc_type: str, count: int) -> str:
    """분석 프롬프트 생성"""
    return AnalysisPrompts.PAGE_RANGE_ANALYSIS.format(doc_type=doc_type, count=count)


def get_extraction_prompt(doc_type: str, schema: Dict[str, Any]) -> str:
    """추출 프롬프트 생성"""
    if doc_type == "invoice":
        return ExtractionPrompts.INVOICE_EXTRACTION.format(schema=schema)
    else:
        raise ValueError(f"Unsupported document type: {doc_type}")
