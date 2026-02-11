# CSV-to-JSON Converter Workflow

A robust CSV-to-JSON/JSONL converter with intelligent type inference, header detection, validation, and batch processing capabilities.

## Pattern
**Collect > Transform > Store**

---

## Inputs

| Input | Type | Source | Required | Default | Description |
|-------|------|--------|----------|---------|-------------|
| `csv_files` | `list[file_path]`, `directory_path`, or `glob_pattern` | CLI argument | Yes | - | One or more CSV files to convert. Can be individual paths, a directory, or a glob pattern (e.g., `data/*.csv`) |
| `output_format` | `string` (json or jsonl) | CLI flag or workflow_dispatch | No | json | Output format: 'json' for array-of-objects, 'jsonl' for newline-delimited JSON |
| `output_directory` | `string` (directory path) | CLI flag or workflow_dispatch | No | output/ | Where to write converted files. Directory is created if missing |
| `type_inference` | `boolean` | CLI flag | No | true | Enable intelligent type inference. If false, all values remain strings |
| `strict_mode` | `boolean` | CLI flag | No | false | If true, halt on any validation error. If false, log errors and continue |
| `header_row` | `integer` or 'auto' | CLI flag | No | auto | Which row contains headers (0-indexed). 'auto' detects automatically. -1 means no headers |

---

## Outputs

| Output | Format | Destination | Description |
|--------|--------|-------------|-------------|
| `converted_files` | JSON or JSONL | `{output_directory}/{input_basename}.{format}` | One output file per input CSV. Each record is an object with column names as keys |
| `run_summary.json` | JSON | `{output_directory}/run_summary.json` | Metadata report covering files processed, total rows, inferred types per column, validation issues, processing time, errors |
| `validation_report.md` | Markdown | `{output_directory}/validation_report.md` | Human-readable summary of validation issues, type inference results, and recommendations |

---

## Steps

### Step 1: Collect Input Files

**Responsibility:** Main agent

Parse the `csv_files` input parameter and build a list of CSV files to process.

1. Check if input is a single file path, directory, or glob pattern
2. For directories: find all `*.csv` files recursively (up to 2 levels deep)
3. For glob patterns: expand to matching file paths
4. Validate that at least one file exists and is readable
5. Return absolute file paths as a list

**Tools:** Python `pathlib` and `glob` modules

**Outputs:** `list[str]` of absolute file paths

**Failure modes:**
- No files found matching the input specification
- Invalid paths or permission errors
- Empty directory

**Fallback:**
- Log clear error message explaining what was searched and why no files were found
- Exit with code 1 if no valid files found

---

### Step 2: Decision -- Parallel or Sequential

**Responsibility:** Main agent

Determine execution strategy based on file count and Agent Teams availability.

1. Count the number of files to process
2. **If 3 or more files AND Agent Teams is enabled:**
   - Proceed to Step 3a (Parallel Processing with Agent Teams)
3. **Otherwise:**
   - Proceed to Step 3b (Sequential Processing)

**Outputs:** Execution path decision (parallel or sequential)

**Failure modes:**
- Agent Teams initialization fails

**Fallback:**
- Always fall back to sequential processing if parallel execution cannot be initialized

---

### Step 3a: Parallel Processing (Agent Teams)

**Responsibility:** Team Lead (main agent)

Process multiple CSV files in parallel using Agent Teams.

1. **Create shared task list:**
   - One task per CSV file
   - Each task includes: input file path, output format, output directory, configuration flags
2. **Spawn teammates:**
   - One teammate per file (up to 5 parallel)
   - Each teammate executes Step 3b (per-file pipeline) independently
3. **Collect results:**
   - Wait for all teammates to complete
   - Gather per-file metadata from each teammate
4. **Handle failures:**
   - If a teammate fails, collect partial results from successful teammates
   - Include error details in the aggregated metadata
5. **Proceed to Step 4** with collected metadata

**Tools:** Agent Teams coordination

**Outputs:** `list[dict]` of per-file metadata objects

**Failure modes:**
- Teammate fails to process a file
- Agent Teams coordination failure

**Fallback:**
- Fall back to Step 3b (sequential) if Agent Teams fails to initialize
- Continue with successful file results if some files fail

---

### Step 3b: Per-File Processing Pipeline

**Responsibility:** Main agent (sequential) or Teammate (parallel)

Execute the full conversion pipeline for a single CSV file.

This step is executed once per file, either sequentially by the main agent or in parallel by teammates.

