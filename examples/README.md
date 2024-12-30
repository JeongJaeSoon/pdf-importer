# PDF Processor 예제

이 디렉토리에는 PDF Processor 패키지의 사용 예제와 테스트용 샘플 파일들이 포함되어 있습니다.

## 디렉토리 구조

```
examples/
├── .env.example         # 환경 변수 템플릿
├── process_pdf.py       # 예제 스크립트
└── samples/            # 샘플 PDF 파일들
    ├── text/           # 일반 텍스트 PDF
    ├── scanned/       # 스캔된 PDF
    ├── protected/     # 비밀번호 보호된 PDF
    └── copy_protected/ # 복사 방지된 PDF
```

## 실행 방법

1. 환경 설정:
```bash
# examples 디렉토리로 이동
cd examples

# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 편집
# - REDIS_ENCRYPTION_KEY: 32바이트 키 생성 및 설정
# - OPENAI_API_KEY: OpenAI API 키 설정
# - 필요한 경우 다른 설정들도 수정
```

2. Redis 서버 실행 (다음 중 하나 선택):
```bash
# 로컬 Redis 서버
redis-server

# 또는 Docker 사용
docker run --name pdf-redis -p 6379:6379 -d redis
```

3. 샘플 PDF 준비:
```bash
# 테스트하려는 PDF 파일을 해당 유형의 디렉토리에 복사
cp your-text.pdf samples/text/sample.pdf
cp your-scan.pdf samples/scanned/scanned.pdf
cp your-protected.pdf samples/protected/protected.pdf
cp your-nocopy.pdf samples/copy_protected/nocopy.pdf
```

4. 예제 실행:
```bash
# Poetry 환경에서 실행
poetry run python process_pdf.py

# 또는 가상환경이 활성화된 상태에서
python process_pdf.py
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
