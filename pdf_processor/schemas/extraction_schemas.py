from typing import Any, Dict, List, TypedDict


class InvoiceItemDict(TypedDict):
    """인보이스 항목 정보"""

    item_name: str  # 품목명
    quantity: int  # 수량
    unit_price: float  # 단가
    amount: float  # 금액


class InvoiceTaxDict(TypedDict):
    """인보이스 세금 정보"""

    tax_type: str  # 세금 유형 (예: VAT, 소득세 등)
    tax_rate: float  # 세율
    tax_amount: float  # 세액


class InvoiceDict(TypedDict):
    """인보이스 전체 정보"""

    invoice_number: str  # 인보이스 번호
    issue_date: str  # 발행일
    due_date: str  # 지급기한
    customer_name: str  # 고객명
    items: List[InvoiceItemDict]  # 품목 리스트
    subtotal: float  # 공급가액
    taxes: List[InvoiceTaxDict]  # 세금 정보
    total_amount: float  # 총액


# 인보이스 추출 스키마
INVOICE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_number": {
            "type": "string",
            "description": (
                "인보이스 번호 - 필수 필드\n"
                "- 위치: 첫 페이지 우측 상단\n"
                "- 라벨: '인보이스 번호:', '청구서 번호:', 'Invoice No:' 등\n"
                "- 검증: 영문/숫자/특수문자 조합"
            ),
        },
        "issue_date": {
            "type": "string",
            "description": (
                "발행일 - 필수 필드\n"
                "- 위치: 첫 페이지 상단\n"
                "- 라벨: '발행일:', '작성일:', 'Issue Date:' 등\n"
                "- 형식: YYYY-MM-DD"
            ),
        },
        "due_date": {
            "type": "string",
            "description": (
                "지급기한 - 필수 필드\n"
                "- 위치: 발행일 근처\n"
                "- 라벨: '지급기한:', '만기일:', 'Due Date:' 등\n"
                "- 형식: YYYY-MM-DD"
            ),
        },
        "customer_name": {
            "type": "string",
            "description": (
                "고객명 - 필수 필드\n"
                "- 위치: 첫 페이지 좌측 상단\n"
                "- 형식: 회사명/지사명 (경칭 제외)"
            ),
        },
        "items": {
            "type": "array",
            "description": (
                "품목 리스트 - 필수 필드\n"
                "- 구조: 표 형태의 품목 정보\n"
                "- 포함 조건:\n"
                "  * 품목명(item_name)이 있고\n"
                "  * 수량(quantity)이 있고\n"
                "  * 단가(unit_price)가 있고\n"
                "  * 금액(amount)이 있는 항목만 포함\n"
                "- 제외 대상:\n"
                "  * 카테고리/구분용 텍스트\n"
                "  * 메모/설명만 있는 행 (수량/단가/금액 없음)\n"
                "  * 소계/합계 행\n"
                "  * 수량/단가/금액 중 하나라도 없는 항목\n"
                "- 메모/설명 처리:\n"
                "  * 품목에 대한 부가 설명은 해당 품목의 item_name에 포함\n"
                "  * 독립적인 메모/설명 행은 품목에서 제외"
            ),
            "items": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": (
                            "품목명\n"
                            "- 상품/서비스 명칭\n"
                            "- 관련 메모나 설명 포함 가능\n"
                            "- 카테고리/구분용 텍스트 제외"
                        ),
                    },
                    "quantity": {
                        "type": "integer",
                        "description": (
                            "수량\n" "- 정수값\n" "- 양수/음수 모두 가능 (반품 등의 경우 음수)"
                        ),
                    },
                    "unit_price": {
                        "type": "number",
                        "description": (
                            "단가\n"
                            "- 쉼표/통화기호 제외한 숫자\n"
                            "- 양수/음수 모두 가능 (할인 등의 경우 음수)"
                        ),
                    },
                    "amount": {
                        "type": "number",
                        "description": (
                            "금액\n" "- quantity * unit_price와 일치\n" "- 양수/음수 모두 가능"
                        ),
                    },
                },
                "required": ["item_name", "quantity", "unit_price", "amount"],
            },
        },
        "subtotal": {
            "type": "number",
            "description": (
                "공급가액 - 필수 필드\n"
                "- 위치 및 검증:\n"
                "  * 첫 페이지 상단의 금액과 마지막 페이지 합계 금액을 비교\n"
                "  * 두 금액이 유사하거나 일치하는 경우 해당 값 사용\n"
                "  * 차이가 있는 경우 첫 페이지 금액 우선\n"
                "- 라벨: '공급가액:', '소계:', '합계:', 'Subtotal:' 등\n"
                "- 음수 가능 (전체가 반품/할인인 경우)"
            ),
        },
        "taxes": {
            "type": "array",
            "description": (
                "세금 정보 - 필수 필드\n"
                "- 위치 및 검증:\n"
                "  * 첫 페이지 상단의 세액과 마지막 페이지 합계 세액을 비교\n"
                "  * 두 금액이 유사하거나 일치하는 경우 해당 값 사용\n"
                "  * 차이가 있는 경우 첫 페이지 금액 우선\n"
                "- 구조: 세금 유형별 정보\n"
                "- 음수 가능 (공급가액이 음수인 경우)"
            ),
            "items": {
                "type": "object",
                "properties": {
                    "tax_type": {
                        "type": "string",
                        "description": "세금 유형 (예: 'VAT', '부가가치세', '소득세' 등)",
                    },
                    "tax_rate": {
                        "type": "number",
                        "description": ("세율\n" "- % 기호 제외한 숫자\n" "- 0 이상 100 이하"),
                    },
                    "tax_amount": {
                        "type": "number",
                        "description": (
                            "세액\n"
                            "- 쉼표/통화기호 제외한 숫자\n"
                            "- 청 페이지와 마지막 페이지의 세액 비교하여 검증\n"
                            "- 양수/음수 모두 가능"
                        ),
                    },
                },
                "required": ["tax_type", "tax_rate", "tax_amount"],
            },
        },
        "total_amount": {
            "type": "number",
            "description": (
                "총액 - 필수 필드\n"
                "- 위치 및 검증:\n"
                "  * 첫 페이지 상단의 금액과 마지막 페이지 합계 금액을 비교\n"
                "  * 두 금액이 유사하거나 일치하는 경우 해당 값 사용\n"
                "  * 차이가 있는 경우 첫 페이지 금액 우선\n"
                "- 라벨: '총액:', '합계:', '청구금액:', 'Total:' 등\n"
                "- 음수 가능 (전체가 반품/할인인 경우)"
            ),
        },
    },
    "required": [
        "invoice_number",
        "issue_date",
        "due_date",
        "customer_name",
        "items",
        "subtotal",
        "taxes",
        "total_amount",
    ],
}
