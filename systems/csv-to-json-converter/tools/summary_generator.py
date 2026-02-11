#!/usr/bin/env python3
"""
Summary Generator

Aggregates per-file metadata into run_summary.json and validation_report.md.
Provides comprehensive reporting for batch CSV conversion jobs.

Pattern: Aggregation pattern
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_summary(file_metadata: list[dict], output_directory: str) -> dict:
    """
    Generate run_summary.json and validation_report.md.
    
    Args:
        file_metadata: List of per-file metadata dictionaries
        output_directory: Where to write summary files
        
    Returns:
        Dictionary with summary_path and report_path
    """
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate totals
    total_files = len(file_metadata)
    successful_files = len([f for f in file_metadata if not f.get('error')])
    failed_files = total_files - successful_files
    total_rows = sum(f.get('rows_written', 0) for f in file_metadata)
    total_time_ms = sum(f.get('processing_time_ms', 0) for f in file_metadata)
    
    # Build run_summary.json
    summary = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'files_processed': total_files,
        'successful': successful_files,
        'failed': failed_files,
        'total_rows': total_rows,
        'total_processing_time_ms': round(total_time_ms, 2),
        'files': file_metadata,
    }
    
    summary_path = output_dir / 'run_summary.json'
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    logger.info(f"Run summary saved to {summary_path}")
    
    # Build validation_report.md
    report_lines = []
    report_lines.append('# CSV-to-JSON Conversion Report\n')
    report_lines.append(f"**Generated:** {summary['timestamp']}\n")
    report_lines.append('---\n')
    
    # Overview
    report_lines.append('## Overview\n')
    report_lines.append(f"- **Files Processed:** {total_files}")
    report_lines.append(f"- **Successful:** {successful_files}")
    report_lines.append(f"- **Failed:** {failed_files}")
    report_lines.append(f"- **Total Rows:** {total_rows:,}")
    report_lines.append(f"- **Processing Time:** {total_time_ms:.1f}ms")
    report_lines.append('')
    
    # Per-file results
    report_lines.append('## File Results\n')
    for fm in file_metadata:
        input_file = fm.get('input', 'unknown')
        if fm.get('error'):
            report_lines.append(f"### ❌ {input_file}")
            report_lines.append(f"**Error:** {fm['error']}\n")
        else:
            report_lines.append(f"### ✓ {input_file}")
            report_lines.append(f"- **Output:** {fm.get('output', 'N/A')}")
            report_lines.append(f"- **Rows:** {fm.get('rows_written', 0):,}")
            report_lines.append(f"- **Columns:** {fm.get('column_count', 0)}")
            report_lines.append(f"- **Encoding:** {fm.get('encoding', 'N/A')}")
            report_lines.append(f"- **Processing Time:** {fm.get('processing_time_ms', 0):.1f}ms")
            report_lines.append('')
            
            # Type inference results
            if fm.get('inferred_types'):
                report_lines.append('**Inferred Types:**')
                for col, type_info in fm['inferred_types'].items():
                    confidence = type_info.get('confidence', 0)
                    col_type = type_info.get('type', 'string')
                    report_lines.append(f"- `{col}`: {col_type} (confidence: {confidence:.2f})")
                report_lines.append('')
            
            # Validation issues
            if fm.get('validation_issues'):
                issues = fm['validation_issues']
                if issues:
                    report_lines.append('**Validation Issues:**')
                    # Group by severity
                    errors = [i for i in issues if i.get('severity') == 'error']
                    warnings = [i for i in issues if i.get('severity') == 'warning']
                    infos = [i for i in issues if i.get('severity') == 'info']
                    
                    if errors:
                        report_lines.append(f"- Errors: {len(errors)}")
                    if warnings:
                        report_lines.append(f"- Warnings: {len(warnings)}")
                    if infos:
                        report_lines.append(f"- Info: {len(infos)}")
                    
                    # Show first 5 issues
                    report_lines.append('')
                    report_lines.append('**Top Issues:**')
                    for issue in issues[:5]:
                        row = issue.get('row', 'N/A')
                        col = issue.get('column', 'N/A')
                        msg = issue.get('issue', 'Unknown issue')
                        report_lines.append(f"- Row {row}, Column {col}: {msg}")
                    
                    if len(issues) > 5:
                        report_lines.append(f"- ... and {len(issues) - 5} more issues")
                    report_lines.append('')
    
    # Recommendations
    report_lines.append('## Recommendations\n')
    
    # Check for common issues across all files
    all_issues = []
    for fm in file_metadata:
        if fm.get('validation_issues'):
            all_issues.extend(fm['validation_issues'])
    
    if not all_issues:
        report_lines.append('✅ No validation issues detected. Data quality looks good!\n')
    else:
        issue_types = {}
        for issue in all_issues:
            issue_type = issue.get('issue', '').split(':')[0]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        report_lines.append('Common issues detected:')
        for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            report_lines.append(f"- **{issue_type}**: {count} occurrences")
        report_lines.append('')
        
        report_lines.append('**Suggested Actions:**')
        if any('Empty row' in str(i.get('issue')) for i in all_issues):
            report_lines.append('- Remove empty rows from source CSV files')
        if any('Duplicate' in str(i.get('issue')) for i in all_issues):
            report_lines.append('- Review and deduplicate source data')
        if any('Ragged' in str(i.get('issue')) for i in all_issues):
            report_lines.append('- Ensure all rows have consistent column counts')
        if any("doesn't match" in str(i.get('issue')) for i in all_issues):
            report_lines.append('- Review type conflicts and standardize data formats')
        report_lines.append('')
    
    report_path = output_dir / 'validation_report.md'
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')
    logger.info(f"Validation report saved to {report_path}")
    
    return {
        'summary_path': str(summary_path),
        'report_path': str(report_path),
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate run summary and validation report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s metadata.json output/
        """
    )
    parser.add_argument('metadata_file', help='JSON file with file metadata list')
    parser.add_argument('output_directory', help='Output directory for reports')
    
    args = parser.parse_args()
    
    try:
        # Read metadata
        metadata_path = Path(args.metadata_file)
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {args.metadata_file}")
        
        file_metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        
        if not isinstance(file_metadata, list):
            raise ValueError("Metadata must be a list of dictionaries")
        
        # Generate summary and report
        result = generate_summary(file_metadata, args.output_directory)
        
        # Print result
        print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
