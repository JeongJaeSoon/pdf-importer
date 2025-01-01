# PDF Processor 예제

이 디렉토리에는 PDF Processor 패키지의 사용 예제와 테스트를 위한 디렉토리 구조가 포함되어 있습니다.

## 디렉토리 구조

```directory
examples/
├── pyproject.toml         # 예제 프로그램의 의존성 정의
├── poetry.lock           # 예제 프로그램의 의존성 잠금 파일
├── README.md            # 예제 사용 설명서
├── .env.example         # 환경 변수 템플릿
├── src/                 # 예제 소스 코드
│   ├── __init__.py
│   ├── process_sync.py  # 동기 처리 예제
│   └── process_async.py # 비동기 처리 예제
└── samples/            # 테스트용 PDF 파일 디렉토리 (비어있음)
    ├── text/           # 일반 텍스트 PDF용
    ├── scanned/       # 스캔된 PDF용
    ├── protected/     # 비밀번호 보호된 PDF용
    └── copy_protected/ # 복사 방지된 PDF용
```

## 예제 실행 준비

1. 예제 디렉토리로 이동:

    ```bash
    cd examples
    ```

2. Poetry 환경 설정:

    ```bash
    # 가상 환경을 프로젝트 디렉토리 안에 생성
    poetry config virtualenvs.in-project true

    # 의존성 설치
    poetry install
    ```

3. 환경 변수 설정:

    ```bash
    cp .env.example .env
    # .env 파일을 편집하여 필요한 값들을 설정
    ```

4. Redis 서버 실행 (비동기 처리 시 필요):

    ```bash
    # 로컬 Redis 서버
    redis-server

    # 또는 Docker 사용
    docker run --name pdf-redis -p 6379:6379 -d redis
    ```

5. Redis 암호화 키 생성 (비동기 처리 시 필요):

    ```bash
    # 32바이트 암호화 키 생성
    poetry run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ```

## 테스트용 PDF 준비

테스트를 위해서는 다음과 같이 PDF 파일을 준비해야 합니다:

1. `samples/text/` 디렉토리에 테스트용 PDF 파일을 위치시킵니다.
2. 단일 또는 다중 인보이스를 포함한 PDF 파일: `sample_invoice_*.pdf`

예시:

- `sample_invoice_1.pdf`: 단일 인보이스 문서 (1개)
- `sample_invoice_2.pdf`: 2개의 인보이스가 포함된 문서
- `sample_invoice_3.pdf`: 3개의 인보이스가 포함된 문서
- `sample_invoice_4.pdf`: 4개의 인보이스가 포함된 문서

## 예제 실행

1. 동기 처리 예제:

    ```bash
    # Poetry 사용
    poetry run python src/process_sync.py

    # 또는 Poetry 쉘에서
    poetry shell
    python src/process_sync.py
    ```

2. 비동기 처리 예제 (Redis 필요):

    ```bash
    # Poetry 사용
    poetry run python src/process_async.py

    # 또는 Poetry 쉘에서
    poetry shell
    python src/process_async.py
    ```

## 테스트 실행

```bash
# 전체 테스트 실행
poetry run pytest

# 특정 테스트 실행
poetry run pytest tests/test_pdf_processor.py
```

## 디버깅

로그 레벨 변경:

```bash
# .env 파일에서 설정
LOG_LEVEL=DEBUG

# 또는 환경 변수로 설정
export LOG_LEVEL=DEBUG
```

## 주의사항

1. 실제 중요한 문서는 테스트용 샘플 디렉토리에 저장하지 마세요.
2. 비밀번호가 있는 PDF의 경우, 비밀번호를 반드시 기록해두세요.
3. OCR 처리를 위해서는 Tesseract가 설치되어 있어야 합니다.
4. 비동기 처리를 위해서는 Redis 서버가 실행 중이어야 합니다.
5. Redis 암호화 키는 안전하게 보관하고, 프로덕션 환경에서는 환경 변수나 시크릿 관리 시스템을 통해 관리하세요.
6. 다중 인보이스 처리 시에는 PDF에 포함된 실제 인보이스 수를 정확히 지정해야 합니다.
