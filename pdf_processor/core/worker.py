import asyncio
from typing import Type

from ..extractors.copy_protected_pdf import CopyProtectedPDFExtractor
from ..extractors.password_protected_pdf import PasswordProtectedPDFExtractor
from ..extractors.scanned_pdf import ScannedPDFExtractor
from ..extractors.text_pdf import TextPDFExtractor
from ..processors.llm_processor import LLMDataProcessor
from .base import BasePDFExtractor
from .queue import BaseQueue, TaskStatus


class PDFWorker:
    """비동기 PDF 처리 작업자"""

    def __init__(self, queue: BaseQueue, openai_api_key: str):
        self.queue = queue
        self.openai_api_key = openai_api_key
        self.running = False

    def _get_extractor_class(self, pdf_type: str) -> Type[BasePDFExtractor]:
        """PDF 유형에 따른 적절한 추출기 클래스 반환"""
        extractors = {
            "text": TextPDFExtractor,
            "scanned": ScannedPDFExtractor,
            "password_protected": PasswordProtectedPDFExtractor,
            "copy_protected": CopyProtectedPDFExtractor,
        }
        return extractors.get(pdf_type, TextPDFExtractor)

    async def process_task(self, task_data: dict) -> None:
        """단일 PDF 처리 작업 수행"""
        try:
            task_id = task_data["task_id"]
            pdf_type = task_data.get("pdf_type", "text")
            extraction_schema = task_data.get("extraction_schema", {})

            # 작업 상태 업데이트
            await self.queue.update_task_status(task_id, TaskStatus.PROCESSING, pdf_type)

            # 추출기 및 처리기 초기화
            extractor_class = self._get_extractor_class(pdf_type)
            extractor = extractor_class(
                file_path=task_data["file_path"], password=task_data.get("password")
            )
            processor = LLMDataProcessor(api_key=self.openai_api_key)

            # 텍스트 추출
            text = extractor.extract_text()
            metadata = extractor.extract_metadata()

            # LLM 처리를 위한 데이터 준비
            processing_data = {"text": text, "extraction_schema": extraction_schema}

            # 텍스트 처리 및 구조화
            processed_data = processor.process(processing_data)
            processed_data["metadata"] = metadata

            # 결과 저장
            await self.queue.store_result(
                task_id=task_id,
                result=processed_data,
                ttl=task_data.get("result_ttl", 3600),
                pdf_type=pdf_type,
            )

        except Exception as e:
            print(f"Error processing task: {e}")
            await self.queue.update_task_status(task_id, TaskStatus.FAILED, pdf_type)

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
