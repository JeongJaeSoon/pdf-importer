import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from pdf_processor import PDFProcessor, PDFProcessType

# .env 파일 로드
load_dotenv()

# Rich 콘솔 초기화
console = Console()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def process_single_pdf(
    processor: PDFProcessor, pdf_path: Path, task_id: str
) -> Optional[Dict]:
    """단일 PDF 파일 처리

    Args:
        processor: PDF 처리기
        pdf_path: PDF 파일 경로
        task_id: 작업 ID

    Returns:
        처리 결과 또는 None (실패 시)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]{pdf_path.name} - 처리 중...[/]", total=None)
        status = None

        while True:
            status = await processor.get_task_status(task_id)
            progress.update(
                task,
                description=f"[bold blue]{pdf_path.name} - 현재 상태:[/] [yellow]{status}[/]",
            )

            if status == "completed":
                console.print()
                result = await processor.get_task_result(task_id)
                console.print(f"\n[bold green]{pdf_path.name} - 처리 결과:[/]")
                result_json = json.dumps(result, ensure_ascii=False, indent=2)
                console.print(Panel(JSON(result_json), title="추출된 데이터", border_style="green"))
                return result

            elif status == "failed":
                console.print()
                error_info = await processor.get_task_result(task_id)
                console.print(f"\n[bold red]{pdf_path.name} - 작업 실패[/]")
                if error_info:
                    console.print(
                        f"[red]에러 메시지:[/] {error_info.get('error', '알 수 없는 오류')}"
                    )
                return None

            await asyncio.sleep(1)


async def process_pdfs(processor: PDFProcessor, pdf_files: List[Path]) -> List[Dict]:
    """여러 PDF 파일 처리

    Args:
        processor: PDF 처리기
        pdf_files: PDF 파일 경로 리스트

    Returns:
        처리 결과 리스트
    """
    # 파일별 인보이스 수 매핑
    invoice_counts = {
        "sample_invoice_1.pdf": 1,
        "sample_invoice_2.pdf": 2,
        "sample_invoice_3.pdf": 3,
        "sample_invoice_4.pdf": 4,
    }

    # 작업 제출
    tasks = []
    for pdf_path in pdf_files:
        # 파일명에 따른 인보이스 수 결정
        num_invoices = invoice_counts.get(pdf_path.name, 1)
        task_id = await processor.process_pdf(
            pdf_path=str(pdf_path),
            process_type=PDFProcessType.INVOICE.value,
            num_pages=num_invoices,  # 파일별 인보이스 수 지정
            async_processing=True,
        )
        tasks.append((task_id, pdf_path))
        console.print(
            f"\n[bold green]작업이 제출되었습니다.[/] 파일: [yellow]{pdf_path.name}[/], "
            f"작업 ID: [yellow]{task_id}[/], 예상 인보이스 수: [yellow]{num_invoices}[/]"
        )

    # 모든 작업 완료 대기
    results = []
    for task_id, pdf_path in tasks:
        result = await process_single_pdf(processor, pdf_path, task_id)
        if result:
            results.append(result)
        console.print("\n" + "=" * 80 + "\n")

    return results


async def main():
    """비동기 처리 예제"""
    # 환경 변수 확인
    redis_url = os.getenv("REDIS_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    redis_encryption_key = os.getenv("REDIS_ENCRYPTION_KEY")
    max_concurrent = int(os.getenv("MAX_CONCURRENT", "2"))  # 최대 동시 실행 수 (기본값: 2)
    model_name = os.getenv("MODEL_NAME", "gpt-4")  # 사용할 모델 이름 (기본값: gpt-4)

    if not redis_url or not openai_api_key or not redis_encryption_key:
        raise ValueError("REDIS_URL, OPENAI_API_KEY, REDIS_ENCRYPTION_KEY 환경 변수가 필요합니다.")

    # PDF 파일 경로들
    samples_dir = Path(__file__).parent.parent / "samples" / "text"
    pdf_files = sorted(samples_dir.glob("sample_invoice_*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {samples_dir}")

    # 작업 정보 표시
    info_text = [
        "[bold cyan]PDF 처리 시작 (비동기 처리)[/]",
        f"처리할 파일: [yellow]{', '.join(f.name for f in pdf_files)}[/]",
        f"처리 타입: [blue]{PDFProcessType.INVOICE.value}[/]",
        f"최대 동시 실행 수: [blue]{max_concurrent}[/]",
        f"사용 모델: [blue]{model_name}[/]",
    ]
    console.print(Panel("\n".join(info_text), title="작업 정보", border_style="blue"))

    # PDF 처리기 초기화 (LLM 프로세서도 함께 초기화됨)
    processor = PDFProcessor(
        redis_url=redis_url,
        openai_api_key=openai_api_key,
        redis_encryption_key=redis_encryption_key,
        model_name=model_name,
        max_concurrent=max_concurrent,
    )

    worker_task = None
    try:
        # 작업자 시작
        worker_task = asyncio.create_task(processor.start_worker())

        # PDF 파일들 처리
        await process_pdfs(processor, pdf_files)

    except Exception as e:
        console.print(f"\n[bold red]에러 발생:[/] {str(e)}")
        logger.error(f"Error processing PDFs: {e}")
        raise

    finally:
        # 작업자 중지
        if worker_task:
            await processor.stop_worker()
            await worker_task


if __name__ == "__main__":
    asyncio.run(main())
