# Invoice Generator Workflow

**System:** invoice-generator
**Purpose:** Transform JSON invoice data into professional PDF invoices with automatic numbering, tax calculation, and configurable branding

---

## Inputs

- **invoice_data** -- JSON file containing invoice details (client info, line items, dates, payment terms)
  - Source: File path or workflow dispatch input
  - Format: JSON (see config/invoice_example.json for schema)
  - Required fields: client_name, project_description, invoice_date, due_date, line_items

- **config** -- Company branding and tax settings
  - Source: config/invoice_config.json
  - Optional: System provides defaults if missing

- **counter_state** -- Sequential invoice numbering state
  - Source: state/invoice_counter.json
  - Auto-initialized to 1000 if missing

## Outputs

- **invoice_pdf** -- Professional PDF invoice
  - Destination: output/{client-slug}-{YYYY-MM-DD}-{invoice-number}.pdf
  - Format: PDF with branding, itemized table, calculations, payment instructions

- **updated_counter** -- Incremented invoice counter
  - Destination: state/invoice_counter.json (overwrite)
  - Format: JSON with last_invoice_number, prefix, padding

- **audit_log** -- Invoice generation history
  - Destination: logs/invoice_log.jsonl (append-only)
  - Format: JSONL with timestamp, invoice_number, client, total, pdf_path

---

## Step 1: Parse and Validate Input

**Delegate to:** invoice-parser-specialist

Read JSON invoice data from the input source, validate all required fields and business rules, normalize client name for filename generation.

### Actions

1. Load invoice JSON from input file path or stdin
2. Validate against JSON schema:
   - Required fields: client_name, project_description, invoice_date, due_date, line_items
   - Line items must have: description, quantity > 0, rate >= 0
3. Parse dates and validate business rule: due_date >= invoice_date
4. Slugify client_name for safe filename generation
5. Return validated invoice data with client_slug field

### Tool

```bash
python tools/parse_invoice_input.py <input_path>
```

### Success Criteria

- JSON parses correctly
- All required fields present
- Date formats valid (ISO 8601 or parseable)
- due_date >= invoice_date
- All quantities > 0
- All rates >= 0
- client_slug generated successfully

### Failure Mode

**Missing required field or validation error**

- Log specific validation failure with field name and error message
- Exit with code 1 and clear error message
- DO NOT proceed to invoice generation with incomplete data

**Fallback:** None -- validation must pass for the system to continue

---

## Step 2: Load Configuration

**Delegate to:** Main agent (simple file read)

Read company branding and tax settings from config/invoice_config.json. Use sensible defaults for any missing fields.

### Actions

1. Load config/invoice_config.json
2. Merge with default config for any missing fields:
   - company_name: "Your Company LLC"
   - tax_rate: 0.0
   - currency: "USD"
   - currency_symbol: "$"
3. Return complete config dict

### Tool

```bash
python tools/load_config.py config/invoice_config.json
```

### Success Criteria

- Config loaded (or defaults used)
- All required config fields present after merge

### Failure Mode

**Missing or malformed config file**

- Log warning but continue with defaults
- DO NOT fail invoice generation due to config issues

**Fallback:** Use DEFAULT_CONFIG from load_config.py

---

## Step 3: Get Next Invoice Number

**Delegate to:** counter-manager-specialist

Atomically increment the invoice counter and return the next formatted invoice number.

### Actions

1. Acquire file lock on state/invoice_counter.json
2. Read current counter value (or initialize to 1000 if missing)
3. Increment counter
4. Write updated counter to file
5. Release lock
6. Format invoice number: {prefix}{number:0{padding}d}
7. Return invoice_number and numeric value

### Tool

```bash
python tools/manage_counter.py state/invoice_counter.json get_next
```

### Success Criteria

- Lock acquired within 5 seconds
- Counter incremented
- File written successfully
- Formatted invoice number returned (e.g., "INV-1043")

### Failure Mode

**File lock timeout after 5 seconds**

- Log warning about lock failure
- Use timestamp-based fallback: "INV-{unix_timestamp}"
- Continue with fallback number (degraded but functional)

