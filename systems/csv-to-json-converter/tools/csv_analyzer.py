#!/usr/bin/env python3
"""
CSV Structure Analyzer

Analyzes CSV file structure to detect encoding, delimiter, quote character,
header row, and column count. Handles BOM, various encodings, and malformed CSVs.

Pattern: File analysis with encoding detection
"""

import sys
import csv
import logging
import argparse
import json
from pathlib import Path

try:
    import chardet
except ImportError:
    chardet = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def detect_encoding(file_path: str) -> str:
    """
    Detect file encoding using chardet library.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Detected encoding (default: utf-8)
    """
    if not chardet:
        logger.warning("chardet not installed, defaulting to utf-8")
        return 'utf-8'
    
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(100000)  # Read first 100KB
        result = chardet.detect(raw)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0)
        logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
        return encoding or 'utf-8'
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}, defaulting to utf-8")
        return 'utf-8'


def detect_csv_params(file_path: str, encoding: str) -> dict:
    """
    Detect CSV dialect (delimiter, quotechar) using csv.Sniffer.
    
    Args:
        file_path: Path to the CSV file
        encoding: File encoding
        
    Returns:
        Dictionary with delimiter and quotechar
    """
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            sample = f.read(10000)
        
        # Strip BOM if present
        if sample.startswith('\ufeff'):
            sample = sample[1:]
        
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        return {
            'delimiter': dialect.delimiter,
            'quotechar': dialect.quotechar,
        }
    except Exception as e:
        logger.warning(f"Dialect detection failed: {e}, defaulting to comma-separated")
        return {'delimiter': ',', 'quotechar': '"'}


def detect_header_row(file_path: str, encoding: str, delimiter: str) -> int:
    """
    Detect which row contains headers (or -1 if no headers).
    
    Args:
        file_path: Path to the CSV file
        encoding: File encoding
        delimiter: CSV delimiter
        
    Returns:
        Header row index (0 for first row, -1 for no headers)
    """
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            sample = f.read(10000)
        
        # Strip BOM
        if sample.startswith('\ufeff'):
            sample = sample[1:]
        
        has_header = csv.Sniffer().has_header(sample)
        return 0 if has_header else -1
    except Exception as e:
        logger.warning(f"Header detection failed: {e}, assuming headers present")
        return 0


def analyze(file_path: str, header_row: str = 'auto') -> dict:
    """
    Analyze CSV structure and return parameters.
    
    Args:
        file_path: Path to the CSV file
        header_row: 'auto' for detection, integer for specific row, -1 for no headers
        
    Returns:
        Dictionary with analysis results
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Detect encoding
    encoding = detect_encoding(file_path)
    
    # Detect CSV parameters
    params = detect_csv_params(file_path, encoding)
    
    # Detect header row
    if header_row == 'auto':
        header_row_index = detect_header_row(file_path, encoding, params['delimiter'])
    else:
        header_row_index = int(header_row)
    
    # Read first few rows as sample
    sample_rows = []
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            # Strip BOM if present
            first_char = f.read(1)
            if first_char != '\ufeff':
                f.seek(0)
            
            reader = csv.reader(f, delimiter=params['delimiter'], 
                              quotechar=params['quotechar'])
            for i, row in enumerate(reader):
                if i < 5:
                    sample_rows.append(row)
                else:
                    break
    except Exception as e:
        logger.error(f"Failed to read sample rows: {e}")
        raise
    
    if not sample_rows:
        raise ValueError("CSV file is empty")
    
    # Determine column names
    column_count = len(sample_rows[0]) if sample_rows else 0
    if header_row_index == 0 and sample_rows:
        column_names = sample_rows[0]
        sample_data = sample_rows[1:]
    elif header_row_index == -1:
        column_names = [f"col_{i}" for i in range(column_count)]
        sample_data = sample_rows
    else:
        # Specific header row index
        if header_row_index < len(sample_rows):
            column_names = sample_rows[header_row_index]
            sample_data = sample_rows[header_row_index + 1:]
        else:
            column_names = [f"col_{i}" for i in range(column_count)]
            sample_data = sample_rows
    
    return {
        'encoding': encoding,
        'delimiter': params['delimiter'],
        'quotechar': params['quotechar'],
        'header_row_index': header_row_index,
        'column_count': column_count,
        'column_names': column_names,
        'sample_rows': sample_data,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze CSV file structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.csv
  %(prog)s data.csv --header-row 0
  %(prog)s data.csv --header-row -1
        """
    )
    parser.add_argument('file', help='CSV file to analyze')
    parser.add_argument('--header-row', default='auto',
                       help="Header row: 'auto', integer index, or -1 for no headers")
    parser.add_argument('--output', help='Output JSON file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        result = analyze(args.file, args.header_row)
        
        output = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            logger.info(f"Analysis saved to {args.output}")
        else:
            print(output)
        
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
