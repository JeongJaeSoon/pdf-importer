"""PDF Page Analyzer"""

"""Initialize

Args:
    api_key: OpenAI API key
"""

"""Analyze PDF pages

Args:
    text: PDF text
    expected_count: Expected number of invoices

Returns:
    List of page ranges (e.g., ["1-3", "4-5", "6"])
"""

# Generate prompt for LLM
prompt = self._create_prompt(text, expected_count)

# Analyze pages using LLM
response = await self.client.chat.completions.create(...)

# Parse and validate response
try:
    # ... existing code ...
except ValueError:
    raise ValueError("Invalid page range.")

"""Generate prompt

Args:
    text: PDF text
    expected_count: Expected number of invoices
"""