**File lock timeout indicates:** Concurrent invoice generation or filesystem issue

**Fallback:** Timestamp-based invoice number (ensures uniqueness but breaks sequential numbering)

**File missing or corrupted**

- Initialize counter to 1000
- Log warning but continue

---

## Step 4: Generate PDF Invoice

**Delegate to:** pdf-generator-specialist

Create a professional PDF invoice using ReportLab with company branding, itemized line items table, tax calculations, and payment instructions.

### Actions

1. Load validated invoice data from Step 1
2. Load config from Step 2
3. Receive invoice number from Step 3
4. Render PDF with:
   - Company branding (logo if available, name, address, contact)
   - Invoice metadata (number, dates, client info)
   - Project description
   - Itemized line items table (description, quantity, rate, amount)
   - Subtotal calculation (sum of all line items)
   - Tax calculation (subtotal × tax_rate)
   - Total (subtotal + tax)
   - Payment terms and methods
   - Notes (if present)
5. Return PDF bytes

### Tool

```bash
python tools/generate_invoice_pdf.py \
  --invoice-data <validated_data_path> \
  --invoice-number <invoice_number> \
  --config <config_path> \
  --output <temp_pdf_path>
```

### Success Criteria

- PDF file created
- File size > 5KB (sanity check)
- All required sections rendered

### Failure Mode

**Missing company logo file**

- Log warning
- Skip logo rendering
- Continue with text-only branding

**ReportLab rendering error**

- Log full error and traceback
- Exit with code 1
- DO NOT create empty or corrupted PDF

**Font loading failure**

- Fall back to built-in Helvetica font
- Log warning but continue

**Fallback:** Skip logo and use built-in fonts for degraded output

---

## Step 5: Save Invoice and Update Logs

**Delegate to:** output-handler-specialist

Write the PDF to the output directory with a standardized filename and append an audit log entry.

### Actions

1. Read PDF bytes from Step 4
2. Generate filename: {client-slug}-{invoice_date}-{invoice_number}.pdf
3. Create output/ directory if it doesn't exist
4. Write PDF to output/{filename}
5. Append audit log entry to logs/invoice_log.jsonl:
   - timestamp (ISO 8601 UTC)
   - invoice_number
   - client (name)
   - total (amount)
   - pdf_path (relative)
6. Return final PDF path

### Tool

```bash
python tools/save_invoice.py \
  --pdf-path <temp_pdf_path> \
  --client-name "<client_name>" \
  --invoice-date <YYYY-MM-DD> \
  --invoice-number <invoice_number> \
  --total <total_amount>
```

### Success Criteria

- PDF written to output/
- Filename follows convention
- Audit log entry appended

### Failure Mode

**Output directory creation fails**

- Log error with filesystem details
- Attempt to save to /tmp/ as fallback
- Continue if fallback succeeds

**Disk full or permissions error**

- Log error
- Exit with code 1
- Invoice counter HAS been incremented (will skip this number)

**Audit log write fails**

- Log warning
- Continue (audit log is best-effort)
- Invoice is still saved successfully

**Fallback:** Save to /tmp/ if output/ write fails; skip audit log if logging fails

---

## Execution Summary

The workflow executes sequentially (no parallelization):

1. **Parse & Validate** → validated invoice data
2. **Load Config** → config dict
3. **Get Invoice Number** → "INV-1043"
4. **Generate PDF** → PDF bytes
5. **Save & Log** → output/client-slug-2026-02-11-INV-1043.pdf

Each step depends on the previous step's output, making sequential execution the correct approach.

**Total execution time:** 2-5 seconds (dominated by PDF generation)

---

## Error Handling Philosophy

- **Validation errors:** Fail fast with clear messages (Step 1)
- **Config errors:** Use defaults, continue (Step 2)
- **Counter errors:** Use timestamp fallback, continue (Step 3)
- **PDF errors:** Degrade gracefully (skip logo), or fail if critical (Step 4)
- **Save errors:** Try fallback location, skip audit if needed (Step 5)

**Never generate an invoice with invalid data.** Better to fail with an error than produce an incorrect invoice.
