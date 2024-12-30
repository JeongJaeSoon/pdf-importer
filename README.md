# PDF Processor

PDF 파일에서 텍스트를 추출하고 LLM을 사용하여 구조화된 데이터로 변환하는 비동기 처리 패키지

## 기능

- 다양한 PDF 유형 지원:
  - 일반 텍스트 PDF
  - 스캔된 PDF (OCR)
  - 비밀번호 보호된 PDF
  - 복사 방지 기능이 설정된 PDF
- 비동기 작업 처리 및 큐 관리
- Redis를 통한 작업 상태 관리
- AES-256 암호화를 통한 데이터 보안
- LLM을 활용한 텍스트 구조화

## 설치

1. Python 3.13 이상이 필요합니다.

2. Poetry를 사용하여 의존성 설치:

    ```bash
    poetry install
    ```

3. 필요한 시스템 의존성:

   - Redis 서버
   - Tesseract OCR (스캔된 PDF 처리용)
   - Poppler (PDF 이미지 변환용)

## 예제 및 샘플

프로젝트는 다음과 같은 구조로 예제와 샘플 PDF 파일들을 관리합니다:

```text
examples/
├── .env.example         # 환경 변수 템플릿
├── process_pdf.py       # 예제 스크립트
└── samples/            # 샘플 PDF 파일들
    ├── text/           # 일반 텍스트 PDF
    ├── scanned/       # 스캔된 PDF
    ├── protected/     # 비밀번호 보호된 PDF
    └── copy_protected/ # 복사 방지된 PDF
```

자세한 사용 방법은 [examples/README.md](examples/README.md)를 참조하세요.

## 빠른 시작

1. 환경 설정:

    ```bash
    cd examples
    cp .env.example .env
    # .env 파일을 편집하여 필요한 값들을 설정
    ```

2. Redis 서버 실행:

    ```bash
    # 로컬 Redis 서버
    redis-server

    # 또는 Docker 사용
    docker run --name pdf-redis -p 6379:6379 -d redis
    ```

3. 예제 실행:

    ```bash
    # examples 디렉토리에서
    poetry run python process_pdf.py
    ```

## 코드에서 사용하기

```python
import asyncio
from pdf_processor.core.queue_redis import RedisQueue
from pdf_processor.core.worker import PDFWorker

async def main():
    # Redis 큐 초기화
    queue = RedisQueue(
        redis_url="redis://localhost:6379/0",
        encryption_key="your-encryption-key"
    )

    # 작업자 초기화
    worker = PDFWorker(
        queue=queue,
        openai_api_key="your-openai-api-key"
    )

    # 작업 등록
    task_id = await queue.enqueue({
        "file_path": "sample.pdf",
        "pdf_type": "text",  # text, scanned, password_protected, copy_protected
        "password": "optional-password",
        "result_ttl": 3600
    })

    # 작업자 시작
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## 테스트

테스트 실행:

```bash
poetry run pytest
```

## 디버깅

로그 레벨 설정:

```bash
export LOG_LEVEL=DEBUG
```

## 라이선스

Apache 2.0 License
