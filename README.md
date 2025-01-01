# PDF Processor

An asynchronous processing package that extracts text from PDF files and converts it into structured data using LLM.

## Features

- Support for various PDF types:
  - Plain text PDFs
  - Scanned PDFs (OCR)
  - Password-protected PDFs
  - Copy-protected PDFs
- Support for synchronous/asynchronous task processing
- Task status management through Redis (asynchronous processing)
- Data security through AES-256 encryption
- Text structuring using LLM
- Automatic splitting and processing of multiple invoices
- Intelligent page range analysis
- Accurate data extraction through Function Calling

## Installation

1. Requires Python 3.13 or higher.

2. Install dependencies using Poetry:

    ```bash
    poetry install
    ```

3. Required system dependencies:

   - Redis server (for asynchronous processing)
   - Tesseract OCR (for processing scanned PDFs)
   - Poppler (for PDF image conversion)

## Basic Usage

### Synchronous Processing

```python
from pdf_processor import PDFProcessor, PDFProcessType

# Initialize processor
processor = PDFProcessor(
    openai_api_key="your-openai-api-key",
    model_name="gpt-4",  # Optional, default: gpt-4
    max_concurrent=2     # Optional, default: 2
)

# Process PDF (single or multiple invoices)
task_id = await processor.process_pdf(
    pdf_path="sample.pdf",
    process_type=PDFProcessType.INVOICE.value,
    num_pages=1,  # Number of invoices in the PDF
    async_processing=False
)
```

### Asynchronous Processing

```python
import asyncio
from pdf_processor import PDFProcessor, PDFProcessType

async def main():
    # Initialize processor
    processor = PDFProcessor(
        redis_url="redis://localhost:6379/0",
        openai_api_key="your-openai-api-key",
        redis_encryption_key="your-redis-encryption-key",
        model_name="gpt-4",  # Optional
        max_concurrent=2     # Optional
    )

    try:
        # Start worker
        worker_task = asyncio.create_task(processor.start_worker())

        # Submit task
        task_id = await processor.process_pdf(
            pdf_path="sample.pdf",
            process_type=PDFProcessType.INVOICE.value,
            num_pages=1,  # Number of invoices in the PDF
            async_processing=True
        )

        # Check task status
        while True:
            status = await processor.get_task_status(task_id)
            if status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

        # Get results
        if status == "completed":
            result = await processor.get_task_result(task_id)
            print(result)

    finally:
        # Stop worker
        await processor.stop_worker()
        await worker_task

if __name__ == "__main__":
    asyncio.run(main())
```

## Environment Variables

Required environment variables:

```bash
# OpenAI API Key (Required)
OPENAI_API_KEY=your-openai-api-key

# Redis Configuration (Required for async processing)
REDIS_URL=redis://localhost:6379/0
REDIS_ENCRYPTION_KEY=your-redis-encryption-key  # 32-byte encryption key

# LLM Configuration (Optional)
MAX_CONCURRENT=2  # Maximum concurrent executions (default: 2)
MODEL_NAME=gpt-4  # OpenAI model to use (default: gpt-4)

# Logging Configuration (Optional)
LOG_LEVEL=INFO

# OCR Configuration (Optional)
TESSERACT_CMD=/usr/local/bin/tesseract
TESSERACT_LANG=kor+eng
```

## Key Features Explained

### Page Number Handling

- Page numbers start from 1 in the user interface
- Internally processed with 0-based index, but all logs and outputs are displayed as 1-based

### Multiple Invoice Processing

- Can process PDFs containing multiple invoices
- LLM automatically analyzes page ranges for each invoice
- Falls back to equal distribution if analysis fails
- Requires accurate specification of invoice count

### Data Extraction and Validation

- Accurate data extraction through Function Calling
- Strict data validation and consistency checks
- Empty values for incomplete or uncertain data

### Error Handling

- Empty values for format mismatches or missing data
- Only affected fields set to empty values on validation failure
- Detailed error messages for task failures

## Examples and Testing

For detailed examples and testing methods, refer to [examples/README.md](examples/README.md).

## License

Apache 2.0 License
