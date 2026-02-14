#!/usr/bin/env python3
"""Validate site intelligence pack against JSON schema."""

import sys
import json
import argparse
import logging
from jsonschema import validate, ValidationError, Draft7Validator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "object",
    "required": ["site", "inventory", "ranked_pages", "evidence_index"],
    "properties": {
        "site": {"type": "object"},
        "inventory": {"type": "array"},
        "ranked_pages": {"type": "array"},
        "synthesized_findings": {"type": "object"},
        "evidence_index": {"type": "object"}
    }
}


def validate_pack(data: dict) -> dict:
    """Validate intelligence pack structure."""
    errors = []
    
    try:
        validate(instance=data, schema=SCHEMA)
        logger.info("Schema validation passed")
        valid = True
    except ValidationError as e:
        errors.append(f"Schema error: {e.message}")
        logger.error(f"Validation failed: {e.message}")
        valid = False
    
    return {"valid": valid, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Intelligence pack JSON")
    parser.add_argument("--output", help="Validation result output")
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        result = validate_pack(data)
        output = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
        else:
            print(output)
        
        return 0 if result["valid"] else 1
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        print(json.dumps({"valid": False, "errors": [str(e)]}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
