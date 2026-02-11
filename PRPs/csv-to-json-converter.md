name: "csv-to-json-converter"
description: |
  A robust CSV-to-JSON/JSONL converter with intelligent type inference, header detection, 
  validation, and batch processing capabilities. Transforms one or more CSV files into 
  clean JSON/JSONL with comprehensive metadata and error reporting.

## Purpose
WAT System PRP (Product Requirements Prompt) — a structured blueprint that gives the factory enough context to build a complete, working system in one pass.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, references, and caveats
2. **Validation Loops**: Provide executable checks the factory can run at each gate
3. **Information Dense**: Use keywords and patterns from the WAT framework
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Follow all rules in CLAUDE.md

---

## Goal
Build a production-ready CSV-to-JSON converter that handles real-world CSV files with grace: ragged rows, missing headers, mixed types, encoding issues, and edge cases. The system must intelligently infer data types (strings, numbers, booleans, dates), detect headers automatically, validate data quality, and produce clean JSON/JSONL output with comprehensive metadata reports. Support batch processing of multiple CSVs in a single run with parallel processing when beneficial.

## Why
- **Manual conversion is error-prone**: Copy-paste into online converters loses type information and produces string-only output
- **Existing tools lack intelligence**: Most CSV parsers don't infer types, detect malformed rows, or provide actionable validation reports
- **Data pipeline dependency**: Many systems need clean JSON ingestion from legacy CSV exports
- **Audit trail requirement**: Teams need to know what was transformed, what failed, and why — metadata reporting is critical

## What
A WAT system that accepts one or more CSV files (via file paths, directory glob, or manual upload), analyzes structure and content, performs intelligent type inference across all columns, handles malformed/ragged rows gracefully, and outputs clean JSON or JSONL files with a comprehensive run summary reporting statistics, type mappings, validation issues, and processing metadata.

### Success Criteria
- [ ] Correctly infers types for common patterns: integers, floats, booleans (`true/false`, `yes/no`, `1/0`), ISO8601 dates, URLs, emails
- [ ] Detects headers automatically when present; handles headerless CSVs with generated column names (`col_0`, `col_1`, etc.)
- [ ] Handles ragged rows: fewer columns than header → pad with nulls; more columns than header → log warning and truncate or create overflow columns
- [ ] Processes multiple CSV files in a single run, outputting one JSON/JSONL per input file
- [ ] Produces `run_summary.json` with: file count, total rows processed, type inference results per column, validation issues, processing time
- [ ] Validates data quality: reports empty rows, duplicate rows (by hash), column consistency, encoding issues
- [ ] System runs autonomously via GitHub Actions on schedule or manual dispatch
- [ ] Results are committed back to repo with clear commit messages
- [ ] All three execution paths work: CLI (local development), GitHub Actions (production), Agent HQ (issue-driven)

---

## Inputs
CSV files and configuration options for format preference and validation rules.

```yaml
- name: "csv_files"
  type: "list[file_path] | directory_path | glob_pattern"
  source: "CLI argument, manual input, or directory scan"
  required: true
  description: "One or more CSV files to convert. Can be individual paths, a directory (converts all CSVs), or a glob pattern (e.g., data/*.csv)"
  example: "['input/customers.csv', 'input/orders.csv'] OR 'input/' OR 'data/*.csv'"

- name: "output_format"
  type: "string (json | jsonl)"
  source: "CLI flag or workflow_dispatch input"
  required: false
  default: "json"
  description: "Output format: 'json' for array-of-objects, 'jsonl' for newline-delimited JSON (one object per line)"
  example: "jsonl"

- name: "output_directory"
  type: "string (directory path)"
  source: "CLI flag or workflow_dispatch input"
  required: false
  default: "output/"
  description: "Where to write converted files. Directory is created if missing."
  example: "converted/"

- name: "type_inference"
  type: "boolean"
  source: "CLI flag"
  required: false
  default: true
  description: "Enable intelligent type inference. If false, all values remain strings."
  example: true

- name: "strict_mode"
  type: "boolean"
  source: "CLI flag"
  required: false
  default: false
  description: "If true, halt on any validation error. If false, log errors and continue."
  example: false

- name: "header_row"
  type: "integer | 'auto'"
  source: "CLI flag"
  required: false
  default: "auto"
  description: "Which row contains headers (0-indexed). 'auto' detects automatically. -1 means no headers (generate col_0, col_1, etc.)"
  example: 0
```

## Outputs
Converted JSON/JSONL files and a comprehensive run summary.

```yaml
- name: "converted_files"
  type: "JSON or JSONL files"
  destination: "{output_directory}/{input_basename}.json"
  description: "One output file per input CSV. Format matches output_format setting. Each record is an object with column names as keys."
  example: "output/customers.json containing [{\"id\": 1, \"name\": \"Alice\", \"active\": true}, ...]"

- name: "run_summary.json"
  type: "JSON"
  destination: "{output_directory}/run_summary.json"
  description: "Metadata report covering: files processed, total rows, inferred types per column, validation issues, processing time, errors encountered"
  example: |
    {
      "timestamp": "2026-02-11T11:30:00Z",
      "files_processed": 2,
      "total_rows": 1543,
      "files": [
        {
          "input": "input/customers.csv",
          "output": "output/customers.json",
          "rows": 1000,
          "columns": 5,
          "inferred_types": {"id": "int", "name": "string", "active": "boolean", "created": "datetime", "score": "float"},
          "validation_issues": [
            {"row": 42, "issue": "Ragged row: 4 columns (expected 5)", "action": "Padded with null"},
            {"row": 105, "issue": "Type inference conflict in 'score' column", "action": "Kept as string"}
          ],
          "encoding": "utf-8",
          "processing_time_ms": 245
        }
      ],
      "errors": [],
      "total_processing_time_ms": 512
    }

- name: "validation_report.md"
  type: "Markdown"
  destination: "{output_directory}/validation_report.md"
  description: "Human-readable summary of validation issues, type inference results, and recommendations for data cleanup"
  example: "Markdown report with sections: Overview, Type Inference Results, Validation Issues, Recommendations"
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://docs.python.org/3/library/csv.html"
  why: "Python csv module docs — DictReader for parsing, handling dialects, quote characters"

- url: "https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html"
  why: "Pandas read_csv parameters — reference for encoding detection, type inference patterns, handling malformed rows"

- file: "library/tool_catalog.md"
  why: "Check csv_read_write and json_read_write patterns for reusable code"

- doc: "config/mcp_registry.md"
  why: "Check filesystem MCP availability (optional — stdlib works fine)"

- doc: "library/patterns.md"
  why: "This matches 'Collect > Transform > Store' pattern — ingest CSVs, transform with validation, output JSON"
```

