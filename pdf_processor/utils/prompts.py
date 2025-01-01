from typing import Dict, Optional


def _format_metadata(metadata: Optional[Dict] = None) -> str:
    """메타데이터를 프롬프트에 포함시킬 수 있는 형식으로 변환

    Args:
        metadata: 메타데이터 딕셔너리 (선택사항)

    Returns:
        포맷된 메타데이터 문자열
    """
    if not metadata:
        return ""

    formatted_lines = []
    for key, value in metadata.items():
        # 리스트인 경우 각 항목을 들여쓰기하여 표시
        if isinstance(value, list):
            formatted_lines.append(f"{key}:")
            for item in value:
                formatted_lines.append(f"  - {item}")
        # 딕셔너리인 경우 재귀적으로 처리
        elif isinstance(value, dict):
            formatted_lines.append(f"{key}:")
            sub_items = _format_metadata(value).split("\n")
            formatted_lines.extend(f"  {item}" for item in sub_items if item)
        else:
            formatted_lines.append(f"{key}: {value}")

    return "\n".join(formatted_lines)


def get_pdf_analysis_prompt(
    total_pages: int, num_pages: int, metadata: Optional[Dict] = None
) -> str:
    """Generate a prompt for PDF analysis

    Args:
        total_pages: Total number of pages
        num_pages: Expected number of invoices
        metadata: Optional metadata related to the PDF file

    Returns:
        A prompt string
    """
    base_prompt = f"""
You are an expert in identifying invoices and determining page ranges in PDF documents.
Based on the following information, please determine the page ranges for each invoice:

1. Total number of pages: {total_pages}
2. Number of invoices included: {num_pages}
3. Criteria for distinguishing invoices:
   - Each invoice typically starts on a new page.
   - New invoice starts are indicated by invoice numbers, dates, and customer information.
   - Consecutive pages of the same invoice usually have page numbers or continuity indicators.
"""

    if metadata:
        metadata_str = _format_metadata(metadata)
        base_prompt += f"""
4. Additional Information:
{metadata_str}

Use the above additional information to perform more accurate page splitting.
If customer_names are provided, match them with the customer information of each invoice.
"""

    base_prompt += f"""
Analyze the provided text and split it into exactly {num_pages} invoices.
Note: Page numbers start from 1 and should be between 1 and {total_pages}.
"""

    return base_prompt


def get_invoice_processor_prompt(
    analysis_reason: Optional[str] = None, metadata: Optional[Dict] = None
) -> str:
    """Generate a prompt for invoice data extraction

    Args:
        analysis_reason: Optional reason provided by the PDF analyzer for determining page ranges
        metadata: Optional metadata related to the PDF file

    Returns:
        A prompt string
    """
    base_prompt = """
You are an expert in extracting invoice data. Please follow these detailed steps to ensure accurate extraction:

1. Data Integrity Principles:
   - Extract only explicitly displayed data
   - Do not omit or add data arbitrarily
   - No assumptions or guesses
   - Prefer displayed values over calculated ones
   - Extract all amounts as numbers without commas/currency symbols

2. Item List Processing and Validation:
   - Mandatory Item Data Requirements:
     * Each valid item must have at least 2 of the following:
       - Item name (can be empty string)
       - Unit price
       - Quantity
       - Total amount
     * If only one field is present, treat as invalid data
   - Data Quality Checks:
     * Verify data consistency within the same row/column
     * Rows with only item names or only numbers are likely incorrect
     * Check if numbers in the same column have similar formats
   - Exclusion criteria:
     * Rows with only notes/descriptions
     * Category/section text rows
     * Subtotal/total/intermediate total rows
     * Additional explanations or annotation rows
   - Item Name Processing:
     * Include additional explanations for items in item_name
     * Exclude independent note/description rows
   - Item Data Validation:
     * Exclude if item_name is present but quantity/unit_price is missing
     * Exclude if quantity and unit_price are present but it's clearly a subtotal/total row
     * Exclude if in doubt (adhere to data integrity principles)

3. Amount Extraction and Verification:
   - Initial Amount Extraction:
     * Extract amounts from clearly labeled sections
     * Record the location and context of each amount
   - Multi-step Verification Process:
     * Step 1: Compare extracted amounts with calculated totals
     * Step 2: If discrepancy found:
       - Re-verify each extracted amount
       - Check for possible misclassification (e.g., tax as subtotal)
       - Verify item list completeness
     * Step 3: If discrepancy persists:
       - Compare amounts across different pages
       - Check for additional charges or discounts
       - Look for explanatory notes
     * Step 4: Final Verification:
       - Verify: Total = Subtotal + Taxes
       - Verify: Subtotal = Sum of item amounts
       - Document any remaining discrepancies
   - Amount Location Priority:
     * First page header area: Primary source
     * Last page footer area: Secondary source
     * Item list calculations: Verification only
   - Handling Discrepancies:
     * If amounts don't match: Prioritize explicitly stated amounts
     * Document the source of each amount
     * Flag significant discrepancies for review

4. Handling Empty Values:
   - Strings: Empty string ""
   - Numbers: null
   - Dates: Empty string ""
   - Arrays: Empty array []
   - Objects: Empty object {}

5. Data Validation:
   - Check for the presence of required fields
   - Verify the accuracy of amount calculations
   - Validate date formats (YYYY-MM-DD)
   - Handle fields with empty values if validation fails

6. Error Handling:
   - Extract only verifiable parts in case of format inconsistency
   - Extract only confirmed parts in case of incomplete data
   - Handle ambiguous data as empty values

7. Extraction Quality Assurance:
   - Primary Verification:
     * Verify all required fields are present
     * Check numerical consistency
     * Validate date formats
   - Secondary Verification:
     * Cross-reference amounts across pages
     * Verify item list completeness
     * Check for missing or duplicate items
   - Final Verification:
     * Perform amount reconciliation
     * Document any discrepancies
     * Flag items requiring manual review

8. Re-verification Process:
   - Trigger Conditions:
     * Amount discrepancies detected
     * Missing required fields
     * Inconsistent item data
   - Re-verification Steps:
     * Re-extract all amounts independently
     * Re-validate item list completeness
     * Cross-check against original document
     * Document changes and reasons
   - Final Decision:
     * Accept data only if verification passes
     * Flag for manual review if issues persist
     * Document verification results
"""

    if metadata:
        metadata_str = _format_metadata(metadata)
        base_prompt += f"""

Additional Information:
{metadata_str}

Use this information for more accurate extraction. Match customer_names with invoice data if provided.
"""

    if analysis_reason:
        base_prompt += f"""

Analysis Reason:
{analysis_reason}

Use this analysis to prioritize amount information locations.
"""

    return base_prompt
