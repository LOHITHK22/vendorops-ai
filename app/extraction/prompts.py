SYSTEM_PROMPT = """You extract structured business data from vendor documents.
Use only the provided source text. Do not guess.
Return null for missing fields.
Every important non-null field should have source evidence when possible.
Use confidence to reflect how strongly the source text supports the output."""


def build_extraction_prompt(file_type: str, source_text: str) -> str:
    return f"""Document type hint: {file_type}

Extract vendor/invoice/contract/email business data from this source.

Rules:
- Choose record_type from invoice, contract, email, csv, unknown.
- For invoices, extract invoice number as document_id when present.
- For contracts, extract contract/agreement name or ID as document_id when present.
- Use total_amount only for the final amount due or contract value.
- Use ISO dates.
- If a value is not present in source text, use null.
- Include concise source_evidence for important fields.
- Set needs_review=true when required business fields are missing or confidence is low.

Source text:
{source_text[:12000]}
"""