### Workflow Pattern Selection
```yaml
pattern: "Collect > Transform > Store"
rationale: |
  This system collects CSV files, transforms them (parse, infer types, validate, convert), 
  and stores the output (JSON/JSONL + metadata). The pattern fits perfectly:
  - Collect: Find and read CSV files
  - Transform: Parse, infer types, validate, handle edge cases
  - Store: Write JSON/JSONL, commit to repo with summary
modifications: |
  Add a validation gate between Transform and Store. If strict_mode=true and validation 
  fails, halt before writing output. Otherwise log issues and continue.
```

### MCP & Tool Requirements
```yaml
capabilities:
  - name: "Filesystem I/O"
    primary_mcp: "filesystem (optional)"
    alternative_mcp: "none"
    fallback: "Python pathlib and open() — stdlib is sufficient for this use case"
    secret_name: "none"

  - name: "CSV Parsing"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "Python csv.DictReader (stdlib) with custom type inference logic"
    secret_name: "none"

  - name: "JSON Writing"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "Python json module (stdlib) with streaming support for JSONL"
    secret_name: "none"

  - name: "Encoding Detection"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "chardet library (pip install chardet) for automatic encoding detection"
    secret_name: "none"

  - name: "Type Inference"
    primary_mcp: "none"
    alternative_mcp: "none"
    fallback: "Custom Python logic using regex patterns and stdlib parsers (int(), float(), dateutil.parser)"
    secret_name: "none"
```

### Known Gotchas & Constraints
```
# CRITICAL: CSV files may use different delimiters (comma, semicolon, tab) — must auto-detect using csv.Sniffer
# CRITICAL: CSV files may have BOM (byte order mark) — must strip before parsing to avoid "\ufeff" in first column name
# CRITICAL: Encoding can be UTF-8, Latin-1, Windows-1252, or others — use chardet for detection before parsing
# CRITICAL: Type inference must handle: empty strings, 'N/A', 'null', '-', as missing values (convert to JSON null)
# CRITICAL: Boolean inference: 'true'/'false', 'yes'/'no', '1'/'0', 't'/'f', 'y'/'n' (case-insensitive)
# CRITICAL: Date inference: ISO8601, US format (MM/DD/YYYY), European format (DD/MM/YYYY), timestamps (Unix epoch)
# CRITICAL: Ragged rows are common — fewer columns = pad with nulls, more columns = log warning and decide (truncate or keep as overflow)
# CRITICAL: Empty rows should be skipped but logged in validation report
# CRITICAL: Duplicate row detection should hash full row content, not just row number
# CRITICAL: Large files (1M+ rows) should stream processing — don't load entire file into memory
# CRITICAL: JSONL is more memory-efficient for large datasets — write one record at a time, no array wrapping
# CRITICAL: Secrets are NEVER hardcoded — not applicable for this system (no external APIs)
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
```

---

## System Design

### Subagent Architecture
This system uses specialist subagents for each major phase of the conversion pipeline.

```yaml
subagents:
  - name: "csv-analyzer"
    description: "Delegate when you need to analyze CSV structure: detect encoding, delimiter, header row, column count. Use for the initial analysis phase before parsing."
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Detect file encoding using chardet library"
      - "Detect CSV dialect (delimiter, quote character, line terminator) using csv.Sniffer"
      - "Detect header row (auto-detect or use user-specified row index)"
      - "Count columns and validate consistency across first 100 rows"
      - "Generate analysis report with detected parameters"
    inputs: "CSV file path"
    outputs: "JSON object with: encoding, delimiter, quotechar, header_row_index, column_count, sample_rows"

  - name: "type-inference-specialist"
    description: "Delegate when you need to infer data types for CSV columns. Use after parsing but before conversion. Analyzes all values in each column to determine the best type."
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Scan all values in each column to determine predominant type"
      - "Detect integers, floats, booleans, dates, URLs, emails, plain strings"
      - "Handle missing value representations (empty string, 'N/A', 'null', '-', etc.)"
      - "Resolve type conflicts (e.g., mostly integers but some strings → keep as string)"
      - "Generate type map with confidence scores"
    inputs: "Parsed CSV data as list of dicts"
    outputs: "Type map: {column_name: {type: str, confidence: float, conflicts: list}}"

  - name: "data-validator"
    description: "Delegate when you need to validate CSV data quality. Use after parsing and type inference. Checks for common issues and generates a detailed validation report."
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Detect and log empty rows"
      - "Detect and log duplicate rows (hash-based)"
      - "Detect and log ragged rows (column count mismatch)"
      - "Detect and log type inference conflicts"
      - "Validate required columns (if specified)"
      - "Generate validation report with actionable recommendations"
    inputs: "Parsed CSV data, type map, configuration"
    outputs: "Validation report: {issues: list[{row, column, issue, severity, action}], stats: {empty_rows, duplicates, ragged_rows}}"

  - name: "json-writer"
    description: "Delegate when you need to write JSON or JSONL output. Use after validation passes (or warnings logged). Handles streaming for large files."
    tools: "Write, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Apply inferred types to convert values (string to int/float/bool/datetime)"
      - "Handle missing values (convert to JSON null)"
      - "Write JSON (array of objects) or JSONL (one object per line)"
      - "Stream large files to avoid memory issues"
      - "Generate per-file metadata (row count, processing time, output size)"
    inputs: "Validated data, type map, output format, output path"
    outputs: "JSON/JSONL file + metadata object"
```

