import asyncio
import json
import logging
from typing import Any, Dict, Type

from ..extractors.copy_protected_pdf import CopyProtectedPDFExtractor
from ..extractors.password_protected_pdf import PasswordProtectedPDFExtractor
from ..extractors.scanned_pdf import ScannedPDFExtractor
from ..extractors.text_pdf import TextPDFExtractor
from ..processors.llm_processor import LLMDataProcessor
from .base import BasePDFExtractor
from .queue import BaseQueue, TaskStatus

logger = logging.getLogger(__name__)


class PDFWorker:
    """비동기 PDF 처리 작업자"""

    def __init__(self, queue: BaseQueue, openai_api_key: str):
        self.queue = queue
        self.openai_api_key = openai_api_key
        self.running = False
        self.llm_processor = LLMDataProcessor(api_key=openai_api_key)

    def _get_extractor_class(self, pdf_type: str) -> Type[BasePDFExtractor]:
        """PDF 유형에 따른 추출기 클래스 반환"""
        extractors = {
            "text": TextPDFExtractor,
            "scanned": ScannedPDFExtractor,
            "password_protected": PasswordProtectedPDFExtractor,
            "copy_protected": CopyProtectedPDFExtractor,
        }
        return extractors.get(pdf_type, TextPDFExtractor)

    def _validate_and_preprocess_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """작업 데이터 검증 및 전처리"""
        # 필수 필드 검증
        required_fields = ["file_path", "pdf_type", "extraction_schema"]
        for field in required_fields:
            if field not in task_data:
                raise ValueError(f"필수 필드가 누락되었습니다: {field}")

        # page_ranges와 invoice_count 처리
        page_ranges = task_data.get("page_ranges")
        invoice_count = task_data.get("invoice_count")

        if page_ranges:
            # page_ranges가 있는 경우 invoice_count 자동 설정
            task_data["invoice_count"] = len(page_ranges)
            logger.info(f"페이지 범위가 지정되어 인보이스 수를 자동 설정합니다: {len(page_ranges)}")
        elif invoice_count:
            # invoice_count만 있는 경우 그대로 사용
            logger.info(f"지정된 인보이스 수: {invoice_count}")
        else:
            # 둘 다 없는 경우 자동 감지 모드
            logger.info("인보이스 수 자동 감지 모드")
            task_data["invoice_count"] = None

        return task_data

    async def process_task(self, task_data: Dict[str, Any]) -> None:
        """작업 처리"""
        try:
            task_id = task_data["task_id"]
            pdf_type = task_data.get("pdf_type", "text")

            # 작업 상태 업데이트
            await self.queue.update_task_status(task_id, TaskStatus.PROCESSING, pdf_type)

            # 작업 데이터 검증 및 전처리
            task_data = self._validate_and_preprocess_task(task_data)

            # 추출기 초기화
            extractor_class = self._get_extractor_class(pdf_type)
            extractor = extractor_class(
                file_path=task_data["file_path"], password=task_data.get("password")
            )

            # 텍스트 추출
            text = extractor.extract_text()
            metadata = extractor.extract_metadata()

            # LLM 처리를 위한 데이터 준비
            processing_data = {
                "text": text,
                "extraction_schema": task_data["extraction_schema"],
                "page_ranges": task_data.get("page_ranges"),
                "invoice_count": task_data.get("invoice_count"),
            }

            # 텍스트 처리 및 구조화
            processed_data = self.llm_processor.process(json.dumps(processing_data))
            processed_data["metadata"] = metadata

            # 결과 검증
            if not self.llm_processor.validate(processed_data):
                raise ValueError("추출된 데이터가 유효하지 않습니다.")

            # 결과 저장
            await self.queue.store_result(
                task_id=task_id,
                result=processed_data,
                ttl=task_data.get("result_ttl", 3600),
                pdf_type=pdf_type,
            )

        except Exception as e:
            logger.error(f"작업 처리 중 오류 발생: {str(e)}")
            await self.queue.update_task_status(task_id, TaskStatus.FAILED, pdf_type)
            raise

    async def start(self, poll_interval: float = 1.0):
        """작업자 시작"""
        self.running = True
        while self.running:
            try:
                # 큐에서 다음 작업 가져오기
                task_data = await self.queue.dequeue()
                if task_data:
                    # 작업 처리
                    await self.process_task(task_data)
                else:
                    # 작업이 없으면 대기
                    await asyncio.sleep(poll_interval)
            except Exception as e:
                print(f"Worker error: {e}")
                await asyncio.sleep(poll_interval)

    async def stop(self):
        """작업자 중지"""
        self.running = False
