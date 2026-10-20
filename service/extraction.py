import re
from datetime import date


def extract_invoice(markdown: str) -> dict:
    """Conservative rule extraction: absent or ambiguous fields remain null."""
    identifiers = set(
        re.findall(
            r"^\s*Invoice\s*:\s*([A-Za-z0-9_-]{1,60})\s*$", markdown, re.I | re.M
        )
    )
    dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", markdown))
    valid_dates = set()
    for value in dates:
        try:
            valid_dates.add(date.fromisoformat(value).isoformat())
        except ValueError:
            pass
    totals = set(
        re.findall(
            r"^\s*Total\s*:\s*(USD|EUR|OMR)\s+(\d+(?:\.\d{1,3})?)\s*$",
            markdown,
            re.I | re.M,
        )
    )
    invoice_id = next(iter(identifiers)) if len(identifiers) == 1 else None
    invoice_date = next(iter(valid_dates)) if len(valid_dates) == 1 else None
    amount = next(iter(totals)) if len(totals) == 1 else None
    fields = {
        "invoice_id": invoice_id,
        "date": invoice_date,
        "currency": amount[0].upper() if amount else None,
        "total": amount[1] if amount else None,
    }
    return {
        "schema": "invoice.v1",
        "method": "rules",
        "fields": fields,
        "warnings": [
            f"Missing or ambiguous {key}"
            for key, value in fields.items()
            if value is None
        ],
    }
