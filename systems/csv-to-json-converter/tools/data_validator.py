#!/usr/bin/env python3
"""
Data Validation Specialist

Validates CSV data quality and generates detailed validation reports.
Checks for empty rows, duplicates, ragged rows, and type conflicts.

Pattern: Comprehensive validation with actionable reporting
"""

import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def validate_data(data: list[dict], type_map: dict, strict_mode: bool = False,
                  expected_columns: int = None) -> dict:
    """
    Validate parsed CSV data.
    
    Args:
        data: List of dictionaries (parsed CSV)
        type_map: Type inference results
        strict_mode: If True, fail on any issues
        expected_columns: Expected column count (for ragged row detection)
        
    Returns:
        Validation report dictionary
    """
    issues = []
    empty_rows = 0
    duplicate_rows = 0
    ragged_rows = 0
    type_conflicts = 0
    
    seen_hashes = set()
    
    for i, row in enumerate(data):
        # Detect empty rows
        if all(v in ('', None) for v in row.values()):
            empty_rows += 1
            issues.append({
                'row': i,
                'column': None,
                'issue': 'Empty row',
                'severity': 'warning',
                'action': 'Row should be skipped',
            })
            continue
        
        # Detect duplicate rows (hash-based)
        row_hash = hashlib.md5(
            str(sorted(row.items())).encode()
        ).hexdigest()
        
        if row_hash in seen_hashes:
            duplicate_rows += 1
            issues.append({
                'row': i,
                'column': None,
                'issue': 'Duplicate row',
                'severity': 'info',
                'action': 'Kept duplicate',
            })
        seen_hashes.add(row_hash)
        
        # Detect ragged rows (if expected_columns provided)
        if expected_columns is not None:
            actual_columns = len([v for v in row.values() if v != ''])
            if actual_columns != expected_columns:
                ragged_rows += 1
                issues.append({
                    'row': i,
                    'column': None,
                    'issue': f'Ragged row: {actual_columns} columns (expected {expected_columns})',
                    'severity': 'warning',
                    'action': 'Padded with null or truncated',
                })
    
    # Count type conflicts from type map
    for col, type_info in type_map.items():
        if type_info.get('conflicts'):
            conflicts = type_info['conflicts']
            # Filter out the "... and N more" summary line
            conflict_count = len([c for c in conflicts if not c.startswith('...')])
            type_conflicts += conflict_count
            
            # Add conflicts to issues (limit to avoid overwhelming report)
            for conflict in conflicts[:5]:
                issues.append({
                    'row': None,
                    'column': col,
                    'issue': conflict,
                    'severity': 'warning',
                    'action': 'Type conversion may fail or produce null',
                })
    
    # Determine validation result
    validation_passed = True
    if strict_mode:
        # In strict mode, any issues cause validation to fail
        error_issues = [iss for iss in issues if iss['severity'] in ('error', 'warning')]
        if error_issues:
            validation_passed = False
    
    stats = {
        'empty_rows': empty_rows,
        'duplicate_rows': duplicate_rows,
        'ragged_rows': ragged_rows,
        'type_conflicts': type_conflicts,
        'total_issues': len(issues),
    }
    
    logger.info(
        f"Validation: {len(issues)} issues found "
        f"(empty: {empty_rows}, duplicates: {duplicate_rows}, "
        f"ragged: {ragged_rows}, type conflicts: {type_conflicts})"
    )
    
    if not validation_passed:
        logger.error("Validation FAILED in strict mode")
    else:
        logger.info("Validation PASSED")
    
    return {
        'issues': issues,
        'stats': stats,
        'validation_passed': validation_passed,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate CSV data quality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json types.json
  %(prog)s data.json types.json --strict
  %(prog)s data.json types.json --expected-columns 5
        """
    )
    parser.add_argument('data_file', help='JSON file with parsed CSV data')
    parser.add_argument('type_file', help='JSON file with type map')
    parser.add_argument('--strict', action='store_true',
                       help='Fail on any validation issues')
    parser.add_argument('--expected-columns', type=int,
                       help='Expected number of columns (for ragged row detection)')
    parser.add_argument('--output', help='Output JSON file (default: stdout)')
    
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
        
        # Validate
        result = validate_data(data, type_map, args.strict, args.expected_columns)
        
        # Output
        output = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            logger.info(f"Validation report saved to {args.output}")
        else:
            print(output)
        
        # Exit code reflects validation result in strict mode
        if args.strict and not result['validation_passed']:
            return 1
        
        return 0
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
