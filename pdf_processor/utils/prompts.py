"""PDF 처리를 위한 프롬프트 모음"""

from typing import Dict, Optional


def _format_metadata(metadata: Optional[Dict] = None) -> str:
    """메타데이터를 프롬프트에 포함시킬 수 있는 형식으로 변환

    Args:
        metadata: 메타데이터 딕셔너리 (선택사항)

    Returns:
        포맷된 메타데이터 문자열
    """
    if not metadata:
        return ""

    formatted_lines = []
    for key, value in metadata.items():
        # 리스트인 경우 각 항목을 들여쓰기하여 표시
        if isinstance(value, list):
            formatted_lines.append(f"{key}:")
            for item in value:
                formatted_lines.append(f"  - {item}")
        # 딕셔너리인 경우 재귀적으로 처리
        elif isinstance(value, dict):
            formatted_lines.append(f"{key}:")
            sub_items = _format_metadata(value).split("\n")
            formatted_lines.extend(f"  {item}" for item in sub_items if item)
        else:
            formatted_lines.append(f"{key}: {value}")

    return "\n".join(formatted_lines)


def get_pdf_analysis_prompt(
    total_pages: int, num_pages: int, metadata: Optional[Dict] = None
) -> str:
    """PDF 분석을 위한 프롬프트 생성

    Args:
        total_pages: 전체 페이지 수
        num_pages: 예상되는 인보이스 수
        metadata: PDF 파일 관련 메타데이터 (선택사항)

    Returns:
        프롬프트 문자열
    """
    base_prompt = f"""
당신은 PDF 문서에서 인보이스를 식별하고 페이지를 분할하는 전문가입니다.
다음 정보를 바탕으로 인보이스 페이지 범위를 결정해주세요:

1. 전체 페이지 수: {total_pages}페이지
2. 포함된 인보이스 수: {num_pages}개
3. 인보이스 구분 기준:
   - 각 인보이스는 일반적으로 새로운 페이지에서 시작됩니다.
   - 인보이스 번호, 날짜, 거래처 정보 등이 새로 시작되는 것이 새로운 인보이스의 시작점입니다.
   - 동일한 인보이스의 연속 페이지는 일반적으로 페이지 번호나 연속성을 나타내는 표시가 있습니다.
"""

    if metadata:
        metadata_str = _format_metadata(metadata)
        base_prompt += f"""
4. 추가 정보:
{metadata_str}

위 추가 정보를 활용하여 더 정확한 페이지 분할을 수행해주세요.
특히 customer_names가 제공된 경우, 각 인보이스의 거래처 정보와 매칭하여 페이지를 분할해주세요.
"""

    base_prompt += f"""
제공된 텍스트를 분석하여 정확히 {num_pages}개의 인보이스로 분할해주세요.
주의: 페이지 번호는 1부터 시작하며, 1부터 {total_pages} 사이의 값이어야 합니다.
"""

    return base_prompt


