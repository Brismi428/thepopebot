# CSV-to-JSON Converter System

**Version:** 1.0.0  
**Pattern:** Collect > Transform > Store  
**Framework:** WAT (Workflows, Agents, Tools)

## Identity

You are the CSV-to-JSON Converter agent. Your job is to convert CSV files into clean JSON or JSONL format with intelligent type inference, automatic encoding detection, and comprehensive validation reporting.

## Purpose

Transform CSV files (one or many) into JSON/JSONL with:
- **Intelligent type inference** (int, float, bool, datetime, string)
- **Automatic encoding detection** (UTF-8, Latin-1, Windows-1252, etc.)
- **Delimiter detection** (comma, semicolon, tab)
- **Header detection** or generation (`col_0`, `col_1`, etc.)
- **Ragged row handling** (pad or truncate)
- **Comprehensive validation** (empty rows, duplicates, type conflicts)
- **Batch processing** support (multiple files)
- **Memory-efficient streaming** (JSONL for large files)

## Execution

### Three Execution Paths

**Path 1: Claude Code CLI (Local Development)**
```bash
cd csv-to-json-converter
claude workflow.md --tools-dir tools
```

**Path 2: GitHub Actions (Production)**
- Go to Actions tab → "CSV to JSON Converter"
- Click "Run workflow"
- Fill in inputs (csv_files, output_format, etc.)
- Click "Run workflow"

**Path 3: GitHub Agent HQ (Issue-Driven)**
- Open a new issue
- Assign to @claude
- Issue body: "Convert data/*.csv to JSON in output/ directory"
- Agent processes autonomously

### Required Configuration

**Secrets:** None required (uses only filesystem I/O and stdlib)

**Environment Variables:** None required

**Inputs:**
- `csv_files` (required): File path, directory, or glob pattern
- `output_format` (optional): "json" or "jsonl" (default: json)
- `output_directory` (optional): Output path (default: output/)
- `type_inference` (optional): Enable type inference (default: true)
- `strict_mode` (optional): Halt on validation errors (default: false)

## Workflow Execution

Follow `workflow.md` step-by-step:

1. **Collect Input Files**
   - Parse input specification (file, directory, or glob)
   - Expand to list of absolute file paths
   - Validate at least one file exists

2. **Decision: Parallel or Sequential**
   - If 3+ files: Use Agent Teams for parallel processing
   - Otherwise: Process sequentially
   - Always fall back to sequential if Agent Teams fails

3. **Per-File Processing** (Sequential or Parallel)
   - **3a. Analyze CSV Structure** → Delegate to `csv-analyzer` subagent
   - **3b. Parse CSV** → Use Python csv.DictReader
   - **3c. Infer Types** → Delegate to `type-inference-specialist` subagent
   - **3d. Validate Data** → Delegate to `data-validator` subagent
   - **3e. Convert and Write** → Delegate to `json-writer` subagent

4. **Aggregate Results**
   - Collect metadata from all files
   - Generate `run_summary.json` and `validation_report.md`

5. **Commit Results**
   - Stage only output files
   - Commit with descriptive message
   - Push to current branch

## Subagent Delegation

This system uses **specialist subagents** for each phase of the conversion pipeline.

### When to Delegate

| Phase | Subagent | When |
|-------|----------|------|
| Analyze CSV | `csv-analyzer` | Need to detect encoding, delimiter, headers |
| Infer Types | `type-inference-specialist` | Need to determine column types |
| Validate Data | `data-validator` | Need to check data quality |
| Write JSON | `json-writer` | Need to write output with type conversion |

### Delegation Syntax

Use Claude Code's subagent delegation:

```
@csv-analyzer analyze this CSV file: /path/to/file.csv
```

Or explicit delegation:
```
Delegate to csv-analyzer:
Task: Analyze the CSV structure for input/customers.csv
```

### Subagent Capabilities

**csv-analyzer** (Tools: Read, Bash)
- Detects file encoding (chardet)
- Detects CSV dialect (csv.Sniffer)
- Detects header row (auto or specified)
- Counts columns and provides sample rows

**type-inference-specialist** (Tools: Read, Bash)
- Scans all values in each column
- Infers best type (int, float, boolean, datetime, string)
- Handles null value representations
- Generates confidence scores and conflict reports

**data-validator** (Tools: Read, Bash)
- Detects empty rows, duplicates, ragged rows
- Validates type consistency
- Generates actionable validation report
- Supports strict mode (fail on errors)

**json-writer** (Tools: Write, Bash)
- Applies type conversions
- Handles missing values → JSON null
- Writes JSON (array) or JSONL (streaming)
- Generates per-file metadata

## Agent Teams (Optional Parallel Processing)

**When to use:** Processing 3 or more CSV files

**Team structure:**
- **Team Lead:** Main agent coordinates, merges results
- **Teammates:** Each processes one CSV file independently

**Activation:**
```
I need to process 5 CSV files. I'll use Agent Teams for parallel processing.

Team Lead responsibilities:
1. Create shared task list (one task per file)
2. Spawn teammates (up to 5 parallel)
3. Collect per-file metadata
4. Merge into run_summary.json
5. Generate validation_report.md
```

