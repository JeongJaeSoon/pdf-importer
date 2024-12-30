import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from pdf_processor.core.queue_redis import RedisQueue
from pdf_processor.core.worker import PDFWorker

# 환경 변수 로드
load_dotenv()

# Rich 콘솔 초기화
console = Console()

# 필요한 환경 변수
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENCRYPTION_KEY = os.getenv("REDIS_ENCRYPTION_KEY")  # 32바이트 키 필요
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 샘플 디렉토리 경로
SAMPLES_DIR = Path(__file__).parent.parent / "samples"

# 데이터 추출 스키마 예시들
EXTRACTION_SCHEMAS = {
    # 영수증/청구서 스키마
    "invoice": {
        "invoice_number": "청구서 번호",
        "date": "발행일 (YYYY-MM-DD)",
        "vendor": {"name": "판매자/공급자명", "contact": "연락처 정보"},
        "customer": {"name": "구매자/수신자명", "contact": "연락처 정보"},
        "items": [
            {"description": "품목 설명", "quantity": "수량", "unit_price": "단가", "amount": "금액"}
        ],
        "total_amount": "총 금액",
        "payment_terms": "지불 조건",
    },
}


def check_file_exists(file_path: Path) -> bool:
    """파일 존재 여부 확인"""
    if not file_path.exists():
        console.print(f"[bold red]오류:[/] 파일을 찾을 수 없습니다: {file_path}")
        return False
    if not file_path.is_file():
        console.print(f"[bold red]오류:[/] 유효한 파일이 아닙니다: {file_path}")
        return False
    return True


async def process_single_pdf(
    file_path: str | Path,
    pdf_type: str = "text",
    password: str | None = None,
    extraction_schema: str | Dict[str, Any] = "invoice",
):
    """단일 PDF 파일 처리 예제"""
    file_path = Path(file_path)

    # 파일 존재 여부 확인
    if not check_file_exists(file_path):
        return

    # Rich 패널로 작업 정보 표시
    console.print(
        Panel(
            f"[bold cyan]PDF 처리 시작[/]\n"
            f"파일: [yellow]{file_path}[/]\n"
            f"유형: [green]{pdf_type}[/]\n"
            f"스키마: [magenta]"
            f"{extraction_schema if isinstance(extraction_schema, str) else 'custom'}[/]",
            title="작업 정보",
            border_style="blue",
        )
    )

    # Redis 큐 초기화
    queue = RedisQueue(redis_url=REDIS_URL, encryption_key=REDIS_ENCRYPTION_KEY)

    # 작업자 초기화
    worker = PDFWorker(queue=queue, openai_api_key=OPENAI_API_KEY)

    try:
        # 스키마 준비
        schema = (
            EXTRACTION_SCHEMAS[extraction_schema]
            if isinstance(extraction_schema, str)
            else extraction_schema
        )

        # 작업 등록
        task_id = await queue.enqueue(
            {
                "file_path": str(file_path),
                "pdf_type": pdf_type,
                "password": password,
                "result_ttl": 3600,
                "extraction_schema": schema,
            }
        )
        console.print(f"[bold green]작업이 등록되었습니다. 작업 ID:[/] [yellow]{task_id}[/]")

        # 작업자 시작 (백그라운드 태스크로)
        worker_task = asyncio.create_task(worker.start())

        # 작업 완료 대기 (프로그레스 바 추가)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("처리 중...", total=None)
            while True:
                status = await queue.get_task_status(task_id, pdf_type)
                progress.update(
                    task, description=f"[bold blue]현재 작업 상태:[/] [yellow]{status.value}[/]"
                )

                if status.value in ["completed", "failed"]:
                    break

                await asyncio.sleep(1)

        # 결과 조회
        if status.value == "completed":
            result = await queue.get_result(task_id, pdf_type)
            console.print("\n[bold green]처리 결과:[/]")
            # JSON 문자열로 변환 후 다시 파싱하여 출력
            result_json = json.dumps(result, ensure_ascii=False, indent=2)
            console.print(
                Panel(
                    JSON(result_json), title=f"[bold]PDF 유형: {pdf_type}[/]", border_style="green"
                )
            )
        else:
            console.print("\n[bold red]작업 실패[/]")

        # 작업자 중지
        await worker.stop()
        await worker_task

    except KeyError as e:
        console.print(f"[bold red]오류:[/] 지원하지 않는 스키마입니다: {e}")
        await worker.stop()
    except Exception as e:
        console.print(f"[bold red]에러 발생:[/] {str(e)}")
        await worker.stop()

    # 구분선 추가
    console.print("\n" + "=" * 80 + "\n")


async def main():
    """메인 함수"""
    # 환경 변수 체크
    if not REDIS_ENCRYPTION_KEY:
        console.print("[bold red]오류:[/] REDIS_ENCRYPTION_KEY가 설정되지 않았습니다.")
        return
    if not OPENAI_API_KEY:
        console.print("[bold red]오류:[/] OPENAI_API_KEY가 설정되지 않았습니다.")
        return

    console.print(
        Panel(
            "[bold yellow]PDF 처리 작업 시작[/]",
            border_style="yellow",
        )
    )

    # 샘플 디렉토리 체크
    if not SAMPLES_DIR.exists():
        console.print(f"[bold red]오류:[/] 샘플 디렉토리를 찾을 수 없습니다: {SAMPLES_DIR}")
        return

    # 일반 텍스트 PDF를 문서 형식으로 처리
    await process_single_pdf(
        file_path=SAMPLES_DIR / "text/sample.pdf", pdf_type="text", extraction_schema="invoice"
    )

    # 스캔된 PDF를 계약서 형식으로 처리
    await process_single_pdf(
        file_path=SAMPLES_DIR / "scanned/scanned.pdf",
        pdf_type="scanned",
        extraction_schema="invoice",
    )

    # 비밀번호 보호된 PDF를 영수증 형식으로 처리
    await process_single_pdf(
        file_path=SAMPLES_DIR / "protected/protected.pdf",
        pdf_type="password_protected",
        password="your-password",
        extraction_schema="invoice",
    )

    # 복사 방지된 PDF를 사용자 정의 스키마로 처리
    custom_schema = {
        "custom_field1": "설명1",
        "custom_field2": "설명2",
        "nested_data": {"field3": "설명3", "field4": "설명4"},
    }
    await process_single_pdf(
        file_path=SAMPLES_DIR / "copy_protected/nocopy.pdf",
        pdf_type="copy_protected",
        extraction_schema=custom_schema,
    )

    console.print(
        Panel(
            "[bold green]모든 PDF 처리 완료[/]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
