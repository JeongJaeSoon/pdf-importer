import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List

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


async def process_single_pdf(processor: PDFProcessor, pdf_path: Path) -> Dict:
    """단일 PDF 파일 처리

    Args:
        processor: PDF 처리기
        pdf_path: PDF 파일 경로

    Returns:
        처리 결과
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # 진행 상태 표시를 위한 태스크 생성
        task1 = progress.add_task(f"[cyan]{pdf_path.name} - 1단계: PDF 분석 중...[/]", total=None)
        task2 = progress.add_task(
            f"[cyan]{pdf_path.name} - 2단계: 데이터 추출 중...[/]", visible=False
        )

        try:
            # PDF 처리 실행
            results = await processor.process_pdf(
                pdf_path=str(pdf_path),
                process_type=PDFProcessType.INVOICE.value,
                num_pages=1,  # 각 파일을 단일 인보이스로 처리
            )

            # 진행 상태 업데이트
            progress.update(
                task1,
                description=f"[green]{pdf_path.name} - 1단계: PDF 분석 완료[/]",
            )
            progress.update(
                task2,
                visible=True,
                description=f"[green]{pdf_path.name} - 2단계: 데이터 추출 완료[/]",
            )

            # 결과 출력
            console.print(f"\n[bold green]{pdf_path.name} - 처리 결과:[/]")
            result_json = json.dumps(results, ensure_ascii=False, indent=2)
            console.print(Panel(JSON(result_json), title="추출된 데이터", border_style="green"))

            return results

        except Exception as e:
            console.print(f"\n[bold red]{pdf_path.name} - 에러 발생:[/] {str(e)}")
            logger.error(f"Error processing PDF {pdf_path.name}: {e}")
            raise


async def process_pdfs(processor: PDFProcessor, pdf_files: List[Path]) -> List[Dict]:
    """여러 PDF 파일 처리

    Args:
        processor: PDF 처리기
        pdf_files: PDF 파일 경로 리스트

    Returns:
        처리 결과 리스트
    """
    results = []
    for pdf_path in pdf_files:
        try:
            result = await process_single_pdf(processor, pdf_path)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
        console.print("\n" + "=" * 80 + "\n")
    return results


async def main():
    """동기 처리 예제"""
    # 환경 변수 확인
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 필요합니다.")

    # PDF 파일 경로들
    samples_dir = Path(__file__).parent.parent / "samples" / "text"
    pdf_files = sorted(samples_dir.glob("sample_invoice_*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {samples_dir}")

    # 작업 정보 표시
    info_text = [
        "[bold cyan]PDF 처리 시작 (동기 처리)[/]",
        f"처리할 파일: [yellow]{', '.join(f.name for f in pdf_files)}[/]",
        f"처리 타입: [blue]{PDFProcessType.INVOICE.value}[/]",
    ]
    console.print(Panel("\n".join(info_text), title="작업 정보", border_style="blue"))

    try:
        # PDF 처리기 초기화
        processor = PDFProcessor(openai_api_key=openai_api_key)

        # PDF 파일들 처리
        await process_pdfs(processor, pdf_files)

    except Exception as e:
        console.print(f"\n[bold red]에러 발생:[/] {str(e)}")
        logger.error(f"Error processing PDFs: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