#### Substep 3b.1: Analyze CSV Structure

**Delegate to:** `csv-analyzer` subagent

Detect file encoding, delimiter, quote character, header row, and column count.

1. Detect encoding using `chardet` library (sample first 100KB)
2. Detect CSV dialect using `csv.Sniffer` (delimiter, quote character)
3. Detect header row using `csv.Sniffer().has_header()` or use `header_row` parameter if specified
4. Read first 5 rows as sample
5. Return analysis result as JSON

**Tools:** `csv_analyzer.py`

**Inputs:** CSV file path

**Outputs:**
```json
{
  "encoding": "utf-8",
  "delimiter": ",",
  "quotechar": "\"",
  "header_row_index": 0,
  "column_count": 5,
  "column_names": ["id", "name", "email", "created", "active"],
  "sample_rows": [...]
}
```

**Failure modes:**
- Encoding detection fails
- No delimiter detected (malformed CSV)
- File is empty or unreadable

**Fallback:**
- Try UTF-8 encoding if `chardet` fails
- Default to comma delimiter if `Sniffer` fails
- Log warnings and return best-guess result
- Skip file and log error if completely unreadable

---

#### Substep 3b.2: Parse CSV

**Responsibility:** Main agent or Teammate (using `csv.DictReader`)

Read the CSV file using detected parameters and parse into a list of dictionaries.

1. Open file with detected encoding
2. Create `csv.DictReader` with detected delimiter and quote character
3. If header row detected: use first row as column names
4. If no header: generate column names `col_0`, `col_1`, etc.
5. Handle ragged rows:
   - Fewer columns than header → pad with `None`
   - More columns than header → truncate and log warning
6. Skip empty rows but log them
7. Return parsed data as list of dicts

**Tools:** Python `csv.DictReader` (stdlib)

**Inputs:** CSV file path, analysis result from 3b.1

**Outputs:** `list[dict]` where keys are column names

**Failure modes:**
- Ragged rows (inconsistent column counts)
- Missing headers
- Malformed CSV syntax

**Fallback:**
- Pad short rows with `None` values
- Truncate long rows and log warnings
- Generate column names if headers missing
- Log all issues for validation report

---

#### Substep 3b.3: Infer Types

**Delegate to:** `type-inference-specialist` subagent

Analyze each column to determine data types (int, float, boolean, datetime, string).

1. For each column, collect all non-null values
2. Test each value against type patterns:
   - **Integer:** Can parse with `int()`
   - **Float:** Can parse with `float()` but not `int()`
   - **Boolean:** Matches `true/false`, `yes/no`, `1/0`, `t/f`, `y/n` (case-insensitive)
   - **Datetime:** Can parse with `dateutil.parser.parse()`
   - **String:** Default fallback
