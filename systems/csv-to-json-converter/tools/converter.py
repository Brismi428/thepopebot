#!/usr/bin/env python3
"""
CSV-to-JSON Converter

Main orchestrator for CSV-to-JSON conversion pipeline.
Coordinates analysis, parsing, type inference, validation, and output generation.

Pattern: Orchestrator pattern
"""

import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
import glob as glob_module

# Import tool modules
import csv_analyzer
import type_inferrer
import data_validator
import json_writer
import summary_generator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def collect_files(input_spec: str) -> List[str]:
    """
    Collect CSV files from input specification.
    
    Args:
        input_spec: File path, directory, or glob pattern
        
    Returns:
        List of absolute file paths
    """
    path = Path(input_spec)
    
    # Single file
    if path.is_file():
        return [str(path.resolve())]
    
    # Directory
    if path.is_dir():
        return [str(f.resolve()) for f in path.glob('*.csv')]
    
    # Glob pattern
    matches = glob_module.glob(input_spec, recursive=True)
    return [str(Path(f).resolve()) for f in matches if Path(f).is_file()]


def parse_csv(file_path: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse CSV file using detected parameters.
    
    Args:
        file_path: Path to CSV file
        analysis: Analysis result from csv_analyzer
        
    Returns:
        List of dictionaries (parsed CSV data)
    """
    encoding = analysis['encoding']
    delimiter = analysis['delimiter']
    quotechar = analysis['quotechar']
    header_row_index = analysis['header_row_index']
    column_names = analysis['column_names']
    
    parsed_data = []
    
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        # Strip BOM if present
        first_char = f.read(1)
        if first_char != '\ufeff':
            f.seek(0)
        
        reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
        
        # Skip to data rows (past header if present)
        if header_row_index == 0:
            next(reader, None)  # Skip header row
        
        for i, row in enumerate(reader):
            # Skip completely empty rows
            if not any(row):
                continue
            
            # Handle ragged rows
            if len(row) < len(column_names):
                # Pad with empty strings
                row.extend([''] * (len(column_names) - len(row)))
            elif len(row) > len(column_names):
                # Truncate
                logger.warning(f"Row {i}: {len(row)} columns (expected {len(column_names)}), truncating")
                row = row[:len(column_names)]
            
            # Create dict
            row_dict = {col: val for col, val in zip(column_names, row)}
            parsed_data.append(row_dict)
    
    return parsed_data


def process_file(file_path: str, output_format: str, output_directory: str,
                 type_inference: bool, strict_mode: bool) -> Dict[str, Any]:
    """
    Process a single CSV file through the full pipeline.
    
    Args:
        file_path: Path to CSV file
        output_format: 'json' or 'jsonl'
        output_directory: Output directory path
        type_inference: Enable type inference
        strict_mode: Halt on validation errors
        
    Returns:
        File metadata dictionary
    """
    logger.info(f"Processing {Path(file_path).name}...")
    
    try:
        # Step 1: Analyze CSV structure
        analysis = csv_analyzer.analyze(file_path)
        
        # Step 2: Parse CSV
        parsed_data = parse_csv(file_path, analysis)
        
        if not parsed_data:
            raise ValueError("No data rows found in CSV")
        
        # Step 3: Infer types
        if type_inference:
            type_map = type_inferrer.infer_types(parsed_data, analysis['column_names'])
        else:
            # No type inference - all strings
            type_map = {
                col: {
                    'type': 'string',
                    'confidence': 1.0,
                    'conflicts': [],
                    'null_count': 0,
                    'sample_values': []
                }
                for col in analysis['column_names']
            }
        
        # Step 4: Validate
        validation = data_validator.validate_data(
            parsed_data, type_map, strict_mode,
            expected_columns=analysis['column_count']
        )
        
        if not validation['validation_passed']:
            raise RuntimeError("Validation failed in strict mode")
        
        # Step 5: Convert and write
        output_path = Path(output_directory) / f"{Path(file_path).stem}.{output_format}"
        write_result = json_writer.write_json(
            parsed_data, type_map, str(output_path), output_format
        )
        
        # Build file metadata
        return {
            'input': file_path,
            'output': write_result['output_file'],
            'rows_written': write_result['rows_written'],
            'column_count': analysis['column_count'],
            'encoding': analysis['encoding'],
            'processing_time_ms': write_result['processing_time_ms'],
            'file_size_bytes': write_result['file_size_bytes'],
            'inferred_types': type_map,
            'validation_issues': validation['issues'],
            'validation_stats': validation['stats'],
        }
        
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")
        return {
            'input': file_path,
            'error': str(e),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert CSV files to JSON/JSONL with intelligent type inference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.csv
  %(prog)s data/ --output-format jsonl
  %(prog)s "data/*.csv" --strict --no-type-inference
  %(prog)s file1.csv file2.csv --output-directory converted/
        """
    )
    parser.add_argument('csv_files', nargs='+',
                       help='CSV file(s), directory, or glob pattern')
    parser.add_argument('--output-format', choices=['json', 'jsonl'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--output-directory', default='output/',
                       help='Output directory (default: output/)')
    parser.add_argument('--type-inference', dest='type_inference',
                       action='store_true', default=True,
                       help='Enable type inference (default)')
    parser.add_argument('--no-type-inference', dest='type_inference',
                       action='store_false',
                       help='Disable type inference, keep all values as strings')
    parser.add_argument('--strict', dest='strict_mode', action='store_true',
                       help='Halt on validation errors (default: continue with warnings)')
    
    args = parser.parse_args()
    
    try:
        # Collect input files
        all_files = []
        for spec in args.csv_files:
            files = collect_files(spec)
            all_files.extend(files)
        
        # Remove duplicates
        all_files = list(set(all_files))
        
        if not all_files:
            logger.error(f"No CSV files found matching: {args.csv_files}")
            return 1
        
        logger.info(f"Found {len(all_files)} CSV file(s) to process")
        
        # Process each file
        file_metadata = []
        for file_path in all_files:
            metadata = process_file(
                file_path,
                args.output_format,
                args.output_directory,
                args.type_inference,
                args.strict_mode
            )
            file_metadata.append(metadata)
        
        # Generate summary and report
        summary_result = summary_generator.generate_summary(
            file_metadata,
            args.output_directory
        )
        
        # Print summary
        successful = len([f for f in file_metadata if not f.get('error')])
        failed = len(file_metadata) - successful
        total_rows = sum(f.get('rows_written', 0) for f in file_metadata)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("CONVERSION COMPLETE")
        logger.info(f"Files processed: {len(file_metadata)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total rows: {total_rows:,}")
        logger.info(f"Output directory: {args.output_directory}")
        logger.info(f"Run summary: {summary_result['summary_path']}")
        logger.info(f"Validation report: {summary_result['report_path']}")
        logger.info("=" * 60)
        
        # Exit code: 0 if all successful, 1 if any failed
        return 0 if failed == 0 else 1
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