### Agent Teams Analysis
```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "Process file 1: analyze, parse, infer types, validate, write output"
  - "Process file 2: analyze, parse, infer types, validate, write output"
  - "Process file 3: analyze, parse, infer types, validate, write output"

independent_task_count: "N (one per input file)"
recommendation: "Use Agent Teams for multi-file batches (3+ files)"
rationale: |
  When processing 3 or more CSV files, each file can be processed independently 
  by a teammate. The team lead distributes file paths, teammates process in parallel, 
  then the team lead merges metadata into run_summary.json. For 1-2 files, sequential 
  execution is sufficient. Agent Teams is an optimization for batch jobs.

# Agent Teams structure (for 3+ files):
team_lead_responsibilities:
  - "Parse input: list of CSV file paths"
  - "Create shared task list: one task per CSV file"
  - "Spawn teammate for each file (up to 5 parallel teammates)"
  - "Collect individual file metadata as teammates complete"
  - "Merge metadata into run_summary.json"
  - "Generate validation_report.md from aggregated issues"
  - "Commit all outputs to repo"

teammates:
  - name: "File Processor"
    task: "Convert one CSV file to JSON/JSONL with full pipeline: analyze -> parse -> infer types -> validate -> write output"
    inputs: "CSV file path, output format, output directory, configuration"
    outputs: "JSON/JSONL file + metadata object (for run_summary)"

# Sequential fallback (for 1-2 files or if Agent Teams disabled):
sequential_rationale: |
  For single-file or two-file conversions, sequential execution is simpler and 
  avoids Agent Teams overhead. The main agent delegates to subagents for each phase 
  (analyzer, type inference, validator, writer) but processes files one at a time.
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "workflow_dispatch"
    config:
      inputs:
        csv_files:
          description: "CSV file paths (comma-separated) or directory path"
          required: true
          default: "input/"
        output_format:
          description: "Output format: json or jsonl"
          required: false
          default: "json"
        output_directory:
          description: "Output directory path"
          required: false
          default: "output/"
        type_inference:
          description: "Enable type inference (true/false)"
          required: false
          default: "true"
        strict_mode:
          description: "Halt on validation errors (true/false)"
          required: false
          default: "false"
    description: "Manual trigger via GitHub Actions UI — primary execution path for production use"

  - type: "schedule"
    config: "0 2 * * *  # Daily at 02:00 UTC"
    description: "Optional: scheduled conversion of files in a watched directory (e.g., daily batch processing)"

  - type: "repository_dispatch"
    config: "event_type: csv_convert_request"
    description: "Optional: webhook trigger for external systems to request conversions"
```

---

## Implementation Blueprint

### Workflow Steps
The workflow follows the Collect > Transform > Store pattern with validation gates.

```yaml
steps:
  - name: "1. Collect Input Files"
    description: "Parse input parameter (file paths, directory, or glob pattern) and build list of CSV files to process"
    subagent: "none (main agent)"
    tools: ["pathlib", "glob"]
    inputs: "csv_files parameter (string or list)"
    outputs: "List of absolute file paths: ['/path/to/file1.csv', '/path/to/file2.csv']"
    failure_mode: "No files found, invalid paths, permission errors"
    fallback: "Log error with clear message. Halt if no valid files found."

  - name: "2. Decision: Parallel or Sequential"
    description: "If 3+ files AND Agent Teams enabled: delegate to team. Otherwise: process sequentially with subagents."
    subagent: "none (main agent decision)"
    tools: []
    inputs: "File list length, Agent Teams availability"
    outputs: "Execution path decision"
    failure_mode: "Agent Teams fails to initialize"
    fallback: "Fall back to sequential processing"

  - name: "3. Per-File Processing Pipeline"
    description: "For each CSV file, run the full conversion pipeline. This step is executed once per file (sequentially or in parallel)."
    subagent: "multiple (csv-analyzer, type-inference-specialist, data-validator, json-writer)"
    tools: ["csv_analyzer.py", "type_inferrer.py", "data_validator.py", "json_writer.py"]
    inputs: "CSV file path, output format, output directory, configuration"
    outputs: "JSON/JSONL file + metadata object"
    failure_mode: "File unreadable, encoding detection fails, parsing fails, validation fails (strict mode)"
    fallback: "Log error, skip file if non-strict mode, include error in run_summary"

  - name: "3a. Analyze CSV Structure"
    description: "Detect encoding, delimiter, quote character, header row, column count"
    subagent: "csv-analyzer"
    tools: ["csv_analyzer.py"]
    inputs: "CSV file path"
    outputs: "Analysis result: {encoding, delimiter, quotechar, header_row, column_count, sample_rows}"
    failure_mode: "Encoding detection fails, no delimiter detected, file corrupted"
    fallback: "Try UTF-8 encoding, comma delimiter. If still fails, skip file and log error."

  - name: "3b. Parse CSV"
    description: "Read CSV using detected parameters, parse into list of dictionaries"
    subagent: "none (main agent using csv.DictReader)"
    tools: ["csv.DictReader"]
    inputs: "CSV file path, analysis result"
    outputs: "Parsed data: list[dict] where keys are column names"
    failure_mode: "Ragged rows, missing headers, malformed CSV"
    fallback: "Handle ragged rows (pad/truncate), generate headers if missing, log all issues"

  - name: "3c. Infer Types"
    description: "Analyze each column to determine data types (int, float, bool, datetime, string)"
    subagent: "type-inference-specialist"
    tools: ["type_inferrer.py"]
    inputs: "Parsed data (list of dicts)"
    outputs: "Type map: {column_name: {type, confidence, conflicts}}"
    failure_mode: "Ambiguous types, mixed types in column"
    fallback: "When unsure, default to string. Log conflicts in validation report."

  - name: "3d. Validate Data"
    description: "Check data quality: empty rows, duplicates, ragged rows, type conflicts"
    subagent: "data-validator"
    tools: ["data_validator.py"]
    inputs: "Parsed data, type map, configuration"
    outputs: "Validation report: {issues, stats}"
    failure_mode: "Validation errors in strict mode"
    fallback: "If strict_mode=false, log all issues and continue. If strict_mode=true, halt and report errors."

  - name: "3e. Convert and Write"
    description: "Apply type conversions, write JSON or JSONL output"
    subagent: "json-writer"
    tools: ["json_writer.py"]
    inputs: "Validated data, type map, output format, output path"
    outputs: "JSON/JSONL file + metadata"
    failure_mode: "Write permission error, disk full, JSON serialization error"
    fallback: "Log error, skip this file, include error in run_summary"

  - name: "4. Aggregate Results"
    description: "Collect metadata from all files, generate run_summary.json and validation_report.md"
    subagent: "none (main agent)"
    tools: ["summary_generator.py"]
    inputs: "List of per-file metadata objects"
    outputs: "run_summary.json, validation_report.md"
    failure_mode: "Metadata missing for some files"
    fallback: "Include partial results, note missing files in summary"

  - name: "5. Commit Results"
    description: "Commit all output files to the repository with descriptive commit message"
    subagent: "none (main agent)"
    tools: ["git"]
    inputs: "Output directory path"
    outputs: "Git commit SHA"
    failure_mode: "Git push fails, branch protection"
    fallback: "Log error, leave files uncommitted for manual review"
```

