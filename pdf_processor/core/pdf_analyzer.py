import logging
from typing import List, Tuple

import fitz

from pdf_processor.processors.llm_processor import LLMProcessor

logger = logging.getLogger(__name__)


class PDFAnalyzer:
    """PDF 파일 분석 및 분할을 위한 클래스"""

    def __init__(self):
        """PDF 분석기 초기화"""
        self.llm_processor = LLMProcessor.get_instance()

    async def analyze_pdf(self, pdf_path: str, num_pages: int) -> List[Tuple[int, int]]:
        """PDF 파일을 분석하여 페이지 범위 결정

        Args:
            pdf_path: PDF 파일 경로
            num_pages: 예상되는 인보이스 문서 수

        Returns:
            페이지 범위 리스트 [(시작, 끝), ...] (0-based index)
        """
        try:
            # PDF 파일 열기
            pdf_document = fitz.open(pdf_path)
            total_pages = len(pdf_document)

            if total_pages == 0:
                raise ValueError("PDF 파일이 비어있습니다.")

            if num_pages <= 0:
                raise ValueError("문서 수는 1 이상이어야 합니다.")

            # 전체 텍스트 추출
            text = ""
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                text += f"\n=== 페이지 {page_num + 1} ===\n"  # 1-based 페이지 번호
                text += page.get_text()

            # LLM을 사용하여 페이지 범위 분석
            schema = {
                "type": "object",
                "properties": {
                    "page_ranges": {
                        "type": "array",
                        "description": "인보이스 문서별 페이지 범위 리스트",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_page": {
                                    "type": "integer",
                                    "description": "시작 페이지 번호 (1부터 시작)",
                                    "minimum": 1,
                                },
                                "end_page": {
                                    "type": "integer",
                                    "description": "끝 페이지 번호 (1부터 시작)",
                                    "minimum": 1,
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "이 페이지 범위를 하나의 인보이스로 판단한 근거",
                                },
                            },
                            "required": ["start_page", "end_page", "reason"],
                        },
                    }
                },
                "required": ["page_ranges"],
            }

            # LLM 분석 요청을 위한 시스템 메시지 구성
            system_message = (
                "당신은 PDF 문서에서 인보이스를 식별하고 페이지를 분할하는 전문가입니다. "
                "다음 정보를 바탕으로 인보이스 페이지 범위를 결정해주세요:\n"
                f"1. 전체 페이지 수: {total_pages}페이지\n"
                f"2. 포함된 인보이스 수: {num_pages}개\n"
                "3. 인보이스 구분 기준:\n"
                "   - 각 인보이스는 일반적으로 새로운 페이지에서 시작됩니다.\n"
                "   - 인보이스 번호, 날짜, 거래처 정보 등이 새로 시작되는 것이 새로운 인보이스의 시작점입니다.\n"
                "   - 동일한 인보이스의 연속 페이지는 일반적으로 페이지 번호나 연속성을 나타내는 표시가 있습니다.\n"
                "\n제공된 텍스트를 분석하여 정확히 {num_pages}개의 인보이스로 분할해주세요.\n"
                "주의: 페이지 번호는 1부터 시작하며, 1부터 {total_pages} 사이의 값이어야 합니다."
            )

            # LLM 분석 결과
            result = await self.llm_processor.extract_data(
                pdf_path,
                (0, total_pages - 1),
                schema,
                system_message=system_message,
            )

            page_ranges = []
            if not result or "page_ranges" not in result or not result["page_ranges"]:
                logger.warning("LLM 분석 결과가 없어 기본 분할 방식을 사용합니다.")
                pages_per_doc = max(1, total_pages // num_pages)
                for i in range(num_pages):
                    start_page = i * pages_per_doc
                    if start_page >= total_pages:
                        break
                    end_page = min((i + 1) * pages_per_doc - 1, total_pages - 1)
                    page_ranges.append((start_page, end_page))
                    logger.info(f"기본 분할 - 인보이스 {i+1}: 페이지 {start_page+1}-{end_page+1}")
            else:
                # LLM 분석 결과 사용 (1-based를 0-based로 변환)
                for range_info in result["page_ranges"]:
                    # 1-based를 0-based로 변환하고 범위 검증
                    start_page = max(0, min(total_pages - 1, range_info["start_page"] - 1))
                    end_page = max(0, min(total_pages - 1, range_info["end_page"] - 1))

                    if start_page <= end_page:
                        page_ranges.append((start_page, end_page))
                        logger.info(
                            f"인보이스 페이지 범위: {start_page+1}-{end_page+1}, "
                            f"근거: {range_info.get('reason', '정보 없음')}"
                        )

                # 결과 검증
                if len(page_ranges) != num_pages:
                    logger.warning(
                        "LLM이 반환한 인보이스 수가 예상 수와 다릅니다. "
                        f"(반환: {len(page_ranges)}, 예상: {num_pages}) "
                        "기본 분할 방식을 사용합니다."
                    )
                    page_ranges = []
                    pages_per_doc = max(1, total_pages // num_pages)
                    for i in range(num_pages):
                        start_page = i * pages_per_doc
                        if start_page >= total_pages:
                            break
                        end_page = min((i + 1) * pages_per_doc - 1, total_pages - 1)
                        page_ranges.append((start_page, end_page))
                        logger.info(
                            f"기본 분할 - 인보이스 {i+1}: 페이지 {start_page+1}-{end_page+1}"
                        )

            logger.info(f"PDF 분석 완료 - 페이지 범위: {[(s+1, e+1) for s, e in page_ranges]}")
            return page_ranges

        except Exception as e:
            logger.error(f"PDF 분석 중 오류 발생: {e}")
            raise

        finally:
            if "pdf_document" in locals():
                pdf_document.close()
