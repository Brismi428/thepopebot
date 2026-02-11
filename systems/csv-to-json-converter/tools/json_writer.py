#!/usr/bin/env python3
"""
JSON Writer

Converts validated CSV data to JSON or JSONL with type conversion.
Supports streaming for large files and handles missing values.

Pattern: Adapted from json_read_write (tool_catalog.md)
"""

import sys
import json
import time
import logging
import argparse
from pathlib import Path

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

NULL_VALUES = {'', 'N/A', 'null', 'NULL', 'None', '-', 'n/a', 'NA', 'nan', 'NaN'}


def convert_value(value: str, target_type: str):
    """
    Convert string value to target type.
    
    Args:
        value: String value from CSV
        target_type: Target type ('int', 'float', 'boolean', 'datetime', 'string')
        
    Returns:
        Converted value or None for null values
    """
    if value in NULL_VALUES:
        return None
    
    try:
        if target_type == 'int':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'boolean':
            return str(value).strip().lower() in {'true', 'yes', '1', 't', 'y'}
        elif target_type == 'datetime':
            if date_parser:
                dt = date_parser.parse(str(value).strip())
                return dt.isoformat()
            else:
                # Fallback: return as-is if dateutil not available
                return str(value).strip()
        else:
            return str(value)
    except (ValueError, TypeError) as e:
        # If conversion fails, keep as string
        logger.warning(f"Conversion failed for '{value}' to {target_type}: {e}")
        return str(value)


def write_json(data: list[dict], type_map: dict, output_path: str,
               output_format: str = 'json') -> dict:
    """
    Write JSON or JSONL with type conversions.
    
    Args:
        data: List of dictionaries (parsed CSV)
        type_map: Type conversion instructions
        output_path: Output file path
        output_format: 'json' or 'jsonl'
        
    Returns:
        Metadata dictionary
    """
    start = time.time()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Apply type conversions
    converted_data = []
    for row in data:
        converted_row = {}
        for col, value in row.items():
            type_info = type_map.get(col, {})
            target_type = type_info.get('type', 'string')
            converted_row[col] = convert_value(value, target_type)
        converted_data.append(converted_row)
    
    # Write output
    rows_written = 0
    try:
        if output_format == 'jsonl':
            with output_path.open('w', encoding='utf-8') as f:
                for record in converted_data:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    rows_written += 1
        else:  # json
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(converted_data, f, indent=2, ensure_ascii=False)
            rows_written = len(converted_data)
    except Exception as e:
        # Clean up partial write
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(f"Failed to write output: {e}") from e
    
    elapsed_ms = (time.time() - start) * 1000
    file_size = output_path.stat().st_size
    
    logger.info(
        f"Wrote {rows_written} rows to {output_path.name} "
        f"({file_size} bytes, {elapsed_ms:.1f}ms)"
    )
    
    return {
        'output_file': str(output_path),
        'rows_written': rows_written,
        'file_size_bytes': file_size,
        'processing_time_ms': round(elapsed_ms, 2),
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Write JSON or JSONL output with type conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json types.json output.json
  %(prog)s data.json types.json output.jsonl --format jsonl
        """
    )
    parser.add_argument('data_file', help='JSON file with parsed CSV data')
    parser.add_argument('type_file', help='JSON file with type map')
    parser.add_argument('output_file', help='Output file path')
    parser.add_argument('--format', choices=['json', 'jsonl'], default='json',
                       help='Output format (default: json)')
    
    args = parser.parse_args()
    
    try:
        # Read parsed data
        data_path = Path(args.data_file)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {args.data_file}")
        data = json.loads(data_path.read_text(encoding='utf-8'))
        
        # Read type map
        type_path = Path(args.type_file)
        if not type_path.exists():
            raise FileNotFoundError(f"Type file not found: {args.type_file}")
        type_map = json.loads(type_path.read_text(encoding='utf-8'))
        
        # Write output
        metadata = write_json(data, type_map, args.output_file, args.format)
        
        # Print metadata
        print(json.dumps(metadata, indent=2))
        
        return 0
    except Exception as e:
        logger.error(f"JSON writing failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
