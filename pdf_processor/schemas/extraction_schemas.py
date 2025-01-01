from typing import Dict, List, TypedDict


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
    customer_registration_number: str  # 고객 사업자등록번호
    items: List[InvoiceItemDict]  # 품목 리스트
    subtotal: float  # 공급가액
    taxes: List[InvoiceTaxDict]  # 세금 정보
    total_amount: float  # 총액


# 인보이스 추출 스키마
INVOICE_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string", "description": "인보이스 번호"},
        "issue_date": {"type": "string", "description": "발행일 (YYYY-MM-DD 형식)"},
        "due_date": {"type": "string", "description": "지급기한 (YYYY-MM-DD 형식)"},
        "customer_name": {"type": "string", "description": "고객명"},
        "customer_registration_number": {
            "type": "string",
            "description": "고객 사업자등록번호",
        },
        "items": {
            "type": "array",
            "description": "품목 리스트",
            "items": {
                "type": "object",
                "properties": {
                    "item_name": {"type": "string", "description": "품목명"},
                    "quantity": {"type": "integer", "description": "수량"},
                    "unit_price": {"type": "number", "description": "단가"},
                    "amount": {"type": "number", "description": "금액"},
                },
                "required": ["item_name", "quantity", "unit_price", "amount"],
            },
        },
        "subtotal": {"type": "number", "description": "공급가액"},
        "taxes": {
            "type": "array",
            "description": "세금 정보",
            "items": {
                "type": "object",
                "properties": {
                    "tax_type": {"type": "string", "description": "세금 유형 (예: VAT, 소득세 등)"},
                    "tax_rate": {"type": "number", "description": "세율 (%)"},
                    "tax_amount": {"type": "number", "description": "세액"},
                },
                "required": ["tax_type", "tax_rate", "tax_amount"],
            },
        },
        "total_amount": {"type": "number", "description": "총액"},
    },
    "required": [
        "invoice_number",
        "issue_date",
        "due_date",
        "customer_name",
        "customer_registration_number",
        "items",
        "subtotal",
        "taxes",
        "total_amount",
    ],
}
