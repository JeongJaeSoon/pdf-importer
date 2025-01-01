"""PDF 페이지 분석기"""

import logging
from typing import List

from pdf_processor.core.llm import LLM

logger = logging.getLogger(__name__)


class PDFPageAnalyzer:
    """PDF 페이지 분석기"""

    def __init__(self, api_key: str):
        """초기화

        Args:
            api_key: OpenAI API 키
        """
        self.llm = LLM(api_key=api_key)

    async def analyze_pages(self, text: str, expected_count: int | None = None) -> List[str]:
        """PDF 페이지 분석

        Args:
            text: PDF 텍스트
            expected_count: 예상되는 인보이스 수

        Returns:
            페이지 범위 리스트 (예: ["1-3", "4-5", "6"])
        """
        # LLM에게 전달할 프롬프트 생성
        prompt = self._create_prompt(text, expected_count)

        # LLM을 통한 페이지 분석
        response = await self.llm.process_text(prompt)

        # 응답 파싱 및 검증
        page_ranges = self._parse_response(response)
        if not self._validate_ranges(page_ranges, expected_count):
            raise ValueError("페이지 범위가 유효하지 않습니다.")

        return page_ranges

    def _create_prompt(self, text: str, expected_count: int | None = None) -> str:
        """프롬프트 생성

        Args:
            text: PDF 텍스트
            expected_count: 예상되는 인보이스 수

        Returns:
            LLM에게 전달할 프롬프트
        """
        base_prompt = (
            "주어진 PDF 문서에서 각각의 인보이스가 위치한 페이지 범위를 분석해주세요.\n"
            "다음과 같은 형식으로 응답해주세요:\n"
            "- 하나의 인보이스가 한 페이지에 있는 경우: '1'\n"
            "- 하나의 인보이스가 여러 페이지에 걸쳐 있는 경우: '1-3'\n"
            "- 여러 인보이스가 있는 경우 쉼표로 구분: '1-3,4,5-6'\n\n"
            "문서 내용:\n"
            f"{text}\n\n"
        )

        if expected_count is not None:
            base_prompt += f"\n참고: 이 문서에는 {expected_count}개의 인보이스가 있어야 합니다."

        return base_prompt

    def _parse_response(self, response: str) -> List[str]:
        """LLM 응답 파싱

        Args:
            response: LLM 응답

        Returns:
            페이지 범위 리스트
        """
        # 응답에서 페이지 범위만 추출
        ranges = [r.strip() for r in response.split(",")]

        # 각 범위가 올바른 형식인지 검증
        for r in ranges:
            if "-" in r:
                start, end = r.split("-")
                if not (start.isdigit() and end.isdigit() and int(start) <= int(end)):
                    raise ValueError(f"잘못된 페이지 범위 형식: {r}")
            elif not r.isdigit():
                raise ValueError(f"잘못된 페이지 번호 형식: {r}")

        return ranges

    def _validate_ranges(self, ranges: List[str], expected_count: int | None = None) -> bool:
        """페이지 범위 검증

        Args:
            ranges: 페이지 범위 리스트
            expected_count: 예상되는 인보이스 수

        Returns:
            검증 결과
        """
        if not ranges:
            return False

        # 페이지 번호가 중복되지 않는지 확인
        used_pages = set()
        for r in ranges:
            if "-" in r:
                start, end = map(int, r.split("-"))
                pages = set(range(start, end + 1))
            else:
                pages = {int(r)}

            if pages & used_pages:
                return False
            used_pages.update(pages)

        # 예상되는 인보이스 수와 일치하는지 확인
        if expected_count is not None and len(ranges) != expected_count:
            return False

        return True
