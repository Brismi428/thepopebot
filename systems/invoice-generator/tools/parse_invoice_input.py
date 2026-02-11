#!/usr/bin/env python3
"""
Parse and validate invoice JSON input with business rule checks.

Validates required fields, data types, and business constraints before
invoice generation. Normalizes client name for filename generation.

Inputs:
    - input_path: str -- Path to JSON file or '-' for stdin

Outputs:
    - JSON dict with validated, normalized invoice data to stdout

Exit Codes:
    0: Success
    1: Validation error or malformed input
"""

import sys
import json
import logging
from pathlib import Path
from datetime import date
from decimal import Decimal

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

try:
    from dateutil import parser as date_parser
except ImportError:
    print("Error: python-dateutil not installed. Run: pip install python-dateutil", file=sys.stderr)
    sys.exit(1)

try:
    from slugify import slugify
except ImportError:
    print("Error: python-slugify not installed. Run: pip install python-slugify", file=sys.stderr)
    sys.exit(1)


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


INVOICE_SCHEMA = {
    "type": "object",
    "required": [
        "client_name",
        "project_description",
        "invoice_date",
        "due_date",
        "line_items"
    ],
    "properties": {
        "client_name": {"type": "string", "minLength": 1},
        "client_address": {"type": "string"},
        "client_email": {"type": "string"},
        "project_description": {"type": "string", "minLength": 1},
        "invoice_date": {"type": "string"},
        "due_date": {"type": "string"},
        "line_items": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["description", "quantity", "rate"],
                "properties": {
                    "description": {"type": "string", "minLength": 1},
                    "quantity": {"type": "number", "exclusiveMinimum": 0},
                    "rate": {"type": "number", "minimum": 0}
                }
            }
        },
        "payment_terms": {"type": "string"},
        "payment_methods": {
            "type": "array",
            "items": {"type": "string"}
        },
        "notes": {"type": "string"}
    }
}


def main(input_path: str) -> dict:
    """Parse and validate invoice input JSON."""
    try:
        # Step 1: Parse input JSON
        if input_path == '-':
            logger.info("Reading invoice data from stdin")
            data = json.load(sys.stdin)
        else:
            logger.info(f"Reading invoice data from {input_path}")
            data = json.loads(Path(input_path).read_text(encoding='utf-8'))

        # Step 2: Validate schema
        logger.info("Validating invoice schema")
        validate(instance=data, schema=INVOICE_SCHEMA)

        # Step 3: Parse and validate dates
        logger.info("Validating date fields")
        try:
            invoice_date = date_parser.parse(data["invoice_date"]).date()
            due_date = date_parser.parse(data["due_date"]).date()
        except Exception as e:
            raise ValueError(f"Invalid date format: {e}")

        # Business rule: due_date >= invoice_date
        if due_date < invoice_date:
            raise ValueError(
                f"due_date ({due_date}) must be >= invoice_date ({invoice_date})"
            )

        # Step 4: Validate line items have positive quantities and rates
        for i, item in enumerate(data["line_items"]):
            if item["quantity"] <= 0:
                raise ValueError(
                    f"Line item {i+1}: quantity must be > 0 (got {item['quantity']})"
                )
            if item["rate"] < 0:
                raise ValueError(
                    f"Line item {i+1}: rate must be >= 0 (got {item['rate']})"
                )

        # Step 5: Normalize client name for filename (slugify)
        client_slug = slugify(data["client_name"], lowercase=True)
        if not client_slug:
            raise ValueError(
                f"client_name '{data['client_name']}' cannot be converted to valid filename"
            )
        data["client_slug"] = client_slug

        # Step 6: Store normalized dates as ISO strings
        data["invoice_date_normalized"] = invoice_date.isoformat()
        data["due_date_normalized"] = due_date.isoformat()

        logger.info(f"✓ Validation passed for client: {data['client_name']}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Business rule validation failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse and validate invoice JSON input")
    parser.add_argument(
        "input_path",
        help="Path to JSON file or '-' for stdin"
    )
    args = parser.parse_args()

    result = main(args.input_path)
    print(json.dumps(result, indent=2))