### Tool Specifications
These tools implement the per-file processing pipeline.

```yaml
tools:
  - name: "csv_analyzer.py"
    purpose: "Analyze CSV file structure: detect encoding, delimiter, header row, column count"
    catalog_pattern: "new (CSV analysis pattern)"
    inputs:
      - "file_path: str — Path to CSV file"
    outputs: |
      JSON: {
        "encoding": "utf-8",
        "delimiter": ",",
        "quotechar": "\"",
        "header_row_index": 0,
        "column_count": 5,
        "column_names": ["id", "name", "email", "created", "active"],
        "sample_rows": [...first 5 rows...]
      }
    dependencies: ["chardet"]
    mcp_used: "none"
    error_handling: "Try UTF-8 if chardet fails. Try comma delimiter if Sniffer fails. Log warnings, return best-guess result."

  - name: "type_inferrer.py"
    purpose: "Infer data types for each column by analyzing all values"
    catalog_pattern: "new (Type inference pattern)"
    inputs:
      - "data: list[dict] — Parsed CSV data"
      - "column_names: list[str] — Column names to analyze"
    outputs: |
      JSON: {
        "column_name": {
          "type": "int | float | boolean | datetime | string",
          "confidence": 0.95,
          "conflicts": ["Row 42: 'N/A' treated as null", "Row 105: Mixed int/string"],
          "null_count": 12,
          "sample_values": ["1", "2", "3"]
        }
      }
    dependencies: ["python-dateutil"]
    mcp_used: "none"
    error_handling: "Default to 'string' type when uncertain. Log all conflicts. Never fail — always return a type map."

  - name: "data_validator.py"
    purpose: "Validate data quality and generate detailed validation report"
    catalog_pattern: "new (Data validation pattern)"
    inputs:
      - "data: list[dict] — Parsed CSV data"
      - "type_map: dict — Inferred types"
      - "strict_mode: bool — Halt on errors if true"
    outputs: |
      JSON: {
        "issues": [
          {"row": 42, "column": "age", "issue": "Type conflict: expected int, got 'N/A'", "severity": "warning", "action": "Converted to null"},
          {"row": 105, "column": null, "issue": "Ragged row: 4 columns (expected 5)", "severity": "warning", "action": "Padded with null"}
        ],
        "stats": {
          "empty_rows": 3,
          "duplicate_rows": 7,
          "ragged_rows": 12,
          "type_conflicts": 5
        },
        "validation_passed": true
      }
    dependencies: []
    mcp_used: "none"
    error_handling: "Never raise exceptions. Collect all issues, return validation report. If strict_mode=true and issues exist, set validation_passed=false."

  - name: "json_writer.py"
    purpose: "Convert data to JSON/JSONL and write to output file"
    catalog_pattern: "Adapted from json_read_write (tool_catalog.md)"
    inputs:
      - "data: list[dict] — Validated data"
      - "type_map: dict — Type conversion instructions"
      - "output_path: str — Output file path"
      - "format: str — 'json' or 'jsonl'"
    outputs: |
      JSON: {
        "output_file": "output/customers.json",
        "rows_written": 1000,
        "file_size_bytes": 245800,
        "processing_time_ms": 134
      }
    dependencies: []
    mcp_used: "none"
    error_handling: "If write fails, raise exception with clear error message. Ensure partial writes are cleaned up."

  - name: "summary_generator.py"
    purpose: "Aggregate per-file metadata into run_summary.json and validation_report.md"
    catalog_pattern: "new (Aggregation pattern)"
    inputs:
      - "file_metadata: list[dict] — Metadata from each processed file"
      - "output_directory: str — Where to write summary files"
    outputs: |
      Files: run_summary.json, validation_report.md
      JSON metadata: {
        "summary_path": "output/run_summary.json",
        "report_path": "output/validation_report.md"
      }
    dependencies: []
    mcp_used: "none"
    error_handling: "If summary generation fails, write error log to output directory"

  - name: "converter.py"
    purpose: "Main orchestrator — coordinates the full conversion workflow"
    catalog_pattern: "new (Orchestrator pattern)"
    inputs:
      - "csv_files: str | list[str] — Input files/directory/glob"
      - "output_format: str — 'json' or 'jsonl'"
      - "output_directory: str — Output path"
      - "type_inference: bool — Enable type inference"
      - "strict_mode: bool — Halt on validation errors"
    outputs: "Exit code 0 on success, non-zero on failure. Prints summary to stdout."
    dependencies: ["all other tools"]
    mcp_used: "none"
    error_handling: "Catch all exceptions at top level. Log full traceback. Exit with non-zero code on fatal errors."
```

