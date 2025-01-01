from typing import Any, Dict

# PDF Analysis Data Extraction Schema
PDF_ANALYZER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "page_ranges": {
            "type": "array",
            "description": "List of page ranges for each invoice document",
            "items": {
                "type": "object",
                "properties": {
                    "start_page": {
                        "type": "integer",
                        "description": "Start page number (1-based index)",
                        "minimum": 1,
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "End page number (1-based index)",
                        "minimum": 1,
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for determining this page range as a single invoice",
                    },
                },
                "required": ["start_page", "end_page", "reason"],
            },
        }
    },
    "required": ["page_ranges"],
}

# Invoice Extraction Schema
INVOICE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_number": {
            "type": "string",
            "description": (
                "Invoice number - Required field\n"
                "- Location: Top right of the first page\n"
                "- Label: 'Invoice No:', 'Invoice Number:', etc.\n"
                "- Validation: Combination of letters, numbers, and special characters"
            ),
        },
        "issue_date": {
            "type": "string",
            "description": (
                "Issue date - Required field\n"
                "- Location: Top of the first page\n"
                "- Label: 'Issue Date:', 'Date of Issue:', etc.\n"
                "- Format: YYYY-MM-DD"
            ),
        },
        "due_date": {
            "type": "string",
            "description": (
                "Due date - Required field\n"
                "- Location: Near the issue date\n"
                "- Label: 'Due Date:', 'Payment Due:', etc.\n"
                "- Format: YYYY-MM-DD"
            ),
        },
        "customer_name": {
            "type": "string",
            "description": (
                "Customer name - Required field\n"
                "- Location: Top left of the first page\n"
                "- Format: Company/Branch name (without honorifics)"
            ),
        },
        "items": {
            "type": "array",
            "description": (
                "List of items - Required field\n"
                "- Structure: Tabular item information\n"
                "- Inclusion criteria:\n"
                "  * Must have item_name\n"
                "  * Must have quantity\n"
                "  * Must have unit_price\n"
                "  * Must have amount\n"
                "- Exclusion criteria:\n"
                "  * Category/section text\n"
                "  * Rows with only notes/descriptions (no quantity/unit_price/amount)\n"
                "  * Subtotal/total rows\n"
                "  * Rows missing any of quantity/unit_price/amount\n"
                "- Note/description handling:\n"
                "  * Additional descriptions for items are included in item_name\n"
                "  * Independent note/description rows are excluded"
            ),
            "items": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": (
                            "Item name (can be an empty string)\n"
                            "- Name of the product/service\n"
                            "- May include related notes or descriptions\n"
                            "- Excludes category/section text"
                        ),
                    },
                    "quantity": {
                        "type": "integer",
                        "description": (
                            "Quantity\n"
                            "- Integer value\n"
                            "- Can be positive or negative (negative for returns, etc.)"
                        ),
                    },
                    "unit_price": {
                        "type": "number",
                        "description": (
                            "Unit price\n"
                            "- Number without commas/currency symbols\n"
                            "- Can be positive or negative (negative for discounts, etc.)"
                        ),
                    },
                    "amount": {
                        "type": "number",
                        "description": (
                            "Amount\n"
                            "- Should match quantity * unit_price\n"
                            "- Can be positive or negative"
                        ),
                    },
                },
                "required": ["item_name", "quantity", "unit_price", "amount"],
            },
        },
        "subtotal": {
            "type": "number",
            "description": (
                "Subtotal - Required field\n"
                "- Location and validation:\n"
                "  * Compare the amount at the top of the first page with the total amount on the last page\n"
                "  * Use the value if they are similar or match\n"
                "  * If there is a difference, prioritize the first page amount\n"
                "- Label: 'Subtotal:', 'Total before tax:', etc.\n"
                "- Can be negative (if the entire invoice is a return/discount)"
            ),
        },
        "taxes": {
            "type": "array",
            "description": (
                "Tax information - Required field\n"
                "- Location and validation:\n"
                "  * Compare the tax amount at the top of the first page with the total tax amount on the last page\n"
                "  * Use the value if they are similar or match\n"
                "  * If there is a difference, prioritize the first page amount\n"
                "- Structure: Information by tax type\n"
                "- Can be negative (if the subtotal is negative)"
            ),
            "items": {
                "type": "object",
                "properties": {
                    "tax_type": {
                        "type": "string",
                        "description": "Type of tax (e.g., 'VAT', 'Sales Tax', etc.)",
                    },
                    "tax_rate": {
                        "type": "number",
                        "description": (
                            "Tax rate\n"
                            "- Number without % symbol\n"
                            "- Between 0 and 100 inclusive"
                        ),
                    },
                    "tax_amount": {
                        "type": "number",
                        "description": (
                            "Tax amount\n"
                            "- Number without commas/currency symbols\n"
                            "- Compare with the tax amount on the first and last pages for validation\n"
                            "- Can be positive or negative"
                        ),
                    },
                },
                "required": ["tax_type", "tax_rate", "tax_amount"],
            },
        },
        "total_amount": {
            "type": "number",
            "description": (
                "Total amount - Required field\n"
                "- Location and validation:\n"
                "  * Compare the amount at the top of the first page with the total amount on the last page\n"
                "  * Use the value if they are similar or match\n"
                "  * If there is a difference, prioritize the first page amount\n"
                "- Label: 'Total:', 'Grand Total:', etc.\n"
                "- Can be negative (if the entire invoice is a return/discount)"
            ),
        },
    },
    "required": [
        "invoice_number",
        "issue_date",
        "due_date",
        "customer_name",
        "items",
        "subtotal",
        "taxes",
        "total_amount",
    ],
}
