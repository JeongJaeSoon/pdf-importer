import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from pdf_processor.core.queue_redis import RedisQueue
from pdf_processor.core.worker import PDFWorker

# 환경 변수 로드
load_dotenv()

# 필요한 환경 변수
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENCRYPTION_KEY = os.getenv("REDIS_ENCRYPTION_KEY")  # 32바이트 키 필요
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 샘플 디렉토리 경로
SAMPLES_DIR = Path(__file__).parent / "samples"


async def process_single_pdf(
    file_path: str | Path, pdf_type: str = "text", password: str | None = None
):
    """단일 PDF 파일 처리 예제"""
    # Redis 큐 초기화
    queue = RedisQueue(redis_url=REDIS_URL, encryption_key=REDIS_ENCRYPTION_KEY)

    # 작업자 초기화
    worker = PDFWorker(queue=queue, openai_api_key=OPENAI_API_KEY)

    try:
        # 작업 등록
        task_id = await queue.enqueue(
            {
                "file_path": str(file_path),
                "pdf_type": pdf_type,
                "password": password,
                "result_ttl": 3600,
            }
        )
        print(f"작업이 등록되었습니다. 작업 ID: {task_id}")

        # 작업자 시작 (백그라운드 태스크로)
        worker_task = asyncio.create_task(worker.start())

        # 작업 완료 대기
        while True:
            status = await queue.get_task_status(task_id, pdf_type)
            print(f"현재 작업 상태: {status.value}")

            if status.value in ["completed", "failed"]:
                break

            await asyncio.sleep(1)

        # 결과 조회
        if status.value == "completed":
            result = await queue.get_result(task_id, pdf_type)
            print("\n처리 결과:")
            print(result)
        else:
            print("\n작업 실패")

        # 작업자 중지
        await worker.stop()
        await worker_task

    except Exception as e:
        print(f"에러 발생: {e}")
        await worker.stop()


async def main():
    """메인 함수"""
    # 일반 텍스트 PDF 처리
    await process_single_pdf(file_path=SAMPLES_DIR / "text/sample.pdf", pdf_type="text")

    # 스캔된 PDF 처리
    await process_single_pdf(file_path=SAMPLES_DIR / "scanned/scanned.pdf", pdf_type="scanned")

    # 비밀번호 보호된 PDF 처리
    await process_single_pdf(
        file_path=SAMPLES_DIR / "protected/protected.pdf",
        pdf_type="password_protected",
        password="your-password",
    )

    # 복사 방지된 PDF 처리
    await process_single_pdf(
        file_path=SAMPLES_DIR / "copy_protected/nocopy.pdf", pdf_type="copy_protected"
    )


if __name__ == "__main__":
    asyncio.run(main())
