# PDF Processor Examples

This directory contains example usage and test directory structure for the PDF Processor package.

## Directory Structure

```directory
examples/
├── pyproject.toml         # Example program dependencies
├── poetry.lock           # Example program dependency lock file
├── README.md            # Example usage guide
├── .env.example         # Environment variable template
├── src/                 # Example source code
│   ├── __init__.py
│   ├── process_sync.py  # Synchronous processing example
│   └── process_async.py # Asynchronous processing example
└── samples/            # Test PDF file directory (empty)
    ├── text/           # For plain text PDFs
    ├── scanned/       # For scanned PDFs
    ├── protected/     # For password-protected PDFs
    └── copy_protected/ # For copy-protected PDFs
```

## Preparation for Running Examples

1. Navigate to the examples directory:

    ```bash
    cd examples
    ```

2. Configure Poetry environment:

    ```bash
    # Create virtual environment in project directory
    poetry config virtualenvs.in-project true

    # Install dependencies
    poetry install
    ```

3. Set environment variables:

    ```bash
    cp .env.example .env
    # Edit .env file to set required values
    ```

4. Start Redis server (required for async processing):

    ```bash
    # Local Redis server
    redis-server

    # Or using Docker
    docker run --name pdf-redis -p 6379:6379 -d redis
    ```

5. Generate Redis encryption key (required for async processing):

    ```bash
    # Generate 32-byte encryption key
    poetry run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ```

## Preparing Test PDFs

To prepare for testing, you need to set up PDF files as follows:

1. Place test PDF files in the `samples/text/` directory.
2. Single or multiple invoice PDFs: `sample_invoice_*.pdf`

Examples:

- `sample_invoice_1.pdf`: Single invoice document (1)
- `sample_invoice_2.pdf`: Document containing 2 invoices
- `sample_invoice_3.pdf`: Document containing 3 invoices
- `sample_invoice_4.pdf`: Document containing 4 invoices

## Running Examples

1. Synchronous processing example:

    ```bash
    # Using Poetry
    poetry run python src/process_sync.py

    # Or in Poetry shell
    poetry shell
    python src/process_sync.py
    ```

2. Asynchronous processing example (requires Redis):

    ```bash
    # Using Poetry
    poetry run python src/process_async.py

    # Or in Poetry shell
    poetry shell
    python src/process_async.py
    ```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_pdf_processor.py
```

## Debugging

Change log level:

```bash
# Set in .env file
LOG_LEVEL=DEBUG

# Or set as environment variable
export LOG_LEVEL=DEBUG
```

## Important Notes

1. Do not store actual important documents in the test sample directory.
2. For password-protected PDFs, make sure to record the passwords.
3. Tesseract must be installed for OCR processing.
4. Redis server must be running for asynchronous processing.
5. Store Redis encryption keys securely and manage them through environment variables or secret management systems in production.
6. When processing multiple invoices, specify the exact number of invoices contained in the PDF.