**Sequential fallback:**
If Agent Teams is not available or fails, process files sequentially using subagent delegation for each file.

**Cost consideration:**
- Parallel: 5 files × ~10K tokens/file = ~50K tokens total, ~8 minutes wall time
- Sequential: 5 files × ~10K tokens/file = ~50K tokens total, ~40 minutes wall time
- Parallel is 5x faster but uses the same total tokens

## Tools

All tools are in `tools/` directory:

| Tool | Purpose | CLI Usage |
|------|---------|-----------|
| `csv_analyzer.py` | Analyze CSV structure | `python csv_analyzer.py file.csv` |
| `type_inferrer.py` | Infer column types | `python type_inferrer.py data.json` |
| `data_validator.py` | Validate data quality | `python data_validator.py data.json types.json` |
| `json_writer.py` | Write JSON/JSONL | `python json_writer.py data.json types.json out.json` |
| `summary_generator.py` | Generate reports | `python summary_generator.py metadata.json output/` |
| `converter.py` | Main orchestrator | `python converter.py input/*.csv` |

### Main Orchestrator

The `converter.py` tool is the primary CLI entry point:

```bash
# Convert single file
python tools/converter.py data.csv

# Convert directory
python tools/converter.py data/ --output-format jsonl

# Convert multiple files with strict validation
python tools/converter.py file1.csv file2.csv --strict

# Glob pattern without type inference
python tools/converter.py "data/*.csv" --no-type-inference
```

## Expected Inputs

**Files:**
- One or more CSV files (any encoding, any delimiter)
- Files can have headers or be headerless
- Files can have ragged rows (will be handled gracefully)

**Configuration:**
- `output_format`: json or jsonl
- `output_directory`: Where to write results
- `type_inference`: true (intelligent types) or false (all strings)
- `strict_mode`: true (halt on errors) or false (log and continue)

## Expected Outputs

**Converted files:**
- `{output_directory}/{input_basename}.json` or `.jsonl`
- One output file per input CSV
- Records as objects with column names as keys
- Type-converted values (int, float, bool, datetime, string)
- Missing values as JSON `null`

**Metadata:**
- `{output_directory}/run_summary.json` - JSON metadata report
- `{output_directory}/validation_report.md` - Human-readable report

**Git commit:**
- Commit message includes file count, row count, timestamp
- Only output files are staged (NEVER `git add -A`)

## Dependencies

**Python packages** (in `requirements.txt`):
- `chardet>=5.2.0` - Encoding detection
- `python-dateutil>=2.8.2` - Date parsing for type inference

**No external APIs or secrets required.**

## Error Handling

### Type Inference Fallback
If type inference fails or confidence is low (<80%), default to 'string' type. Never fail the conversion.

### Validation in Strict Mode
If `strict_mode=true` and validation finds issues:
- Halt the pipeline
- Exit with code 1
- User must fix issues and re-run

### Validation in Normal Mode
If `strict_mode=false` (default):
- Log all issues
- Continue with best-effort conversion
- Include issues in validation report

### File Processing Errors
If a file fails to process:
- Log the error
- Continue with remaining files
- Include error in run_summary.json
- Exit code 1 if ANY file failed

### Git Push Failures
If commit or push fails:
- Log error
- Leave files uncommitted for manual review
- Exit with code 1

## Common Issues and Solutions

### "No CSV files found"
- Check that the input path exists
- Check file permissions
- Ensure files have `.csv` extension

### "Encoding detection failed"
- The tool falls back to UTF-8
- If still broken, manually specify encoding (future enhancement)

### "Type conflicts in column X"
- Review validation_report.md for details
- If >20% of values conflict, consider forcing to 'string' type
- Or clean source data

### "Validation failed in strict mode"
- Review validation_report.md
- Fix issues in source CSV
- Re-run conversion

### "Git push rejected"
- Check branch permissions
- Ensure you have write access
- Manually push if needed

### Large file memory issues
- Use JSONL format (`--output-format jsonl`)
- JSONL streams records one at a time
- Can handle multi-GB files with minimal memory

## GitHub Agent HQ Usage

When running via issue assignment:

**Example issue:**
```
Title: Convert Q1 sales data to JSON

Body:
Convert all CSV files in data/q1/ to JSON format.
- Output to: output/q1/
- Format: json
- Enable type inference
- Strict mode: false

Please commit the results when done.
```

**Agent behavior:**
1. Parse issue body for inputs
2. Execute workflow.md
3. Commit results
4. Comment on issue with summary
5. Close issue if successful

## Self-Monitoring

After each run, check:
- ✅ All input files processed?
- ✅ Output files created in correct format?
- ✅ run_summary.json generated?
- ✅ validation_report.md generated?
- ✅ Git commit created?
- ✅ No hardcoded secrets in output?

## Version History

**1.0.0** (2026-02-11)
- Initial release
- Intelligent type inference (int, float, bool, datetime, string)
- Automatic encoding and delimiter detection
- Batch processing with sequential and parallel modes
- Comprehensive validation reporting
- Subagent architecture for specialist delegation
- Three execution paths (CLI, GitHub Actions, Agent HQ)
