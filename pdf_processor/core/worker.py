import asyncio
import logging
from typing import Any, Dict, Type

from pdf_processor.core.llm import LLM
from pdf_processor.core.queue import BaseQueue, TaskStatus
from pdf_processor.processors.base import BaseProcessor
from pdf_processor.processors.invoice import Invoice
from pdf_processor.processors.pdf_analyzer import PDFAnalyzer
from pdf_processor.utils.constants import PDFProcessType

logger = logging.getLogger(__name__)


class Worker:
    """비동기 PDF 처리 작업자"""

    # 처리 타입별 프로세서 매핑
    PROCESSORS = {
        PDFProcessType.INVOICE: Invoice,
        # 다른 처리 타입들은 구현 후 여기에 추가
        # PDFProcessType.RESUME: ResumeProcessor,
        # PDFProcessType.CONTRACT: ContractProcessor,
        # PDFProcessType.RECEIPT: ReceiptProcessor,
    }

    def __init__(self, queue: BaseQueue):
        self.queue = queue
        self.running = False
        # LLM 초기화
        self.llm = LLM.get_instance()

    def _get_processor_class(self, process_type: str) -> Type[BaseProcessor]:
        """처리 타입에 맞는 프로세서 클래스 반환"""
        try:
            process_type_enum = PDFProcessType(process_type.lower())
            processor_class = self.PROCESSORS.get(process_type_enum)
            if not processor_class:
                available_types = ", ".join(PDFProcessType.values())
                raise ValueError(
                    f"지원하지 않는 처리 타입입니다: {process_type}. "
                    f"사용 가능한 타입: {available_types}"
                )
            return processor_class
        except ValueError:
            available_types = ", ".join(PDFProcessType.values())
            raise ValueError(f"유효하지 않은 처리 타입입니다. 사용 가능한 타입: {available_types}")

    async def process_task(self, task_data: Dict[str, Any]) -> None:
        """작업 처리"""
        task_id = task_data.get("task_id")
        if not task_id:
            logger.error("작업 ID가 없습니다.")
            return

        try:
            # 작업 상태를 처리 중으로 변경
            await self.queue.update_task_status(task_id, TaskStatus.PROCESSING)

            # 필수 필드 확인
            required_fields = ["pdf_path", "process_type", "num_pages"]
            for field in required_fields:
                if field not in task_data:
                    raise ValueError(f"필수 필드가 누락되었습니다: {field}")

            # PDF 분석 및 처리
            pdf_path = task_data["pdf_path"]
            process_type = task_data["process_type"]
            num_pages = task_data["num_pages"]
            metadata = task_data.get("metadata")  # 메타데이터 가져오기

            # PDF 분석기 초기화
            analyzer = PDFAnalyzer()
            page_ranges_with_reasons = await analyzer.execute(
                pdf_path=pdf_path, num_pages=num_pages, metadata=metadata  # 메타데이터 전달
            )

            # 처리 타입에 맞는 프로세서 초기화
            processor_class = self._get_processor_class(process_type)
            processor = processor_class()

            # 각 페이지 범위별로 처리
            results = []
            for start_page, end_page, reason in page_ranges_with_reasons:
                try:
                    # 기존 execute 메서드 호출 시 분석 근거와 메타데이터 함께 전달
                    result = await processor.execute(
                        pdf_path=pdf_path,
                        page_range=(start_page, end_page),
                        analysis_reason=reason,
                        metadata=metadata,  # 메타데이터 전달
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"페이지 범위 {(start_page+1, end_page+1)} 처리 중 오류 발생: {e}")
                    # 개별 페이지 범위 처리 실패는 기록하고 계속 진행
                    results.append(
                        {
                            "error": f"처리 실패: {str(e)}",
                            "page_range": (start_page + 1, end_page + 1),
                        }
                    )

            # 결과 저장
            await self.queue.store_result(task_id, results)

            # 최소한 하나의 결과가 있으면 성공으로 처리
            if any(not isinstance(r, dict) or "error" not in r for r in results):
                await self.queue.update_task_status(task_id, TaskStatus.COMPLETED)
            else:
                # 모든 페이지 범위가 실패한 경우
                await self.queue.update_task_status(task_id, TaskStatus.FAILED)
                error_message = "모든 페이지 범위 처리가 실패했습니다."
                await self.queue.store_result(task_id, {"error": error_message})

        except Exception as e:
            logger.error(f"작업 처리 중 오류 발생: {e}")
            await self.queue.update_task_status(task_id, TaskStatus.FAILED)
            await self.queue.store_result(task_id, {"error": str(e)})

    async def start(self, poll_interval: float = 1.0):
        """작업자 시작"""
        self.running = True
        logger.info("PDF 처리 작업자 시작")

        while self.running:
            try:
                # 큐에서 다음 작업 가져오기
                task_data = await self.queue.dequeue()
                if task_data:
                    logger.info(f"새로운 작업 수신: {task_data.get('task_id')}")
                    # 작업 처리
                    await self.process_task(task_data)
                else:
                    # 작업이 없으면 대기
                    await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f"작업자 오류: {str(e)}")
                await asyncio.sleep(poll_interval)

    async def stop(self):
        """작업자 중지"""
        logger.info("PDF 처리 작업자 중지")
        self.running = False