3. Calculate confidence score (percentage of values matching type)
4. If confidence < 80%, default to string
5. Log type conflicts (values that don't match inferred type)
6. Handle null value representations: `''`, `'N/A'`, `'null'`, `'-'` → JSON `null`

**Tools:** `type_inferrer.py`

**Inputs:** Parsed data (list of dicts), column names

**Outputs:**
```json
{
  "column_name": {
    "type": "int|float|boolean|datetime|string",
    "confidence": 0.95,
    "conflicts": ["Row 42: 'N/A' treated as null"],
    "null_count": 12,
    "sample_values": ["1", "2", "3"]
  }
}
```

**Failure modes:**
- Ambiguous types (mixed int/string)
- All values are null

**Fallback:**
- Default to 'string' type when uncertain
- Log all conflicts in validation report
- Never fail -- always return a type map

---

#### Substep 3b.4: Validate Data

**Delegate to:** `data-validator` subagent

Check data quality and generate a detailed validation report.

1. **Detect empty rows:** All column values are empty or null
2. **Detect duplicate rows:** Hash full row content, track duplicates
3. **Detect ragged rows:** Column count doesn't match header count
4. **Detect type conflicts:** Values that don't match inferred types
5. **Calculate statistics:** Empty rows, duplicates, ragged rows, type conflicts
6. **Assign severity:** `info`, `warning`, or `error`
7. **Determine pass/fail:**
   - If `strict_mode=true` and any issues exist: `validation_passed=false`
   - Otherwise: `validation_passed=true`

**Tools:** `data_validator.py`

**Inputs:** Parsed data, type map, strict_mode flag

**Outputs:**
```json
{
  "issues": [
    {
      "row": 42,
      "column": "age",
      "issue": "Type conflict: expected int, got 'N/A'",
      "severity": "warning",
      "action": "Converted to null"
    }
  ],
  "stats": {
    "empty_rows": 3,
    "duplicate_rows": 7,
    "ragged_rows": 12,
    "type_conflicts": 5
  },
  "validation_passed": true
}
```

**Failure modes:**
- Validation errors in strict mode

**Fallback:**
- Never raise exceptions
- Collect all issues and return validation report
- If `strict_mode=true` and issues exist, halt the pipeline
- If `strict_mode=false`, log issues and continue

---

#### Substep 3b.5: Convert and Write

**Delegate to:** `json-writer` subagent

Apply type conversions and write JSON or JSONL output.

1. **Apply type conversions:**
   - Convert string values to inferred types (int, float, bool, datetime)
   - Handle missing values → JSON `null`
   - For datetime: convert to ISO8601 format
   - For boolean: convert to JSON `true`/`false`
2. **Write output:**
   - **JSON format:** Write as array of objects with 2-space indentation
   - **JSONL format:** Write one JSON object per line (streaming for large files)
3. **Generate metadata:**
   - Output file path
   - Rows written
   - File size in bytes
   - Processing time in milliseconds

**Tools:** `json_writer.py`

**Inputs:** Validated data, type map, output format, output path

**Outputs:**
```json
{
  "output_file": "output/customers.json",
  "rows_written": 1000,
  "file_size_bytes": 245800,
  "processing_time_ms": 134
}
```

**Failure modes:**
- Write permission error
- Disk full
- JSON serialization error (shouldn't happen after validation)

**Fallback:**
- Log error with clear message
- Skip this file and return error metadata
- Clean up partial writes

---

### Step 4: Aggregate Results

**Responsibility:** Main agent (or Team Lead if parallel)

Collect metadata from all processed files and generate summary reports.

1. **Merge per-file metadata:**
   - Combine all file metadata into a single list
   - Include both successful and failed files
2. **Calculate totals:**
   - Total files processed
   - Total rows converted
   - Total processing time
   - Total file size
3. **Generate `run_summary.json`:**
   - Timestamp
   - Files processed count
   - Per-file details (input, output, rows, validation issues)
   - Aggregate statistics
   - Error log for failed files
4. **Generate `validation_report.md`:**
   - Overview section (files processed, success rate)
   - Type inference results (per column, across all files)
   - Validation issues (grouped by severity)
   - Recommendations for data cleanup

**Tools:** `summary_generator.py`

**Inputs:** `list[dict]` of per-file metadata objects

**Outputs:** 
- `run_summary.json` file
- `validation_report.md` file

**Failure modes:**
- Metadata missing for some files

**Fallback:**
- Include partial results
- Note missing files in summary
- Generate report with available data

---

### Step 5: Commit Results

**Responsibility:** Main agent

Commit all output files to the repository with descriptive commit message.

1. Stage only the output files:
   - `{output_directory}/*.json`
   - `{output_directory}/*.jsonl`
   - `{output_directory}/run_summary.json`
   - `{output_directory}/validation_report.md`
2. Create commit with message:
   ```
   Convert {N} CSV files to {format}
   
   - Files processed: {N}
   - Total rows: {total_rows}
   - Output directory: {output_directory}
   - Timestamp: {timestamp}
   ```
3. Push commit to current branch

**Tools:** `git` CLI

**Inputs:** Output directory path, file count, row count

**Outputs:** Git commit SHA

**Failure modes:**
- Git push fails
- Branch protection rules prevent push
- No changes to commit (output directory unchanged)

**Fallback:**
- Log error with clear message
- Leave files uncommitted for manual review
- Return exit code 1 if commit/push fails

---

## Summary

This workflow implements the **Collect > Transform > Store** pattern:

- **Collect:** Parse input specification and gather CSV files
- **Transform:** Analyze structure, parse CSV, infer types, validate data, convert to JSON
- **Store:** Write JSON/JSONL files and commit to repository

**Execution paths:**
1. **Sequential:** Process files one at a time using subagent delegation
2. **Parallel:** Process 3+ files concurrently using Agent Teams with teammates

Both paths produce identical output. Parallel execution is an optimization, not a requirement.

**Key features:**
- Intelligent type inference with confidence scoring
- Automatic encoding and delimiter detection
- Graceful handling of malformed/ragged rows
- Comprehensive validation reporting
- Streaming support for large files (JSONL)
- Full audit trail via Git commits