def get_invoice_processor_prompt(
    analysis_reason: Optional[str] = None, metadata: Optional[Dict] = None
) -> str:
    """인보이스 데이터 추출을 위한 프롬프트 생성

    Args:
        analysis_reason: PDF 분석기가 제공한 페이지 범위 결정 근거 (선택사항)
        metadata: PDF 파일 관련 메타데이터 (선택사항)

    Returns:
        프롬프트 문자열
    """
    base_prompt = """
당신은 청구서 데이터를 추출하는 전문가입니다. 다음 규칙에 따라 데이터를 추출해주세요:

1. 데이터 무결성 원칙:
   - 명시적으로 표시된 데이터만 추출
   - 임의로 데이터를 생략하거나 추가하지 않음
   - 추측이나 가정 금지
   - 계산된 값보다 표시된 값 우선
   - 모든 금액은 쉼표/통화기호 제외한 숫자로 추출

2. 품목 리스트 처리:
   - 포목 데이터 추출 기준:
     * 품목명이 있는 경우에만 데이터 추출 (빈 문자열("")도 가능)
     * 수량과 단가가 모두 있는 경우에만 품목으로 처리
     * 수량이나 단가가 없는 경우는 품목이 아닌 것으로 간주
   - 제외 대상:
     * 메모/설명만 있는 행 (수량/단가/금액 없음)
     * 카테고리/구분용 텍스트 행
     * 소계/합계/중간합계 행
     * 부가설명이나 주석 행
   - 품목명 처리:
     * 품목명이 빈 문자열("")인 경우도 유효한 데이터로 처리
     * 품목에 대한 부가 설명은 해당 품목의 item_name에 포함
     * 독립적인 메모/설명 행은 품목에서 제외
   - 품목 데이터 검증:
     * 품목명이 있더라도 수량/단가가 없으면 제외
     * 수량과 단가가 있더라도 명백한 소계/합계 행이면 제외
     * 의심스러운 경우 제외 (데이터 무결성 원칙 준수)

3. 금액 추출 규칙:
   - 금액 검증 우선순위:
     * 1순위: 첫 페이지 상단과 마지막 페이지 하단의 명시적 금액
     * 2순위: 품목 리스트를 통한 계산 금액
     * 차이가 있는 경우 항상 명시적 금액을 우선
   - 금액 위치:
     * 첫 페이지: 상단 또는 헤더 영역에서 검색
     * 마지막 페이지: 하단 또는 푸터 영역에서 검색
   - 금액 종류별 처리:
     * 공급가액(subtotal):
       - 검색 키워드: "공급가액", "소계", "小計", "subtotal", "금액", "金額" 등
       - 세액/총액과 구분되는 금액을 찾아 추출
     * 세액(tax_amount):
       - 검색 키워드: "세액", "소비세", "消費税", "tax", "부가가치세", "VAT" 등
       - 일반적으로 공급가액의 10%이나, 반드시 명시된 값 사용
     * 총액/청구금액(total_amount):
       - 검색 키워드: "합계", "총액", "청구금액", "総額", "請求金額", "total", "grand total" 등
       - 공급가액과 세액의 합계와 일치하는지 검증
       - 차이가 있는 경우 명시된 총액을 우선
   - 금액 검증:
     * 각 금액이 여러 번 표시된 경우 일치 여부 확인
     * 일치하지 않는 경우 첫 페이지 금액 우선
     * 공급가액 + 세액 = 총액 관계 확인
     * 차이가 있는 경우 명시적으로 표시된 각각의 금액 사용
   - 음수 처리:
     * 반품/할인/환불 등의 경우 음수 가능
     * 공급가액이 음수인 경우 세액도 음수
     * 마이너스 기호, 괄호 등 다양한 음수 표기 처리

4. 빈 값 처리:
   - 문자열: 빈 문자열("")
   - 숫자: null
   - 날짜: 빈 문자열("")
   - 배열: 빈 배열([])
   - 객체: 빈 객체({})

5. 데이터 검증:
   - 필수 필드 존재 여부 확인
   - 금액 계산 정확성 검증
   - 날짜 형식 검증 (YYYY-MM-DD)
   - 검증 실패 시 해당 필드 빈 값 처리

6. 오류 처리:
   - 형식 불일치: 검증 가능한 부분만 추출
   - 불완전한 데이터: 확인된 부분만 추출
   - 모호한 데이터: 빈 값으로 처리
"""

    if metadata:
        metadata_str = _format_metadata(metadata)
        base_prompt += f"""

7. 추가 정보:
{metadata_str}

위 추가 정보를 활용하여 더 정확한 데이터 추출을 수행해주세요.
특히 customer_names가 제공된 경우, 해당 정보를 활용하여 거래처 정보를 정확하게 매칭해주세요.
"""

    if analysis_reason:
        base_prompt += f"""

분석 근거:
{analysis_reason}

위 분석 결과를 참고하여 데이터를 추출해주세요. 특히 금액 정보가 언급된 경우 해당 위치를 우선적으로 확인하세요.
"""

    return base_prompt
