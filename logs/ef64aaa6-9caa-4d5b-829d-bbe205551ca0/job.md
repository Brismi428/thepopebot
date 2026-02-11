Read the WAT factory instructions in CLAUDE.md and factory/workflow.md.

Generate a PRP (Product Requirements Prompt) for a system called "csv-to-json-converter".

Problem description:
Build a csv-to-json-converter system. It should convert one or more CSV files to JSON or JSONL format with type inference, header detection, and validation. Support multiple CSVs per run, handle ragged rows gracefully, and produce a run_summary.json with metadata. Three execution paths: CLI, GitHub Actions manual dispatch, and Agent HQ.

System requirements:
- Inputs: CSV files (one or more per run), format preference (JSON or JSONL), configuration options
- Outputs: Converted JSON/JSONL files, run_summary.json with metadata and statistics, validation reports
- Execution paths: CLI tool, GitHub Actions manual dispatch workflow, Agent HQ integration
- Key features: Automatic type inference (strings, numbers, booleans, dates), smart header detection, graceful handling of ragged/malformed rows, batch processing support, comprehensive error reporting

Follow the PRP generation process:
1. Read library/patterns.md and library/tool_catalog.md for reusable patterns
2. Read config/mcp_registry.md for available MCPs
3. Read PRPs/templates/prp_base.md for the PRP template
4. Generate the PRP and save it to PRPs/csv-to-json-converter.md
5. Log the confidence score and any ambiguity flags

After generating the PRP, report what was created.