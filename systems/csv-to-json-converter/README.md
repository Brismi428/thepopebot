# CSV-to-JSON Converter

A robust CSV-to-JSON/JSONL converter with intelligent type inference, header detection, validation, and batch processing capabilities.

## Features

- ✅ **Intelligent Type Inference** — Automatically detects integers, floats, booleans, dates, and strings
- ✅ **Encoding Detection** — Handles UTF-8, Latin-1, Windows-1252, and more
- ✅ **Delimiter Detection** — Auto-detects comma, semicolon, tab, and pipe delimiters
- ✅ **Header Detection** — Detects or generates column names (`col_0`, `col_1`, etc.)
- ✅ **Ragged Row Handling** — Gracefully pads or truncates inconsistent column counts
- ✅ **Comprehensive Validation** — Reports empty rows, duplicates, ragged rows, and type conflicts
- ✅ **Batch Processing** — Convert multiple CSV files in one run
- ✅ **Memory Efficient** — JSONL streaming for large files (1M+ rows)
- ✅ **Three Execution Paths** — CLI, GitHub Actions, or GitHub Agent HQ

## Quick Start

### Path 1: CLI (Local Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Convert a single file
python tools/converter.py data.csv

# Convert all CSVs in a directory
python tools/converter.py data/

# Convert with specific options
python tools/converter.py "data/*.csv" --output-format jsonl --strict
```

### Path 2: GitHub Actions (Production)

1. Push this repository to GitHub
2. Go to **Actions** tab
3. Select **"CSV to JSON Converter"** workflow
4. Click **"Run workflow"**
5. Fill in inputs:
   - `csv_files`: Path or glob pattern (e.g., `input/*.csv`)
   - `output_format`: `json` or `jsonl`
   - `output_directory`: Where to write results (e.g., `output/`)
   - `type_inference`: Enable intelligent type conversion
   - `strict_mode`: Halt on validation errors
6. Click **"Run workflow"**

Results are automatically committed to the repository.

### Path 3: GitHub Agent HQ (Issue-Driven)

1. Enable GitHub Agent HQ in your repository
2. Open a new issue
3. Assign to `@claude`
4. Issue body:
   ```
   Convert all CSV files in data/ to JSON format.
   - Output directory: output/
   - Format: json
   - Enable type inference
   ```
5. Agent processes autonomously and commits results

## CLI Usage

### Basic Commands

```bash
# Convert single file
python tools/converter.py data.csv

# Convert directory
python tools/converter.py data/

# Convert with glob pattern
python tools/converter.py "data/*.csv"

# Multiple files
python tools/converter.py file1.csv file2.csv file3.csv
```

### Options

```
--output-format {json,jsonl}
    Output format (default: json)
    - json: Standard JSON array with pretty-printing
    - jsonl: Newline-delimited JSON (one object per line)

--output-directory PATH
    Output directory (default: output/)
    Directory is created if missing

--type-inference / --no-type-inference
    Enable/disable intelligent type inference (default: enabled)
    When enabled, detects int, float, bool, datetime, string
    When disabled, all values remain strings

--strict
    Halt on validation errors (default: continue with warnings)
    Use for data quality enforcement
```

### Examples

```bash
# Convert to JSONL for large files
python tools/converter.py large_dataset.csv --output-format jsonl

# Disable type inference, keep all strings
python tools/converter.py data.csv --no-type-inference

# Strict validation mode
python tools/converter.py data.csv --strict

# Custom output directory
python tools/converter.py data/*.csv --output-directory converted/
```

## Outputs

### Converted Files

One output file per input CSV:
- `{output_directory}/{input_basename}.json` (JSON format)
- `{output_directory}/{input_basename}.jsonl` (JSONL format)

Each record is an object with column names as keys:

```json
[
  {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "active": true,
    "created": "2024-01-15T00:00:00",
    "score": 95.5
  }
]
```

### Metadata Reports

**run_summary.json** — JSON metadata:
```json
{
  "timestamp": "2026-02-11T11:30:00Z",
  "files_processed": 2,
  "successful": 2,
  "failed": 0,
  "total_rows": 1543,
  "total_processing_time_ms": 512,
  "files": [...]
}
```

**validation_report.md** — Human-readable report:
- Overview (files processed, success rate)
- Per-file results (rows, types, issues)
- Validation issues (grouped by severity)
- Recommendations for data cleanup

## Type Inference

The system intelligently detects and converts data types:

| Type | Examples | Output |
|------|----------|--------|
| **Integer** | `"1"`, `"42"`, `"-5"` | `1`, `42`, `-5` |
| **Float** | `"3.14"`, `"1.0"`, `"2.5e10"` | `3.14`, `1.0`, `2.5e10` |
| **Boolean** | `"true"`, `"yes"`, `"1"`, `"false"`, `"no"`, `"0"` | `true`, `false` |
| **Datetime** | `"2024-01-15"`, `"01/15/2024"` | `"2024-01-15T00:00:00"` |
| **String** | Anything else or low confidence | `"original value"` |

**Null values** (converted to JSON `null`):
- Empty string: `""`
- Common representations: `"N/A"`, `"null"`, `"NULL"`, `"None"`, `"-"`, `"nan"`

**Confidence threshold:** 80% of values must match a type. If confidence is below 80%, the column defaults to 'string' type to avoid data loss.

## Validation

The system checks for common data quality issues:

### Empty Rows
Rows where all values are empty or null. These are skipped but logged.

### Duplicate Rows
Rows with identical content (detected via hash). These are kept but flagged for awareness.

### Ragged Rows
Rows with inconsistent column counts:
- **Fewer columns than header** → Padded with `null`
- **More columns than header** → Truncated (with warning)

### Type Conflicts
Values that don't match the inferred type. These are:
- Converted to `null` if null-like
- Kept as string if conversion fails
- Logged in the validation report

## Batch Processing

### Sequential Mode (Default)

Processes files one at a time using specialist subagents:
```
File 1 → Analyze → Parse → Infer → Validate → Write
File 2 → Analyze → Parse → Infer → Validate → Write
File 3 → Analyze → Parse → Infer → Validate → Write
```

**Use when:**
- Processing 1-2 files
- Agent Teams is not available
- Simplicity is preferred

### Parallel Mode (Agent Teams)

Processes 3+ files concurrently:
```
Team Lead → Spawn Teammates → Merge Results
   ├─ Teammate 1: File 1 → Full Pipeline
   ├─ Teammate 2: File 2 → Full Pipeline
   └─ Teammate 3: File 3 → Full Pipeline
```

**Use when:**
- Processing 3+ files
- Faster wall-clock time is important
- Agent Teams is enabled

**Fallback:** Always falls back to sequential if parallel fails.

## Architecture

### Subagent Delegation

The system uses **specialist subagents** for each phase:

| Subagent | Responsibility |
|----------|----------------|
| `csv-analyzer` | Detect encoding, delimiter, headers |
| `type-inference-specialist` | Infer column types |
| `data-validator` | Check data quality |
| `json-writer` | Write JSON/JSONL output |

Subagents are Claude Code agents with specialized system prompts and limited tool access (principle of least privilege).

### Workflow Pattern

**Collect > Transform > Store**

1. **Collect:** Gather CSV files from input specification
2. **Transform:** Analyze → Parse → Infer Types → Validate → Convert
3. **Store:** Write JSON/JSONL and commit to repository

## Troubleshooting

### No CSV files found
- **Check:** Input path exists and is correct
- **Check:** Files have `.csv` extension
- **Check:** File permissions allow reading

### Encoding detection failed
- **Fallback:** Tool defaults to UTF-8
- **Solution:** Most CSV exports are UTF-8 compatible
- **If still broken:** File may be corrupt or binary

### Type conflicts
- **Check:** `validation_report.md` for details
- **If >20% conflicts:** Consider forcing column to 'string' type
- **Solution:** Clean source data or use `--no-type-inference`

### Validation failed in strict mode
- **Check:** `validation_report.md` for specific issues
- **Fix:** Clean source CSV and re-run
- **Alternative:** Run without `--strict` to get output with warnings

### Large file memory issues
- **Solution:** Use JSONL format (`--output-format jsonl`)
- **Reason:** JSONL streams records one at a time
- **Capacity:** Can handle multi-GB files with minimal memory

## Dependencies

- Python 3.11+
- `chardet>=5.2.0` — Encoding detection
- `python-dateutil>=2.8.2` — Date parsing

No external APIs or secrets required.

## License

This system is generated by the WAT Systems Factory.

## Support

For issues or questions:
1. Check `validation_report.md` for data quality issues
2. Check GitHub Actions logs for execution errors
3. Open an issue with:
   - Input CSV file characteristics (encoding, delimiter, row count)
   - Command used
   - Error message or unexpected output
