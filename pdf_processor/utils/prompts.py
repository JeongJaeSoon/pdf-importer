from typing import Dict, Optional


def _format_metadata(metadata: Optional[Dict] = None) -> str:
    """Convert metadata to a format that can be included in prompts

    Args:
        metadata: Metadata dictionary (optional)

    Returns:
        Formatted metadata string
    """
    if not metadata:
        return ""

    formatted_lines = []
    for key, value in metadata.items():
        if isinstance(value, list):
            formatted_lines.append(f"{key}:")
            for item in value:
                formatted_lines.append(f"  - {item}")
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
   - DO NOT translate or modify any text content - analyze it as is.
"""

    if metadata:
        metadata_str = _format_metadata(metadata)
        base_prompt += f"""
4. Additional Information:
{metadata_str}

Use the above additional information to perform more accurate page splitting.
If customer_names are provided, match them with the customer information of each invoice.
Remember to match the exact text as it appears in the document, without translation.
"""

    base_prompt += f"""
Analyze the provided text and split it into exactly {num_pages} invoices.
Note: Page numbers start from 1 and should be between 1 and {total_pages}.
Important: Do not translate or modify any text content during analysis.
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
   - Keep all text in its original language - DO NOT translate
   - Remove honorifics such as '御中' or '様' from customer names provided in metadata
   - Identify the original language of the data and ensure it is not changed to another language.

2. Item List Processing and Validation:
   - Each valid item must have at least 2 of the following:
     * Item name (can be empty string, but must be in original language)
     * Unit price
     * Quantity
     * Total amount
   - Verify data consistency within the same row/column
   - Exclude rows with only notes/descriptions, category/section text, or subtotal/total rows
   - Include additional explanations for items in item_name
   - Exclude independent note/description rows
   - Exclude if item_name is present but quantity/unit_price is missing
   - Exclude if quantity and unit_price are present but it's clearly a subtotal/total row

3. Amount Extraction and Verification:
   - Extract amounts from clearly labeled sections
   - Record the location and context of each amount
   - Compare extracted amounts with calculated totals
   - Re-verify each extracted amount if discrepancies are found
   - Prioritize explicitly stated amounts
   - Document the source of each amount

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

6. Error Handling:
   - Extract only verifiable parts in case of format inconsistency
   - Handle ambiguous data as empty values

7. Extraction Quality Assurance:
   - Verify all required fields are present
   - Check numerical consistency
   - Cross-reference amounts across pages
   - Verify item list completeness

8. Re-verification Process:
   - Re-extract all amounts independently if discrepancies are detected
   - Document changes and reasons

9. Language and Text Handling:
   - Maintain original language
   - Preserve original formatting of dates and numbers
   - Handle multi-byte characters correctly

10. Handling Long Data:
   - If extracted data is too long to process, you may exceptionally truncate it
   - Avoid truncation if possible
   - Do not alter or transform the data arbitrarily

11. Post-extraction Verification:
   - Compare extracted data with the actual content in the PDF file
   - Ensure consistency and accuracy between extracted data and original content
   - Document any discrepancies found during comparison

12. Extraction and Verification Sequence:
   1. Extract invoice number and amounts (total, tax, face value) and cross-verify with the PDF
   2. Check the number of items in the item list (note that items with only names and no amounts may be unrelated notes)
   3. Extract detailed information of items (amount, quantity, etc.) and cross-verify with the PDF
   4. Compare the total amount of items with the invoice amount and perform a final cross-verification with the PDF
   5. If any issues arise during this extraction process, re-extract and verify the data
"""

    if metadata:
        metadata_str = _format_metadata(metadata)
        base_prompt += f"""

Additional Information:
{metadata_str}

Use this information for more accurate extraction.
Match customer_names with invoice data if provided, maintaining original text.
"""

    if analysis_reason:
        base_prompt += f"""

Analysis Reason:
{analysis_reason}

Use this analysis to prioritize amount information locations.
Remember to keep all extracted text in its original language.
"""

    return base_prompt