### Per-Tool Pseudocode

```python
# csv_analyzer.py
"""
Analyze CSV file structure and detect parameters.

PATTERN: File analysis with encoding detection
CRITICAL: Must handle BOM, various encodings, and malformed CSVs gracefully
"""
import chardet, csv, pathlib, logging

def detect_encoding(file_path: str) -> str:
    """Detect file encoding using chardet."""
    # Read first 100KB for detection
    with open(file_path, 'rb') as f:
        raw = f.read(100000)
    result = chardet.detect(raw)
    return result['encoding'] or 'utf-8'

def detect_csv_params(file_path: str, encoding: str) -> dict:
    """Detect CSV dialect (delimiter, quotechar) using csv.Sniffer."""
    with open(file_path, 'r', encoding=encoding) as f:
        sample = f.read(10000)
    try:
        dialect = csv.Sniffer().sniff(sample)
        return {
            'delimiter': dialect.delimiter,
            'quotechar': dialect.quotechar,
        }
    except csv.Error:
        # Default to comma-separated
        return {'delimiter': ',', 'quotechar': '"'}

def detect_header_row(file_path: str, encoding: str, delimiter: str) -> int:
    """Detect which row contains headers (or -1 if no headers)."""
    # Read first 5 rows
    with open(file_path, 'r', encoding=encoding) as f:
        reader = csv.reader(f, delimiter=delimiter)
        rows = [next(reader) for _ in range(5) if reader]
    
    # Heuristic: first row is header if:
    # - All values are non-numeric strings
    # - Subsequent rows have different patterns
    # Use csv.Sniffer().has_header() as baseline
    with open(file_path, 'r', encoding=encoding) as f:
        sample = f.read(10000)
    try:
        has_header = csv.Sniffer().has_header(sample)
        return 0 if has_header else -1
    except:
        return 0  # Assume headers by default

def main(file_path: str) -> dict:
    """Analyze CSV structure and return parameters."""
    try:
        encoding = detect_encoding(file_path)
        params = detect_csv_params(file_path, encoding)
        header_row = detect_header_row(file_path, encoding, params['delimiter'])
        
        # Read first few rows for sample
        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.reader(f, delimiter=params['delimiter'])
            sample_rows = [row for i, row in enumerate(reader) if i < 5]
        
        return {
            'encoding': encoding,
            'delimiter': params['delimiter'],
            'quotechar': params['quotechar'],
            'header_row_index': header_row,
            'column_count': len(sample_rows[0]) if sample_rows else 0,
            'column_names': sample_rows[0] if header_row == 0 else [f"col_{i}" for i in range(len(sample_rows[0]))],
            'sample_rows': sample_rows[1:] if header_row == 0 else sample_rows,
        }
    except Exception as e:
        logging.error(f"CSV analysis failed: {e}")
        raise

# type_inferrer.py
"""
Infer data types for CSV columns.

PATTERN: Statistical type inference with confidence scoring
CRITICAL: Must handle missing values, mixed types, and edge cases
"""
import re, logging
from datetime import datetime
from dateutil import parser as date_parser

NULL_VALUES = {'', 'N/A', 'null', 'NULL', 'None', '-', 'n/a', 'NA'}

def is_int(value: str) -> bool:
    """Check if value can be parsed as integer."""
    if value in NULL_VALUES:
        return False
    try:
        int(value)
        return True
    except:
        return False

def is_float(value: str) -> bool:
    """Check if value can be parsed as float."""
    if value in NULL_VALUES:
        return False
    try:
        float(value)
        return True
    except:
        return False

def is_boolean(value: str) -> bool:
    """Check if value is boolean-like."""
    return value.lower() in {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}

def is_datetime(value: str) -> bool:
    """Check if value can be parsed as datetime."""
    if value in NULL_VALUES:
        return False
    try:
        date_parser.parse(value)
        return True
    except:
        return False

def infer_column_type(values: list[str]) -> dict:
    """Infer type for a single column."""
    non_null = [v for v in values if v not in NULL_VALUES]
    total = len(values)
    null_count = total - len(non_null)
    
    if not non_null:
        return {'type': 'string', 'confidence': 1.0, 'conflicts': [], 'null_count': null_count}
    
    # Count type matches
    int_count = sum(is_int(v) for v in non_null)
    float_count = sum(is_float(v) for v in non_null)
    bool_count = sum(is_boolean(v) for v in non_null)
    datetime_count = sum(is_datetime(v) for v in non_null)
    
    # Determine best type with confidence
    type_scores = [
        ('boolean', bool_count / len(non_null)),
        ('int', int_count / len(non_null)),
        ('float', (float_count - int_count) / len(non_null)),  # floats that aren't ints
        ('datetime', datetime_count / len(non_null)),
    ]
    best_type, best_score = max(type_scores, key=lambda x: x[1])
    
    # Default to string if confidence is low
    if best_score < 0.8:
        best_type = 'string'
        best_score = 1.0
    
    # Log conflicts (values that don't match inferred type)
    conflicts = []
    for i, v in enumerate(values):
        if v in NULL_VALUES:
            continue
        type_check = {
            'int': is_int,
            'float': is_float,
            'boolean': is_boolean,
            'datetime': is_datetime,
        }.get(best_type, lambda x: True)
        
        if not type_check(v):
            conflicts.append(f"Row {i}: '{v}' doesn't match {best_type}")
    
    return {
        'type': best_type,
        'confidence': best_score,
        'conflicts': conflicts[:10],  # Limit to first 10 conflicts
        'null_count': null_count,
        'sample_values': non_null[:5],
    }

def main(data: list[dict], column_names: list[str]) -> dict:
    """Infer types for all columns."""
    try:
        type_map = {}
        for col in column_names:
            values = [row.get(col, '') for row in data]
            type_map[col] = infer_column_type(values)
        return type_map
    except Exception as e:
        logging.error(f"Type inference failed: {e}")
        raise

# data_validator.py
"""
Validate CSV data quality.

PATTERN: Comprehensive validation with actionable reporting
CRITICAL: Must never fail — always return validation report
"""
import hashlib, logging

def validate_data(data: list[dict], type_map: dict, strict_mode: bool) -> dict:
    """Validate parsed CSV data."""
    issues = []
    empty_rows = 0
    duplicates = 0
    ragged_rows = 0
    type_conflicts = 0
    
    # Detect duplicates (hash-based)
    seen_hashes = set()
    for i, row in enumerate(data):
        row_hash = hashlib.md5(str(sorted(row.items())).encode()).hexdigest()
        if row_hash in seen_hashes:
            duplicates += 1
            issues.append({
                'row': i,
                'column': None,
                'issue': 'Duplicate row',
                'severity': 'info',
                'action': 'Kept duplicate',
            })
        seen_hashes.add(row_hash)
        
        # Detect empty rows
        if all(v in {'', None} for v in row.values()):
            empty_rows += 1
            issues.append({
                'row': i,
                'column': None,
                'issue': 'Empty row',
                'severity': 'warning',
                'action': 'Row skipped',
            })
        
        # Detect ragged rows
        # (This would require knowing expected column count from analyzer)
        
        # Detect type conflicts
        for col, type_info in type_map.items():
            if type_info['conflicts']:
                type_conflicts += len(type_info['conflicts'])
    
    validation_passed = not (strict_mode and (issues or type_conflicts))
    
    return {
        'issues': issues,
        'stats': {
            'empty_rows': empty_rows,
            'duplicate_rows': duplicates,
            'ragged_rows': ragged_rows,
            'type_conflicts': type_conflicts,
        },
        'validation_passed': validation_passed,
    }

def main(data: list[dict], type_map: dict, strict_mode: bool) -> dict:
    """Run validation and return report."""
    try:
        return validate_data(data, type_map, strict_mode)
    except Exception as e:
        logging.error(f"Validation failed: {e}")
        # Never fail — return error in report
        return {
            'issues': [{'row': None, 'column': None, 'issue': str(e), 'severity': 'error', 'action': 'Validation incomplete'}],
            'stats': {},
            'validation_passed': False,
        }

# json_writer.py
"""
Write JSON or JSONL output with type conversion.

PATTERN: Adapted from json_read_write (tool_catalog.md)
CRITICAL: Stream large files, apply type conversions correctly
"""
import json, pathlib, time, logging

def convert_value(value: str, target_type: str):
    """Convert string value to target type."""
    NULL_VALUES = {'', 'N/A', 'null', 'NULL', 'None', '-', 'n/a', 'NA'}
    
    if value in NULL_VALUES:
        return None
    
    try:
        if target_type == 'int':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'boolean':
            return value.lower() in {'true', 'yes', '1', 't', 'y'}
        elif target_type == 'datetime':
            from dateutil import parser
            return parser.parse(value).isoformat()
        else:
            return value
    except:
        return value  # Keep as string if conversion fails

def write_json(data: list[dict], type_map: dict, output_path: str, format: str) -> dict:
    """Write JSON or JSONL with type conversions."""
    start = time.time()
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Apply type conversions
    converted_data = []
    for row in data:
        converted_row = {}
        for col, value in row.items():
            target_type = type_map.get(col, {}).get('type', 'string')
            converted_row[col] = convert_value(value, target_type)
        converted_data.append(converted_row)
    
    # Write output
    if format == 'jsonl':
        with output_path.open('w', encoding='utf-8') as f:
            for record in converted_data:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
    else:  # json
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(converted_data, f, indent=2, ensure_ascii=False)
    
    elapsed_ms = (time.time() - start) * 1000
    file_size = output_path.stat().st_size
    
    return {
        'output_file': str(output_path),
        'rows_written': len(converted_data),
        'file_size_bytes': file_size,
        'processing_time_ms': round(elapsed_ms, 2),
    }

def main(data: list[dict], type_map: dict, output_path: str, format: str) -> dict:
    """Main entry point."""
    try:
        return write_json(data, type_map, output_path, format)
    except Exception as e:
        logging.error(f"JSON writing failed: {e}")
        raise

# converter.py (main orchestrator)
"""
Main orchestrator for CSV-to-JSON conversion.

PATTERN: Orchestrator pattern — coordinates subagents and tools
CRITICAL: Handle all edge cases, provide clear error messages
"""
import sys, argparse, pathlib, glob, logging, json

def parse_args():
    parser = argparse.ArgumentParser(description='Convert CSV to JSON/JSONL')
    parser.add_argument('csv_files', help='CSV file(s), directory, or glob pattern')
    parser.add_argument('--output-format', choices=['json', 'jsonl'], default='json')
    parser.add_argument('--output-directory', default='output/')
    parser.add_argument('--type-inference', action='store_true', default=True)
    parser.add_argument('--strict-mode', action='store_true', default=False)
    return parser.parse_args()

def collect_files(input_spec: str) -> list[str]:
    """Collect CSV files from input specification."""
    path = pathlib.Path(input_spec)
    
    if path.is_file():
        return [str(path)]
    elif path.is_dir():
        return [str(f) for f in path.glob('*.csv')]
    else:
        # Treat as glob pattern
        return glob.glob(input_spec)

def main():
    """Main entry point."""
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    
    # Collect input files
    files = collect_files(args.csv_files)
    if not files:
        logging.error(f"No CSV files found: {args.csv_files}")
        sys.exit(1)
    
    logging.info(f"Found {len(files)} CSV file(s)")
    
    # Process each file
    file_metadata = []
    for file_path in files:
        try:
            # Delegate to subagents (or call tools directly)
            logging.info(f"Processing {file_path}...")
            
            # Analyze CSV structure (csv-analyzer subagent)
            analysis = csv_analyzer.main(file_path)
            
            # Parse CSV
            # ... (use csv.DictReader with analysis params)
            
            # Infer types (type-inference-specialist subagent)
            type_map = type_inferrer.main(parsed_data, analysis['column_names'])
            
            # Validate (data-validator subagent)
            validation = data_validator.main(parsed_data, type_map, args.strict_mode)
            if not validation['validation_passed']:
                logging.error(f"Validation failed for {file_path}")
                if args.strict_mode:
                    sys.exit(1)
            
            # Convert and write (json-writer subagent)
            output_path = pathlib.Path(args.output_directory) / f"{pathlib.Path(file_path).stem}.{args.output_format}"
            metadata = json_writer.main(parsed_data, type_map, str(output_path), args.output_format)
            
            file_metadata.append({
                'input': file_path,
                'output': str(output_path),
                **metadata,
                'validation': validation,
            })
            
        except Exception as e:
            logging.error(f"Failed to process {file_path}: {e}")
            file_metadata.append({
                'input': file_path,
                'error': str(e),
            })
    
    # Generate run summary
    summary_generator.main(file_metadata, args.output_directory)
    
    logging.info("Conversion complete")
    sys.exit(0)
```

