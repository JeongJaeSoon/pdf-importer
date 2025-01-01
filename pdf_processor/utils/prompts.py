"""PDF 처리를 위한 프롬프트 모음"""

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

2. Item List Processing:
   - Criteria for extracting item data:
     * Extract data only if item_name is present (empty string "" is also valid)
     * Process as an item only if both quantity and unit_price are present
     * Consider it not an item if either quantity or unit_price is missing
   - Exclusion criteria:
     * Rows with only notes/descriptions (no quantity/unit_price/amount)
     * Category/section text rows
     * Subtotal/total/intermediate total rows
     * Additional explanations or annotation rows
   - Item Name Processing:
     * Treat empty string "" as valid data for item_name
     * Include additional explanations for items in item_name
     * Exclude independent note/description rows
   - Item Data Validation:
     * Exclude if item_name is present but quantity/unit_price is missing
     * Exclude if quantity and unit_price are present but it's clearly a subtotal/total row
     * Exclude if in doubt (adhere to data integrity principles)

3. Amount Extraction Rules:
   - Priority for amount verification:
     * 1st priority: Explicit amounts at the top of the first page and bottom of the last page
     * 2nd priority: Calculated amounts from the item list
     * Always prioritize explicit amounts if there is a discrepancy
   - Amount Location:
     * First page: Search in the top or header area
     * Last page: Search in the bottom or footer area
   - Processing by Amount Type:
     * Subtotal:
       - Search keywords: "Subtotal", "Total before tax", etc.
       - Extract amounts distinct from tax/total amounts
     * Tax Amount:
       - Search keywords: "Tax", "VAT", etc.
       - Typically 10% of the subtotal, but always use the explicitly stated value
     * Total Amount:
       - Search keywords: "Total", "Grand Total", etc.
       - Verify if it matches the sum of subtotal and tax amounts
       - Prioritize the explicitly stated total amount if there is a discrepancy
   - Amount Verification:
     * Check for consistency if amounts are displayed multiple times
     * Prioritize the first page amount if inconsistent
     * Verify the relationship: Subtotal + Tax = Total
     * Use explicitly displayed amounts if there is a discrepancy
   - Negative Amount Handling:
     * Negative amounts are possible for returns/discounts/refunds
     * If the subtotal is negative, the tax amount should also be negative
     * Handle various negative notations like minus signs, parentheses, etc.

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

6. Amount Comparison and Verification:
   - Compare the total amount of extracted items with the subtotal, tax, and total amounts
   - If there is a discrepancy:
     * Re-execute data extraction and verification
     * Analyze the cause of the discrepancy and correct if possible
     * Report the cause of the discrepancy if correction is not possible
   - Verification Process:
     * Verify the relationship: Subtotal + Tax = Total
     * Check if the total amount of items matches the subtotal
     * Verify if the tax is 10% of the subtotal (prioritize the explicitly stated value)

7. Error Handling:
   - Extract only verifiable parts in case of format inconsistency
   - Extract only confirmed parts in case of incomplete data
   - Handle ambiguous data as empty values

8. Data Verification and Accuracy Improvement:
   - Compare the extracted data with the actual PDF data to verify accuracy
   - If discrepancies are found:
     * Re-evaluate the extraction process
     * Identify potential causes for discrepancies
     * Adjust extraction parameters or methods to improve accuracy
     * Document findings and adjustments made to enhance data accuracy

9. PDF Data Extraction Process:
   - Step 1: Verify the invoice amount (total amount, tax, and subtotal)
   - Step 2: Check the number of items
   - Step 3: Review detailed information for each item
   - Step 4: Conduct a preliminary verification based on the extracted information
   - Step 5: If the preliminary verification is successful, perform a secondary verification by comparing with the PDF file
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
