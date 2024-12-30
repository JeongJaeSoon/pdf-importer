# PDF Processor 예제

이 디렉토리에는 PDF Processor 패키지의 사용 예제와 테스트용 샘플 파일들이 포함되어 있습니다.

## 디렉토리 구조

```directory
examples/
├── pyproject.toml         # 예제 프로그램의 의존성 정의
├── poetry.lock           # 예제 프로그램의 의존성 잠금 파일
├── README.md            # 예제 사용 설명서
├── .env.example         # 환경 변수 템플릿
├── src/                 # 예제 소스 코드
│   ├── __init__.py
│   └── process_pdf.py   # PDF 처리 예제
└── samples/            # 샘플 PDF 파일들
    ├── text/           # 일반 텍스트 PDF
    ├── scanned/       # 스캔된 PDF
    ├── protected/     # 비밀번호 보호된 PDF
    └── copy_protected/ # 복사 방지된 PDF
```

## 설치 방법

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

## 실행 방법

1. Redis 서버 실행 (다음 중 하나 선택):

    ```bash
    # 로컬 Redis 서버
    redis-server

    # 또는 Docker 사용
    docker run --name pdf-redis -p 6379:6379 -d redis
    ```

2. 샘플 PDF 준비:

    ```bash
    # 테스트하려는 PDF 파일을 해당 유형의 디렉토리에 복사
    cp your-text.pdf samples/text/sample.pdf
    cp your-scan.pdf samples/scanned/scanned.pdf
    cp your-protected.pdf samples/protected/protected.pdf
    cp your-nocopy.pdf samples/copy_protected/nocopy.pdf
    ```

3. 예제 실행:

    ```bash
    # Poetry 환경에서 실행
    poetry run python -m src.process_pdf

    # 또는 가상환경이 활성화된 상태에서
    python -m src.process_pdf
    ```

## 암호화 키 생성

Redis 암호화에 사용할 32바이트 키 생성:

```bash
poetry run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
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