### Integration Points
```yaml
SECRETS:
  # This system requires no external API secrets
  - name: "none"
    purpose: "This system uses only filesystem I/O and stdlib — no secrets required"
    required: false

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "# No environment variables required for basic operation"
      - "# Optional: LOG_LEVEL=INFO  # Logging verbosity"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "chardet>=5.2.0  # Encoding detection"
      - "python-dateutil>=2.8.2  # Date parsing for type inference"

GITHUB_ACTIONS:
  - trigger: "workflow_dispatch"
    config: |
      Manual trigger with inputs:
      - csv_files (required)
      - output_format (default: json)
      - output_directory (default: output/)
      - type_inference (default: true)
      - strict_mode (default: false)
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2

# Test csv_analyzer.py
python -c "import ast; ast.parse(open('tools/csv_analyzer.py').read())"
python -c "import sys; sys.path.insert(0, 'tools'); import csv_analyzer; assert callable(csv_analyzer.main)"

# Test type_inferrer.py
python -c "import ast; ast.parse(open('tools/type_inferrer.py').read())"
python -c "import sys; sys.path.insert(0, 'tools'); import type_inferrer; assert callable(type_inferrer.main)"

# Test data_validator.py
python -c "import ast; ast.parse(open('tools/data_validator.py').read())"
python -c "import sys; sys.path.insert(0, 'tools'); import data_validator; assert callable(data_validator.main)"

# Test json_writer.py
python -c "import ast; ast.parse(open('tools/json_writer.py').read())"
python -c "import sys; sys.path.insert(0, 'tools'); import json_writer; assert callable(json_writer.main)"

# Test summary_generator.py
python -c "import ast; ast.parse(open('tools/summary_generator.py').read())"
python -c "import sys; sys.path.insert(0, 'tools'); import summary_generator; assert callable(summary_generator.main)"

# Test converter.py (main orchestrator)
python -c "import ast; ast.parse(open('tools/converter.py').read())"
python tools/converter.py --help  # Verify argparse works

# Verify workflow.md exists and has required sections
grep -q "## Inputs" workflow.md
grep -q "## Outputs" workflow.md
grep -q "## Failure" workflow.md

# Verify CLAUDE.md documents all subagents
grep -q "csv-analyzer" CLAUDE.md
grep -q "type-inference-specialist" CLAUDE.md
grep -q "data-validator" CLAUDE.md
grep -q "json-writer" CLAUDE.md

# Verify subagent files exist and have valid frontmatter
python -c "import yaml; yaml.safe_load(open('.claude/agents/csv-analyzer.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/type-inference-specialist.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/data-validator.md').read().split('---')[1])"
python -c "import yaml; yaml.safe_load(open('.claude/agents/json-writer.md').read().split('---')[1])"

# Expected: All commands pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs

# Create test CSV
cat > /tmp/test.csv << 'EOF'
id,name,active,score,created
1,Alice,true,95.5,2024-01-15
2,Bob,false,87.2,2024-02-20
3,Charlie,yes,92.0,2024-03-10
EOF

# Test csv_analyzer.py
python tools/csv_analyzer.py /tmp/test.csv
# Expected: JSON with encoding=utf-8, delimiter=,, column_count=5

# Test type_inferrer.py with parsed data
python -c "
import csv, json
with open('/tmp/test.csv') as f:
    data = list(csv.DictReader(f))
# Mock: would call type_inferrer.main(data, ['id', 'name', 'active', 'score', 'created'])
# Expected: type_map with id=int, name=string, active=boolean, score=float, created=datetime
print('Type inferrer would process', len(data), 'rows')
"

# Test data_validator.py
# (Similar mock test with sample data)

# Test json_writer.py
# Create mock input and verify JSON output

# Test full pipeline
python tools/converter.py /tmp/test.csv --output-directory /tmp/output --output-format json
# Expected: /tmp/output/test.json created, /tmp/output/run_summary.json created

# Verify output structure
python -c "
import json
data = json.load(open('/tmp/output/test.json'))
assert len(data) == 3, 'Expected 3 records'
assert data[0]['id'] == 1, 'ID should be int'
assert data[0]['active'] == True, 'Active should be boolean'
print('✓ Output structure valid')
"

# Expected: All tests pass. If any tool fails, fix and re-run.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline

# Create multi-file test scenario
cat > /tmp/customers.csv << 'EOF'
id,name,email,active
1,Alice,alice@example.com,true
2,Bob,bob@example.com,false
EOF

cat > /tmp/orders.csv << 'EOF'
order_id,customer_id,amount,date
1001,1,150.00,2024-01-15
1002,2,200.50,2024-01-16
EOF

# Run converter on multiple files
python tools/converter.py /tmp/*.csv --output-directory /tmp/batch --output-format jsonl

# Verify both files were processed
ls /tmp/batch/customers.jsonl /tmp/batch/orders.jsonl /tmp/batch/run_summary.json

# Verify run_summary.json contains both files
python -c "
import json
summary = json.load(open('/tmp/batch/run_summary.json'))
assert summary['files_processed'] == 2, 'Expected 2 files processed'
assert len(summary['files']) == 2, 'Expected 2 file entries'
print('✓ Run summary valid')
"

# Verify workflow.md references match actual tools
grep -o 'csv_analyzer.py\|type_inferrer.py\|data_validator.py\|json_writer.py\|summary_generator.py' workflow.md | sort -u > /tmp/workflow_tools.txt
ls tools/*.py | xargs -n1 basename | grep -v '^__' | sort > /tmp/actual_tools.txt
diff /tmp/workflow_tools.txt /tmp/actual_tools.txt
# Expected: No differences

# Verify CLAUDE.md documents all tools
for tool in csv_analyzer type_inferrer data_validator json_writer summary_generator; do
  grep -q "$tool" CLAUDE.md || echo "ERROR: $tool not documented in CLAUDE.md"
done

# Verify no hardcoded secrets
grep -r 'sk-\|api_key=' tools/ && echo "ERROR: Hardcoded secret found" || echo "✓ No hardcoded secrets"

# Expected: All checks pass. Integration test complete.
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure, docstrings)
- [ ] All tools pass Level 2 (unit tests with sample CSV data)
- [ ] Pipeline passes Level 3 (multi-file batch processing end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, and execution paths
- [ ] .github/workflows/convert.yml has timeout-minutes and valid YAML
- [ ] .env.example lists all environment variables (none required for basic operation)
- [ ] .gitignore excludes .env, __pycache__/, *.pyc, output/, .DS_Store
- [ ] README.md covers all three execution paths (CLI, GitHub Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase (verified via grep)
- [ ] Subagent files (.claude/agents/*.md) have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies (chardet, python-dateutil)
- [ ] All cross-references valid: workflow.md tools exist, CLAUDE.md subagents exist
- [ ] Error handling in every tool: try/except with logging, meaningful error messages
- [ ] Type hints in all tool functions

---

## Anti-Patterns to Avoid
- Do not hardcode file paths — use CLI arguments and configuration
- Do not use `git add -A` or `git add .` — stage only specific output files
- Do not skip validation levels — run 1, then 2, then 3 in order
- Do not catch bare `except:` — always catch specific exception types or Exception with logging
- Do not load entire large CSVs into memory — stream processing for 1M+ row files
- Do not fail silently — every tool should log errors and exit with non-zero code on failure
- Do not ignore encoding issues — always detect encoding before parsing
- Do not assume headers exist — handle headerless CSVs with generated column names
- Do not ignore ragged rows — pad or truncate and log the issue
- Do not default to string types without attempting inference — type inference is a core feature
- Do not write partial output files on error — clean up failed writes
- Do not commit broken tools — all three validation levels must pass before packaging

---

## Confidence Score: 9/10

**Score rationale:**
- **Requirements clarity**: HIGH — CSV-to-JSON conversion is well-defined, all edge cases documented
- **Technical feasibility**: HIGH — Python stdlib + 2 dependencies (chardet, python-dateutil) are sufficient, no complex MCPs needed
- **Pattern fit**: HIGH — Collect > Transform > Store pattern is perfect for this use case
- **Subagent design**: HIGH — Four clear specialist subagents (analyzer, type-inferrer, validator, writer) with non-overlapping responsibilities
- **Agent Teams applicability**: MEDIUM — Useful for batch processing 3+ files, but sequential fallback is straightforward
- **Validation approach**: HIGH — Three-level validation is well-defined with executable tests
- **Edge case handling**: HIGH — Encoding, ragged rows, missing headers, type conflicts all covered
- **Testing feasibility**: HIGH — Can test with sample CSVs, no external API dependencies

**Ambiguity flags** (areas requiring clarification before building):
- [ ] None — requirements are complete and unambiguous

**Confidence deduction reasons:**
- **-1 point**: Agent Teams parallelization benefit depends on file count and size — may not be worth the complexity for typical use cases (1-5 files). The sequential fallback is always available, so this is low risk.

**This PRP is ready to build. No clarifications needed.**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```bash
# From the repository root:
claude --agent factory/workflow.md --input-file PRPs/csv-to-json-converter.md

# Or use the slash command:
/execute-prp PRPs/csv-to-json-converter.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input, generating a complete WAT system in `systems/csv-to-json-converter/`.
