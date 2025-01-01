# PDF Processor

PDF 파일에서 텍스트를 추출하고 LLM을 사용하여 구조화된 데이터로 변환하는 비동기 처리 패키지

## 기능

- 다양한 PDF 유형 지원:
  - 일반 텍스트 PDF
  - 스캔된 PDF (OCR)
  - 비밀번호 보호된 PDF
  - 복사 방지 기능이 설정된 PDF
- 동기/비동기 작업 처리 지원
- Redis를 통한 작업 상태 관리 (비동기 처리)
- AES-256 암호화를 통한 데이터 보안
- LLM을 활용한 텍스트 구조화
- 다중 인보이스 자동 분할 및 처리
- 지능형 페이지 범위 분석
- Function Calling을 통한 정확한 데이터 추출

## 설치

1. Python 3.13 이상이 필요합니다.

2. Poetry를 사용하여 의존성 설치:

    ```bash
    poetry install
    ```

3. 필요한 시스템 의존성:

   - Redis 서버 (비동기 처리용)
   - Tesseract OCR (스캔된 PDF 처리용)
   - Poppler (PDF 이미지 변환용)

## 기본 사용법

### 동기 처리

```python
from pdf_processor import PDFProcessor, PDFProcessType

# 처리기 초기화
processor = PDFProcessor(
    openai_api_key="your-openai-api-key",
    model_name="gpt-4",  # 선택사항, 기본값: gpt-4
    max_concurrent=2     # 선택사항, 기본값: 2
)

# PDF 처리 (단일 또는 다중 인보이스)
task_id = await processor.process_pdf(
    pdf_path="sample.pdf",
    process_type=PDFProcessType.INVOICE.value,
    num_pages=1,  # PDF에 포함된 인보이스 수
    async_processing=False
)
```

### 비동기 처리

```python
import asyncio
from pdf_processor import PDFProcessor, PDFProcessType

async def main():
    # 처리기 초기화
    processor = PDFProcessor(
        redis_url="redis://localhost:6379/0",
        openai_api_key="your-openai-api-key",
        redis_encryption_key="your-redis-encryption-key",
        model_name="gpt-4",  # 선택사항
        max_concurrent=2     # 선택사항
    )

    try:
        # 작업자 시작
        worker_task = asyncio.create_task(processor.start_worker())

        # 작업 제출
        task_id = await processor.process_pdf(
            pdf_path="sample.pdf",
            process_type=PDFProcessType.INVOICE.value,
            num_pages=1,  # PDF에 포함된 인보이스 수
            async_processing=True
        )

        # 작업 상태 확인
        while True:
            status = await processor.get_task_status(task_id)
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        # 결과 조회
        if status == "completed":
            result = await processor.get_task_result(task_id)
            print(result)

    finally:
        # 작업자 중지
        await processor.stop_worker()
        await worker_task

if __name__ == "__main__":
    asyncio.run(main())
```

## 환경 변수

필요한 환경 변수:

```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=your-openai-api-key

# Redis 설정 (비동기 처리 시 필수)
REDIS_URL=redis://localhost:6379/0
REDIS_ENCRYPTION_KEY=your-redis-encryption-key  # 32바이트 암호화 키

# LLM 설정 (선택)
MAX_CONCURRENT=2  # 최대 동시 실행 수 (기본값: 2)
MODEL_NAME=gpt-4  # 사용할 OpenAI 모델 (기본값: gpt-4)

# 로깅 설정 (선택)
LOG_LEVEL=INFO

# OCR 설정 (선택)
TESSERACT_CMD=/usr/local/bin/tesseract
TESSERACT_LANG=kor+eng
```

## 주요 기능 설명

### 페이지 번호 처리

- 사용자 인터페이스에서는 페이지 번호가 1부터 시작합니다.
- 내부적으로는 0-based 인덱스로 처리되지만, 모든 로그와 출력은 1-based로 표시됩니다.

### 다중 인보이스 처리

- 하나의 PDF 파일에 여러 개의 인보이스가 포함된 경우 처리 가능
- LLM이 자동으로 각 인보이스의 페이지 범위를 분석
- 분석 실패 시 균등 분할 방식으로 폴백
- 인보이스 수를 정확히 지정해야 함

### 데이터 추출 및 검증

- Function Calling을 통한 정확한 데이터 추출
- 엄격한 데이터 검증 및 정합성 확인
- 불완전하거나 불확실한 데이터는 빈 값으로 처리

### 오류 처리

- 형식 불일치나 누락된 데이터는 빈 값으로 처리
- 검증 실패 시 해당 필드만 빈 값으로 설정
- 작업 실패 시 상세한 오류 메시지 제공

## 예제 및 테스트

자세한 예제와 테스트 방법은 [examples/README.md](examples/README.md)를 참조하세요.

## 라이선스

Apache 2.0 License
