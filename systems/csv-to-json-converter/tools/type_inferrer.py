#!/usr/bin/env python3
"""
Type Inference Specialist

Infers data types for CSV columns by analyzing all values.
Detects integers, floats, booleans, dates, and handles missing values.

Pattern: Statistical type inference with confidence scoring
"""

import sys
import re
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

NULL_VALUES = {'', 'N/A', 'null', 'NULL', 'None', '-', 'n/a', 'NA', 'nan', 'NaN'}


def is_int(value: str) -> bool:
    """Check if value can be parsed as integer."""
    if value in NULL_VALUES:
        return False
    try:
        int(value)
        return '.' not in value  # Exclude floats like "1.0"
    except (ValueError, TypeError):
        return False


def is_float(value: str) -> bool:
    """Check if value can be parsed as float."""
    if value in NULL_VALUES:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_boolean(value: str) -> bool:
    """Check if value is boolean-like."""
    return str(value).strip().lower() in {
        'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'
    }


def is_datetime(value: str) -> bool:
    """Check if value can be parsed as datetime."""
    if value in NULL_VALUES:
        return False
    if not date_parser:
        # Fallback to basic ISO8601 pattern matching
        iso_pattern = r'^\d{4}-\d{2}-\d{2}'
        return bool(re.match(iso_pattern, str(value).strip()))
    
    try:
        date_parser.parse(str(value).strip())
        return True
    except (ValueError, TypeError, date_parser.ParserError):
        return False


def infer_column_type(values: list[str], column_name: str) -> dict:
    """
    Infer type for a single column.
    
    Args:
        values: List of string values from the column
        column_name: Name of the column (for logging)
        
    Returns:
        Dictionary with type, confidence, conflicts, null_count, sample_values
    """
    total = len(values)
    non_null = [v for v in values if v not in NULL_VALUES]
    null_count = total - len(non_null)
    
    if not non_null:
        logger.info(f"Column '{column_name}': all null → string")
        return {
            'type': 'string',
            'confidence': 1.0,
            'conflicts': [],
            'null_count': null_count,
            'sample_values': []
        }
    
    # Count type matches
    int_count = sum(is_int(v) for v in non_null)
    float_count = sum(is_float(v) for v in non_null)
    bool_count = sum(is_boolean(v) for v in non_null)
    datetime_count = sum(is_datetime(v) for v in non_null)
    
    # Determine best type with confidence
    # Priority: boolean > int > float > datetime > string
    type_scores = [
        ('boolean', bool_count / len(non_null) if non_null else 0),
        ('int', int_count / len(non_null) if non_null else 0),
        ('float', (float_count - int_count) / len(non_null) if non_null else 0),
        ('datetime', datetime_count / len(non_null) if non_null else 0),
    ]
    
    best_type, best_score = max(type_scores, key=lambda x: x[1])
    
    # Default to string if confidence is low
    confidence_threshold = 0.8
    if best_score < confidence_threshold:
        best_type = 'string'
        best_score = 1.0
    
    # Log conflicts (values that don't match inferred type)
    conflicts = []
    type_check = {
        'int': is_int,
        'float': is_float,
        'boolean': is_boolean,
        'datetime': is_datetime,
    }.get(best_type, lambda x: True)
    
    for i, v in enumerate(values):
        if v in NULL_VALUES:
            continue
        if not type_check(v):
            conflicts.append(f"Row {i}: '{v}' doesn't match {best_type}")
    
    # Limit conflicts to first 10
    if len(conflicts) > 10:
        conflicts = conflicts[:10] + [f"... and {len(conflicts) - 10} more"]
    
    sample_values = non_null[:5] if len(non_null) <= 5 else non_null[:5]
    
    logger.info(
        f"Column '{column_name}': {best_type} "
        f"(confidence: {best_score:.2f}, conflicts: {len(conflicts)})"
    )
    
    return {
        'type': best_type,
        'confidence': round(best_score, 3),
        'conflicts': conflicts,
        'null_count': null_count,
        'sample_values': sample_values,
    }


def infer_types(data: list[dict], column_names: list[str]) -> dict:
    """
    Infer types for all columns.
    
    Args:
        data: List of dictionaries (parsed CSV)
        column_names: List of column names to analyze
        
    Returns:
        Type map dictionary
    """
    type_map = {}
    for col in column_names:
        values = [row.get(col, '') for row in data]
        type_map[col] = infer_column_type(values, col)
    return type_map


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Infer data types for CSV columns',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json
  %(prog)s data.json --output types.json
        """
    )
    parser.add_argument('data_file', help='JSON file with parsed CSV data')
    parser.add_argument('--output', help='Output JSON file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        # Read parsed data
        data_path = Path(args.data_file)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {args.data_file}")
        
        data = json.loads(data_path.read_text(encoding='utf-8'))
        
        if not isinstance(data, list) or not data:
            raise ValueError("Data must be a non-empty list of dictionaries")
        
        # Get column names from first row
        column_names = list(data[0].keys())
        
        # Infer types
        type_map = infer_types(data, column_names)
        
        # Output
        output = json.dumps(type_map, indent=2, ensure_ascii=False)
        
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            logger.info(f"Type map saved to {args.output}")
        else:
            print(output)
        
        return 0
    except Exception as e:
        logger.error(f"Type inference failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
