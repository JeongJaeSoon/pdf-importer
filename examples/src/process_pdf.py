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
        "invoices": [
            {
                "page_range": "해당 인보이스의 페이지 범위 (예: '1-3' 또는 '4')",
                "invoice_number": "청구서 번호",
                "title": "인보이스 제목 또는 건명",
                "issue_date": "발행일 (YYYY-MM-DD)",
                "due_date": "지급기한 (YYYY-MM-DD)",
                "vendor": {
                    "name": "판매자/공급자명",
                    "business_number": "사업자등록번호",
                    "representative": "대표자명",
                    "address": "주소",
                    "contact": {"phone": "전화번호", "fax": "팩스번호", "email": "이메일"},
                },
                "customer": {
                    "name": "구매자/수신자명",
                    "business_number": "사업자등록번호",
                    "representative": "대표자명",
                    "address": "주소",
                    "contact": {"phone": "전화번호", "fax": "팩스번호", "email": "이메일"},
                },
                "items": [
                    {
                        "description": "품목 설명",
                        "quantity": "수량",
                        "unit": "단위",
                        "unit_price": "단가",
                        "amount": "공급가액",
                        "tax_rate": "세율",
                        "tax_amount": "세액",
                        "total_amount": "합계금액",
                        "remarks": "비고",
                    }
                ],
                "summary": {
                    "subtotal": "공급가액 합계",
                    "taxes": [
                        {
                            "type": "세금 유형 (예: 부가가치세, 소득세 등)",
                            "rate": "세율",
                            "amount": "세액",
                        }
                    ],
                    "total_tax_amount": "총 세액",
                    "total_amount": "총 합계금액",
                    "amount_in_words": "금액을 한글로 표시",
                },
                "payment": {
                    "terms": "지불 조건",
                    "method": "지불 방법",
                    "bank_info": {
                        "bank_name": "은행명",
                        "account_number": "계좌번호",
                        "account_holder": "예금주",
                    },
                },
                "additional_info": {
                    "remarks": "특이사항이나 비고",
                    "terms_and_conditions": "계약조건이나 약관",
                    "custom_fields": [{"label": "추가 필드의 이름", "value": "추가 필드의 값"}],
                },
            }
        ],
        "total_pages": "PDF의 총 페이지 수",
        "invoice_count": "감지된 총 인보이스 수",
    }
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
    page_ranges: (
        list[str] | None
    ) = None,  # 예: ["1-3", "4", "5", "6-7"] -> 각 요소는 하나의 인보이스에 해당하는 페이지 범위
    invoice_count: int | None = None,  # 문서에 포함된 총 인보이스 수 (자동 감지하려면 None)
):
    """단일 PDF 파일 처리 예제

    Args:
        file_path: PDF 파일 경로
        pdf_type: PDF 유형 (text, scanned, password_protected, copy_protected)
        password: PDF 비밀번호 (필요한 경우)
        extraction_schema: 데이터 추출 스키마
        page_ranges: 각 인보이스의 페이지 범위 리스트.
                    예: ["1-3", "4", "5", "6-7"]는 4개의 인보이스를 의미하며,
                    첫 번째 인보이스는 1-3페이지, 두 번째는 4페이지,
                    세 번째는 5페이지, 네 번째는 6-7페이지에 있음을 나타냄.
                    None인 경우 자동으로 인보이스 경계를 감지함.
        invoice_count: 문서에 포함된 총 인보이스 수.
                      page_ranges가 지정되지 않은 경우에만 사용됨.
                      None인 경우 자동으로 인보이스 수를 감지함.
    """
    file_path = Path(file_path)

    # 파일 존재 여부 확인
    if not check_file_exists(file_path):
        return

    # page_ranges와 invoice_count가 동시에 지정된 경우 경고
    if page_ranges and invoice_count:
        console.print("[bold yellow]경고:[/] page_ranges가 지정된 경우 invoice_count는 무시됩니다.")

    # Rich 패널로 작업 정보 표시
    info_text = [
        "[bold cyan]PDF 처리 시작[/]",
        f"파일: [yellow]{file_path}[/]",
        f"유형: [green]{pdf_type}[/]",
        f"스키마: [magenta]{extraction_schema if isinstance(extraction_schema, str) else 'custom'}[/]",
    ]

    if page_ranges:
        info_text.append(f"페이지 범위: [blue]{page_ranges}[/]")
    elif invoice_count:
        info_text.append(f"예상 인보이스 수: [blue]{invoice_count}[/]")
    else:
        info_text.append("인보이스 경계: [blue]자동 감지[/]")

    console.print(Panel("\n".join(info_text), title="작업 정보", border_style="blue"))

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
                "page_ranges": page_ranges,
                "invoice_count": invoice_count if not page_ranges else None,
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

            # 인보이스 수 표시
            if "invoices" in result:
                console.print(f"\n[bold cyan]감지된 인보이스 수:[/] {len(result['invoices'])}")

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

    console.print("\n[bold cyan]1. 완전 자동 감지 모드로 처리[/]")
    await process_single_pdf(
        file_path=SAMPLES_DIR / "text/sample.pdf",
        pdf_type="text",
        extraction_schema="invoice",
    )

    console.print("\n[bold cyan]2. 인보이스 수만 지정하여 처리[/]")
    await process_single_pdf(
        file_path=SAMPLES_DIR / "text/sample_2.pdf",
        pdf_type="text",
        extraction_schema="invoice",
    )

    # 3. 페이지 범위를 직접 지정하여 처리
    console.print("\n[bold cyan]3. 페이지 범위를 직접 지정하여 처리[/]")
    await process_single_pdf(
        file_path=SAMPLES_DIR / "text/sample_3.pdf",
        pdf_type="text",
        extraction_schema="invoice",
        invoice_count=3,
        page_ranges=["1-2", "3", "4-5"],
    )

    # 4. 단일 인보이스 처리 (인보이스 수 지정)
    console.print("\n[bold cyan]4. 단일 인보이스 처리 (인보이스 수 지정)[/]")
    await process_single_pdf(
        file_path=SAMPLES_DIR / "text/sample_4.pdf",
        pdf_type="text",
        extraction_schema="invoice",
    )

    console.print(
        Panel(
            "[bold green]모든 PDF 처리 완료[/]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
