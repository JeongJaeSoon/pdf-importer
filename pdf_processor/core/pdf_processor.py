import logging
import uuid
from typing import Any, Optional

from pdf_processor.core.queue_redis import RedisQueue
from pdf_processor.core.worker import PDFWorker
from pdf_processor.utils.constants import PDFProcessType

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF 처리를 위한 메인 클래스"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        redis_encryption_key: Optional[str] = None,
        model_name: str = "gpt-4",
        max_concurrent: int = 2,
    ):
        """PDF 처리기 초기화

        Args:
            redis_url: Redis 서버 URL (비동기 처리 시 필수)
            openai_api_key: OpenAI API 키 (필수)
            redis_encryption_key: Redis 암호화 키 (비동기 처리 시 필수)
            model_name: 사용할 OpenAI 모델 이름 (기본값: "gpt-4")
            max_concurrent: 최대 동시 실행 수 (기본값: 2)
        """
        self.pdf_analyzer = None
        self.processor = None
        self.redis_queue = None
        self.openai_api_key = openai_api_key
        self.worker = None

        if not openai_api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")

        # LLM 프로세서 초기화
        from pdf_processor.processors.llm_processor import LLMProcessor

        LLMProcessor.initialize(
            api_key=openai_api_key, model_name=model_name, max_concurrent=max_concurrent
        )

        # 비동기 처리를 위한 Redis 초기화
        if redis_url and redis_encryption_key:
            self.redis_queue = RedisQueue.initialize(redis_url, redis_encryption_key)
            self.worker = PDFWorker(self.redis_queue, openai_api_key)

    async def process_pdf(
        self,
        pdf_path: str,
        process_type: PDFProcessType,
        num_pages: int,
        async_processing: bool = False,
    ) -> Any:
        """PDF 처리 시작

        Args:
            pdf_path: PDF 파일 경로
            process_type: 처리 유형 (PDFProcessType)
            num_pages: 예상되는 인보이스 수
            async_processing: 비동기 처리 여부 (기본값: False)

        Returns:
            동기 처리: 처리 결과
            비동기 처리: 작업 ID
        """
        # 비동기 처리
        if async_processing:
            if not self.redis_queue or not self.worker:
                raise ValueError("비동기 처리를 위해서는 Redis 설정이 필요합니다.")

            # 작업 ID 생성
            task_id = f"task_{uuid.uuid4()}"

            # 작업 데이터 준비
            task_data = {
                "task_id": task_id,
                "pdf_path": pdf_path,
                "process_type": process_type,
                "num_pages": num_pages,
            }

            # 작업 큐에 추가
            await self.redis_queue.enqueue(task_data)
            return task_id

        # 동기 처리
        worker = PDFWorker(None, self.openai_api_key)
        task_data = {
            "task_id": f"task_{uuid.uuid4()}",
            "pdf_path": pdf_path,
            "process_type": process_type,
            "num_pages": num_pages,
        }
        await worker.process_task(task_data)
        return task_data["task_id"]

    async def get_task_status(self, task_id: str) -> Optional[str]:
        """작업 상태 조회"""
        if not self.redis_queue:
            raise ValueError("작업 상태 조회를 위해서는 Redis 설정이 필요합니다.")
        status = await self.redis_queue.get_task_status(task_id)
        return status.value if status else None

    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """작업 결과 조회"""
        if not self.redis_queue:
            raise ValueError("작업 결과 조회를 위해서는 Redis 설정이 필요합니다.")
        return await self.redis_queue.get_result(task_id)

    async def start_worker(self) -> None:
        """작업자 시작"""
        if not self.worker:
            raise ValueError("작업자 시작을 위해서는 Redis 설정이 필요합니다.")
        await self.worker.start()

    async def stop_worker(self) -> None:
        """작업자 중지"""
        if self.worker:
            await self.worker.stop()
