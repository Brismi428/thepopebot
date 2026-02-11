name: "invoice-generator"
description: |
  Professional invoice generator that transforms JSON input into PDF invoices with automatic numbering,
  tax calculation, and configurable branding.

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
Build an on-demand invoice generator that takes JSON file input and produces professional PDF invoices with automatic sequential numbering, itemized billing tables, tax calculation, and configurable branding. The system runs autonomously via command line or GitHub Actions, saving invoices to a predictable output directory with standardized filenames.

## Why
- **Manual invoice creation is time-consuming**: Eliminates repetitive copy-paste work in document editors or spreadsheets
- **Consistency matters**: Ensures every invoice follows the same professional format and structure
- **Auditability is critical**: Sequential numbering and predictable filenames create a clear paper trail
- **Automation saves money**: Reduces administrative overhead for freelancers, agencies, and small businesses
- **Git-native versioning**: Committed invoices are version-controlled and recoverable

## What
The system receives a JSON file containing invoice data (client details, line items, payment terms, due date), increments a persistent counter, calculates subtotal/tax/total, generates a professional PDF invoice with branding placeholders, and saves it to `output/` with filename format `{client-name}-{YYYY-MM-DD}-{invoice-number}.pdf`.

### Success Criteria
- [ ] Accepts valid JSON input via file path or workflow dispatch parameter
- [ ] Validates all required fields (client name, project, line items, payment terms, due date)
- [ ] Generates sequential invoice numbers via persistent counter file (survives restarts)
- [ ] Calculates subtotal (sum of quantity × rate), applies configurable tax rate, produces correct total
- [ ] Produces professional PDF with branding placeholders, itemized table, payment instructions
- [ ] Saves PDF to `output/` directory with filename: `{client-name}-{YYYY-MM-DD}-{invoice-number}.pdf`
- [ ] System runs autonomously via GitHub Actions on workflow dispatch
- [ ] Results are committed back to repo
- [ ] All three execution paths work: CLI, GitHub Actions, Agent HQ

---

## Inputs
What goes into the system. Be specific about format, source, and any validation requirements.

```yaml
- name: "invoice_data"
  type: "JSON"
  source: "file path or workflow dispatch input"
  required: true
  description: "Complete invoice data including client, project, line items, terms, due date"
  example: |
    {
      "client_name": "Acme Corporation",
      "client_address": "123 Business St, Suite 100, San Francisco, CA 94105",
      "client_email": "billing@acmecorp.com",
      "project_description": "Q1 2026 Website Redesign and Development",
      "invoice_date": "2026-02-11",
      "due_date": "2026-03-13",
      "line_items": [
        {
          "description": "UI/UX Design (40 hours)",
          "quantity": 40,
          "rate": 150.00
        },
        {
          "description": "Frontend Development (80 hours)",
          "quantity": 80,
          "rate": 175.00
        },
        {
          "description": "Backend Integration (20 hours)",
          "quantity": 20,
          "rate": 200.00
        }
      ],
      "payment_terms": "Net 30. Payment due within 30 days of invoice date.",
      "payment_methods": [
        "Wire Transfer: Bank of America, Routing 123456789, Account 987654321",
        "Check: Payable to 'Your Company LLC', Mail to 456 Vendor Ave, Austin, TX 78701",
        "PayPal: payments@yourcompany.com"
      ],
      "notes": "Thank you for your business. Please include invoice number with payment."
    }

- name: "config"
  type: "JSON"
  source: "config/invoice_config.json"
  required: true
  description: "Branding and calculation settings"
  example: |
    {
      "company_name": "Your Company LLC",
      "company_address": "456 Vendor Ave, Austin, TX 78701",
      "company_email": "hello@yourcompany.com",
      "company_phone": "+1 (512) 555-0100",
      "company_logo_path": "assets/logo.png",
      "tax_rate": 0.0825,
      "tax_label": "Sales Tax (8.25%)",
      "currency": "USD",
      "currency_symbol": "$"
    }

- name: "counter_file"
  type: "JSON"
  source: "state/invoice_counter.json"
  required: true
  description: "Persistent invoice counter"
  example: |
    {
      "last_invoice_number": 1042,
      "prefix": "INV-",
      "padding": 4
    }
```

## Outputs
What comes out of the system. Where do results go?

```yaml
- name: "invoice_pdf"
  type: "file (PDF)"
  destination: "output/{client-name}-{YYYY-MM-DD}-{invoice-number}.pdf"
  description: "Professional PDF invoice with itemized table, calculations, and branding"
  example: "output/acme-corporation-2026-02-11-INV-1043.pdf"

- name: "updated_counter"
  type: "JSON"
  destination: "state/invoice_counter.json (overwrite)"
  description: "Incremented invoice counter for next invoice"
  example: |
    {
      "last_invoice_number": 1043,
      "prefix": "INV-",
      "padding": 4
    }

- name: "invoice_log"
  type: "JSON"
  destination: "logs/invoice_log.jsonl (append)"
  description: "JSONL audit trail of generated invoices"
  example: |
    {"timestamp": "2026-02-11T14:30:00Z", "invoice_number": "INV-1043", "client": "Acme Corporation", "total": 24100.00, "pdf_path": "output/acme-corporation-2026-02-11-INV-1043.pdf"}
```

---

## All Needed Context

### Documentation & References
```yaml
# MUST READ — Include these in context when building
- url: "https://reportlab.com/docs/reportlab-userguide.pdf"
  why: "ReportLab is the recommended PDF generation library. Sections 1-4 cover page setup, drawing, and tables."

- url: "https://docs.python.org/3/library/json.html"
  why: "Standard library JSON module for parsing input and managing counter file."

- url: "https://docs.python.org/3/library/pathlib.html"
  why: "Modern file path handling for cross-platform compatibility."

- doc: "config/mcp_registry.md"
  why: "Check which MCPs provide the capabilities this system needs"

- doc: "library/patterns.md"
  why: "Select the best workflow pattern for this system"

- doc: "library/tool_catalog.md"
  why: "Identify reusable tool patterns to adapt"
```

### Workflow Pattern Selection
```yaml
# Reference library/patterns.md — select the best-fit pattern
pattern: "Collect > Transform > Store"
rationale: "This is a data transformation pipeline. Collect JSON input, transform to PDF with calculations, store in output directory with sequential naming. No web access, no external APIs, pure data processing."
modifications: "Add atomic counter increment to prevent race conditions if multiple invoices are generated simultaneously (unlikely but possible in GitHub Actions)."
```

### MCP & Tool Requirements
```yaml
# Reference config/mcp_registry.md — list capabilities needed
capabilities:
  - name: "JSON parsing and validation"
    primary_mcp: "None"
    alternative_mcp: "None"
    fallback: "Python stdlib json + jsonschema for validation"
    secret_name: "None"

  - name: "PDF generation"
    primary_mcp: "None"
    alternative_mcp: "None"
    fallback: "Python reportlab library (pure Python, no external dependencies)"
    secret_name: "None"

  - name: "File I/O"
    primary_mcp: "filesystem"
    alternative_mcp: "None"
    fallback: "Python stdlib pathlib + built-in open()"
    secret_name: "None"

  - name: "Sequential counter management"
    primary_mcp: "None"
    alternative_mcp: "None"
    fallback: "JSON file with atomic read-modify-write via file locking"
    secret_name: "None"
```

### Known Gotchas & Constraints
```
# CRITICAL: ReportLab uses points (72 points = 1 inch) for positioning. US Letter is 612x792 points.
# CRITICAL: Counter file must use atomic read-modify-write to prevent race conditions
# CRITICAL: Client name must be slugified for filename (spaces → hyphens, lowercase, remove special chars)
# CRITICAL: All currency values should be Decimal (not float) to prevent rounding errors
# CRITICAL: Missing company_logo_path in config should gracefully skip logo (not crash)
# CRITICAL: Line item quantities and rates must be non-negative (validation required)
# CRITICAL: Due date must be >= invoice date (validation required)
# CRITICAL: Secrets are NEVER hardcoded — always use GitHub Secrets or .env (though this system needs no API secrets)
# CRITICAL: Every tool must have try/except, logging, type hints, and a main() function
# CRITICAL: PDF generation is pure Python — no headless browser or external rendering engine needed
```

---

## System Design

### Subagent Architecture
Define the specialist subagents this system needs. One subagent per major capability or workflow phase.

```yaml
subagents:
  - name: "invoice-parser-specialist"
    description: "When Claude needs to parse, validate, and normalize invoice JSON input"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Parse JSON invoice data from file or workflow input"
      - "Validate all required fields are present and correctly typed"
      - "Validate business rules (due_date >= invoice_date, quantity > 0, rate > 0)"
      - "Normalize client_name for filename generation (slugify)"
      - "Return validated, normalized invoice data structure"
    inputs: "JSON file path or raw JSON string"
    outputs: "Validated invoice data dict with normalized fields"

  - name: "counter-manager-specialist"
    description: "When Claude needs to manage sequential invoice numbering"
    tools: "Read, Write, Bash"
    model: "haiku"
    permissionMode: "default"
    responsibilities:
      - "Read current counter value from state/invoice_counter.json"
      - "Increment counter atomically"
      - "Generate formatted invoice number (e.g., INV-1043)"
      - "Write updated counter back to file"
      - "Handle missing or corrupted counter file (initialize to 1000)"
    inputs: "Counter file path (state/invoice_counter.json)"
    outputs: "Formatted invoice number string (e.g., 'INV-1043')"

  - name: "pdf-generator-specialist"
    description: "When Claude needs to generate a professional PDF invoice"
    tools: "Read, Bash"
    model: "sonnet"
    permissionMode: "default"
    responsibilities:
      - "Load company branding config from config/invoice_config.json"
      - "Create PDF canvas with professional layout"
      - "Render company branding (logo if available, name, address, contact)"
      - "Render invoice metadata (number, date, due date, client info)"
      - "Render itemized line items table with quantity, rate, amount columns"
      - "Calculate subtotal, apply tax rate, compute total"
      - "Render payment terms and payment methods"
      - "Return PDF as bytes"
    inputs: "Validated invoice data dict, invoice number, config dict"
    outputs: "PDF bytes ready to write to file"

  - name: "output-handler-specialist"
    description: "When Claude needs to save generated invoice and update audit trail"
    tools: "Write, Bash"
    model: "haiku"
    permissionMode: "default"
    responsibilities:
      - "Generate output filename: {client-slug}-{YYYY-MM-DD}-{invoice-number}.pdf"
      - "Write PDF bytes to output/ directory"
      - "Append audit log entry to logs/invoice_log.jsonl"
      - "Return full path to saved PDF"
    inputs: "PDF bytes, invoice metadata (client name, date, invoice number, total)"
    outputs: "Path to saved PDF file"
```

### Agent Teams Analysis
```yaml
# Apply the 3+ Independent Tasks Rule
independent_tasks:
  - "None — all steps have sequential dependencies"

independent_task_count: "0"
recommendation: "Sequential execution"
rationale: "This is a linear pipeline where each step depends on the output of the previous step:
  1. Parse input → 2. Get invoice number → 3. Generate PDF → 4. Save file.
  No parallelization opportunity. Agent Teams overhead is not justified."

# If NOT recommended:
sequential_rationale: "Every workflow step depends on the previous step's output. Parse must complete before counter can be incremented. Counter must return invoice number before PDF can be generated. PDF must be generated before it can be saved. Pure sequential pipeline."
```

### GitHub Actions Triggers
```yaml
triggers:
  - type: "workflow_dispatch"
    config: |
      inputs:
        invoice_json:
          description: 'Invoice data as JSON string'
          required: true
          type: string
    description: "Primary trigger: manual workflow dispatch with JSON input parameter. Ideal for API integration or manual generation."

  - type: "push"
    config: |
      paths:
        - 'input/*.json'
    description: "Secondary trigger: file drop. User commits a JSON file to input/ directory, workflow picks it up, generates invoice, deletes the input file."

  - type: "repository_dispatch"
    config: |
      types: ['generate_invoice']
    description: "Tertiary trigger: webhook-driven. External system POSTs to GitHub API to trigger invoice generation with JSON payload."
```

---

## Implementation Blueprint

### Workflow Steps
Ordered list of workflow phases. Each step becomes a section in workflow.md.

```yaml
steps:
  - name: "Parse and Validate Input"
    description: "Read JSON invoice data from input source, validate required fields and business rules, normalize client name for filename generation"
    subagent: "invoice-parser-specialist"
    tools: ["parse_invoice_input.py"]
    inputs: "JSON file path or raw JSON string from workflow dispatch"
    outputs: "Validated invoice data dict with normalized fields"
    failure_mode: "Missing required field, invalid date format, negative quantity/rate, malformed JSON"
    fallback: "Log validation errors to stderr, exit with code 1 and clear error message. DO NOT generate invoice with incomplete data."

  - name: "Load Configuration"
    description: "Read company branding and tax settings from config/invoice_config.json"
    subagent: "None (main agent)"
    tools: ["load_config.py"]
    inputs: "config/invoice_config.json path"
    outputs: "Config dict with branding, tax rate, currency settings"
    failure_mode: "Missing config file or malformed JSON"
    fallback: "Use sensible defaults: no logo, 0% tax rate, USD currency. Log warning but continue."

  - name: "Get Next Invoice Number"
    description: "Atomically increment invoice counter and return formatted invoice number"
    subagent: "counter-manager-specialist"
    tools: ["manage_counter.py"]
    inputs: "Counter file path (state/invoice_counter.json)"
    outputs: "Formatted invoice number string (e.g., 'INV-1043')"
    failure_mode: "Missing or corrupted counter file, file lock timeout"
    fallback: "Initialize counter to 1000 if missing. If file lock fails after 5 seconds, use timestamp-based fallback: 'INV-{timestamp}'. Log warning."

  - name: "Generate PDF Invoice"
    description: "Create professional PDF invoice with branding, itemized table, calculations, and payment instructions"
    subagent: "pdf-generator-specialist"
    tools: ["generate_invoice_pdf.py"]
    inputs: "Validated invoice data, invoice number, config dict"
    outputs: "PDF bytes ready to write"
    failure_mode: "ReportLab rendering error, missing font, invalid logo path"
    fallback: "Skip logo if file missing. Use built-in fonts if custom font fails. Log error and continue with degraded output."

  - name: "Save Invoice and Update Logs"
    description: "Write PDF to output directory with standardized filename, append audit log entry"
    subagent: "output-handler-specialist"
    tools: ["save_invoice.py"]
    inputs: "PDF bytes, invoice metadata (client name, date, invoice number, total)"
    outputs: "Path to saved PDF file"
    failure_mode: "Output directory missing, disk full, permission denied"
    fallback: "Create output/ directory if missing. If write fails, save to temp directory and log error. Audit log append is best-effort (continue even if log write fails)."
```

### Tool Specifications
For each tool the system needs. Reference library/tool_catalog.md for reusable patterns.

```yaml
tools:
  - name: "parse_invoice_input.py"
    purpose: "Parse and validate JSON invoice data with business rule checks"
    catalog_pattern: "json_read_write + custom validation (new pattern)"
    inputs:
      - "input_path: str — Path to JSON file or '-' for stdin"
    outputs: "JSON dict with validated, normalized invoice data"
    dependencies: ["jsonschema", "python-dateutil"]
    mcp_used: "none"
    error_handling: "Catch JSONDecodeError, ValidationError, ValueError. Log specific validation failures. Exit 1 on error with clear message."

  - name: "load_config.py"
    purpose: "Load company branding and tax configuration with sensible defaults"
    catalog_pattern: "json_read_write (from tool_catalog.md)"
    inputs:
      - "config_path: str — Path to config JSON file"
    outputs: "JSON dict with config (uses defaults for missing fields)"
    dependencies: []
    mcp_used: "none"
    error_handling: "Catch FileNotFoundError, JSONDecodeError. Return default config on error. Log warning but DO NOT fail."

  - name: "manage_counter.py"
    purpose: "Atomically increment invoice counter with file locking"
    catalog_pattern: "new (atomic counter management)"
    inputs:
      - "counter_path: str — Path to counter JSON file"
      - "action: str — 'get_next' or 'get_current'"
    outputs: "JSON with {'invoice_number': 'INV-1043', 'numeric': 1043}"
    dependencies: ["filelock"]
    mcp_used: "none"
    error_handling: "Use filelock for atomic read-modify-write. Timeout after 5 seconds. Initialize to 1000 if file missing. Fallback to timestamp-based number on lock failure."

  - name: "generate_invoice_pdf.py"
    purpose: "Generate professional PDF invoice with ReportLab"
    catalog_pattern: "new (PDF generation)"
    inputs:
      - "invoice_data: dict — Validated invoice data (from parse_invoice_input.py)"
      - "invoice_number: str — Formatted invoice number"
      - "config: dict — Company branding and tax config"
    outputs: "PDF bytes to stdout (or file path if --output specified)"
    dependencies: ["reportlab", "pillow"]
    mcp_used: "none"
    error_handling: "Catch ReportLab errors, IOErrors for logo file. Skip logo if missing. Use built-in Helvetica font as fallback. Log errors but produce PDF anyway (degraded output is better than no output)."

  - name: "save_invoice.py"
    purpose: "Save PDF to output directory with standardized filename and append audit log"
    catalog_pattern: "new (file output + audit logging)"
    inputs:
      - "pdf_bytes: bytes — PDF content (read from stdin or file)"
      - "client_name: str — Client name for filename"
      - "invoice_date: str — YYYY-MM-DD format"
      - "invoice_number: str — Formatted invoice number"
      - "total: Decimal — Total invoice amount"
    outputs: "JSON with {'pdf_path': 'output/acme-corporation-2026-02-11-INV-1043.pdf'}"
    dependencies: []
    mcp_used: "none"
    error_handling: "Create output/ directory if missing. Catch IOError on write. Save to /tmp/ as fallback. Audit log append is best-effort (log error but continue)."
```

### Per-Tool Pseudocode
```python
# parse_invoice_input.py
def main():
    # PATTERN: json_read_write + validation
    # Step 1: Parse input JSON
    if input_path == '-':
        data = json.load(sys.stdin)
    else:
        data = json.loads(Path(input_path).read_text())

    # Step 2: Validate schema
    # CRITICAL: Check required fields, data types, business rules
    schema = {
        "type": "object",
        "required": ["client_name", "project_description", "line_items", "invoice_date", "due_date"],
        "properties": {
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["description", "quantity", "rate"],
                    "properties": {
                        "quantity": {"type": "number", "minimum": 0},
                        "rate": {"type": "number", "minimum": 0}
                    }
                }
            }
        }
    }
    jsonschema.validate(instance=data, schema=schema)

    # CRITICAL: Validate due_date >= invoice_date
    invoice_date = dateutil.parser.parse(data["invoice_date"]).date()
    due_date = dateutil.parser.parse(data["due_date"]).date()
    if due_date < invoice_date:
        raise ValueError("due_date must be >= invoice_date")

    # Step 3: Normalize client name for filename (slugify)
    data["client_slug"] = slugify(data["client_name"])

    # Step 4: Output validated data
    print(json.dumps(data, indent=2))

# load_config.py
def main():
    # PATTERN: json_read_write with defaults
    try:
        config = json.loads(Path(config_path).read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"Config load failed: {e}. Using defaults.")
        config = {}

    # CRITICAL: Provide sensible defaults
    defaults = {
        "company_name": "Your Company",
        "tax_rate": 0.0,
        "currency": "USD",
        "currency_symbol": "$",
        "company_logo_path": None,
    }
    config = {**defaults, **config}
    print(json.dumps(config))

# manage_counter.py
def main():
    # PATTERN: Atomic counter with file locking
    from filelock import FileLock

    lock_path = f"{counter_path}.lock"
    with FileLock(lock_path, timeout=5):
        # CRITICAL: Atomic read-modify-write
        try:
            counter = json.loads(Path(counter_path).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            counter = {"last_invoice_number": 1000, "prefix": "INV-", "padding": 4}

        if action == "get_next":
            counter["last_invoice_number"] += 1
            Path(counter_path).write_text(json.dumps(counter, indent=2))

        invoice_number = f"{counter['prefix']}{counter['last_invoice_number']:0{counter['padding']}d}"
        print(json.dumps({"invoice_number": invoice_number, "numeric": counter["last_invoice_number"]}))

# generate_invoice_pdf.py
def main():
    # PATTERN: PDF generation with ReportLab
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from decimal import Decimal

    # GOTCHA: ReportLab uses points (72 points = 1 inch). US Letter = 612x792 points
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter  # 612, 792

    # Render company branding (top left)
    y = height - inch
    if config.get("company_logo_path") and Path(config["company_logo_path"]).exists():
        c.drawImage(config["company_logo_path"], inch, y - 0.5*inch, width=2*inch, preserveAspectRatio=True)
        y -= 0.7*inch
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, y, config["company_name"])
    y -= 0.3*inch
    c.setFont("Helvetica", 10)
    c.drawString(inch, y, config.get("company_address", ""))
    # ... more header rendering ...

    # CRITICAL: Use Decimal for currency calculations to prevent rounding errors
    subtotal = Decimal(0)
    for item in invoice_data["line_items"]:
        amount = Decimal(str(item["quantity"])) * Decimal(str(item["rate"]))
        subtotal += amount
        # ... render table row ...

    tax = subtotal * Decimal(str(config["tax_rate"]))
    total = subtotal + tax

    # Render totals table
    # ... render subtotal, tax, total rows ...

    c.save()
    buffer.seek(0)
    sys.stdout.buffer.write(buffer.getvalue())

# save_invoice.py
def main():
    # PATTERN: File output with audit logging
    # CRITICAL: Slugify client name, format date as YYYY-MM-DD
    filename = f"{slugify(client_name)}-{invoice_date}-{invoice_number}.pdf"
    output_path = Path("output") / filename

    # Create output directory if missing
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write PDF
    output_path.write_bytes(pdf_bytes)

    # Append audit log (best-effort)
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "invoice_number": invoice_number,
            "client": client_name,
            "total": float(total),
            "pdf_path": str(output_path),
        }
        with open("logs/invoice_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except IOError as e:
        logging.warning(f"Audit log write failed: {e}")

    print(json.dumps({"pdf_path": str(output_path)}))
```

### Integration Points
```yaml
SECRETS:
  # No external API secrets needed for this system

ENVIRONMENT:
  - file: ".env.example"
    vars:
      - "# No environment variables required for basic operation"
      - "# Optional: Customize config paths"
      - "INVOICE_CONFIG_PATH=config/invoice_config.json  # Company branding config"
      - "INVOICE_COUNTER_PATH=state/invoice_counter.json  # Invoice counter state"

DEPENDENCIES:
  - file: "requirements.txt"
    packages:
      - "reportlab>=4.0.0  # PDF generation"
      - "jsonschema>=4.0.0  # Input validation"
      - "python-dateutil>=2.8.0  # Date parsing"
      - "filelock>=3.0.0  # Atomic counter file locking"
      - "pillow>=10.0.0  # Logo image handling for ReportLab"
      - "python-slugify>=8.0.0  # Client name normalization"

GITHUB_ACTIONS:
  - trigger: "workflow_dispatch"
    config: |
      inputs:
        invoice_json:
          description: 'Invoice data as JSON string'
          required: true
          type: string
      
      jobs:
        generate:
          runs-on: ubuntu-latest
          timeout-minutes: 10
          steps:
            - uses: actions/checkout@v4
            - uses: actions/setup-python@v5
              with:
                python-version: '3.11'
            - run: pip install -r requirements.txt
            - run: echo '${{ inputs.invoice_json }}' | python -m invoice_generator.workflow
            - uses: stefanzweifel/git-auto-commit-action@v5
              with:
                commit_message: "feat: generate invoice"
                file_pattern: 'output/*.pdf state/invoice_counter.json logs/invoice_log.jsonl'
```

---

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Run FIRST — every tool must pass before proceeding to Level 2
# AST parse — verify valid Python syntax
python -c "import ast; ast.parse(open('tools/parse_invoice_input.py').read())"
python -c "import ast; ast.parse(open('tools/load_config.py').read())"
python -c "import ast; ast.parse(open('tools/manage_counter.py').read())"
python -c "import ast; ast.parse(open('tools/generate_invoice_pdf.py').read())"
python -c "import ast; ast.parse(open('tools/save_invoice.py').read())"

# Import check — verify no missing dependencies
python -c "import sys; sys.path.insert(0, 'tools'); import parse_invoice_input"
python -c "import sys; sys.path.insert(0, 'tools'); import load_config"
python -c "import sys; sys.path.insert(0, 'tools'); import manage_counter"
python -c "import sys; sys.path.insert(0, 'tools'); import generate_invoice_pdf"
python -c "import sys; sys.path.insert(0, 'tools'); import save_invoice"

# Structure check — verify main() exists
python -c "from tools.parse_invoice_input import main; assert callable(main)"
python -c "from tools.load_config import main; assert callable(main)"
python -c "from tools.manage_counter import main; assert callable(main)"
python -c "from tools.generate_invoice_pdf import main; assert callable(main)"
python -c "from tools.save_invoice import main; assert callable(main)"

# Expected: All pass with no errors. If any fail, fix before proceeding.
```

### Level 2: Unit Tests
```bash
# Run SECOND — each tool must produce correct output for sample inputs
# Test parse_invoice_input.py with valid input
cat > /tmp/test_invoice.json << 'EOF'
{
  "client_name": "Test Client",
  "project_description": "Test Project",
  "invoice_date": "2026-02-11",
  "due_date": "2026-03-13",
  "line_items": [
    {"description": "Service A", "quantity": 10, "rate": 100.00}
  ],
  "payment_terms": "Net 30"
}
EOF
python tools/parse_invoice_input.py /tmp/test_invoice.json > /tmp/parsed.json
# Expected: Valid JSON with client_slug field added

# Test load_config.py with missing file (should use defaults)
python tools/load_config.py /nonexistent/config.json > /tmp/config.json
# Expected: JSON with default values, exit code 0

# Test manage_counter.py (initialize counter)
mkdir -p state
python tools/manage_counter.py state/invoice_counter.json get_next > /tmp/counter.json
# Expected: {"invoice_number": "INV-1001", "numeric": 1001}

python tools/manage_counter.py state/invoice_counter.json get_next > /tmp/counter.json
# Expected: {"invoice_number": "INV-1002", "numeric": 1002}

# Test generate_invoice_pdf.py with sample data
python tools/generate_invoice_pdf.py \
  --invoice-data /tmp/parsed.json \
  --invoice-number "INV-1001" \
  --config /tmp/config.json \
  --output /tmp/test_invoice.pdf
# Expected: PDF file created, size > 5KB

# Test save_invoice.py
python tools/save_invoice.py \
  --pdf-path /tmp/test_invoice.pdf \
  --client-name "Test Client" \
  --invoice-date "2026-02-11" \
  --invoice-number "INV-1001" \
  --total "1100.00"
# Expected: PDF copied to output/test-client-2026-02-11-INV-1001.pdf
# Expected: Audit log entry appended to logs/invoice_log.jsonl

# If any tool fails: Read the error, fix the root cause, re-run.
# NEVER mock to make tests pass — fix the actual code.
```

### Level 3: Integration Tests
```bash
# Run THIRD — verify tools work together as a pipeline
# Simulate the full workflow with sample data

# Full pipeline test
cat > /tmp/full_invoice.json << 'EOF'
{
  "client_name": "Integration Test Corp",
  "client_address": "123 Test St",
  "client_email": "test@example.com",
  "project_description": "Full Pipeline Test",
  "invoice_date": "2026-02-11",
  "due_date": "2026-03-13",
  "line_items": [
    {"description": "Task 1", "quantity": 5, "rate": 150.00},
    {"description": "Task 2", "quantity": 10, "rate": 200.00}
  ],
  "payment_terms": "Net 30",
  "payment_methods": ["Bank transfer"],
  "notes": "Test invoice"
}
EOF

# Step 1: Parse input
python tools/parse_invoice_input.py /tmp/full_invoice.json > /tmp/step1_parsed.json
test -s /tmp/step1_parsed.json || { echo "Parse failed"; exit 1; }

# Step 2: Load config
python tools/load_config.py config/invoice_config.json > /tmp/step2_config.json
test -s /tmp/step2_config.json || { echo "Config load failed"; exit 1; }

# Step 3: Get invoice number
python tools/manage_counter.py state/invoice_counter.json get_next > /tmp/step3_counter.json
INVOICE_NUMBER=$(jq -r '.invoice_number' /tmp/step3_counter.json)
test -n "$INVOICE_NUMBER" || { echo "Counter failed"; exit 1; }

# Step 4: Generate PDF
python tools/generate_invoice_pdf.py \
  --invoice-data /tmp/step1_parsed.json \
  --invoice-number "$INVOICE_NUMBER" \
  --config /tmp/step2_config.json \
  --output /tmp/step4_invoice.pdf
test -f /tmp/step4_invoice.pdf || { echo "PDF generation failed"; exit 1; }
test $(stat -f%z /tmp/step4_invoice.pdf) -gt 5000 || { echo "PDF too small"; exit 1; }

# Step 5: Save invoice
python tools/save_invoice.py \
  --pdf-path /tmp/step4_invoice.pdf \
  --client-name "Integration Test Corp" \
  --invoice-date "2026-02-11" \
  --invoice-number "$INVOICE_NUMBER" \
  --total "2950.00"

# Verify final output exists
test -f output/integration-test-corp-2026-02-11-$INVOICE_NUMBER.pdf || { echo "Save failed"; exit 1; }

# Verify audit log has entry
grep "$INVOICE_NUMBER" logs/invoice_log.jsonl > /dev/null || { echo "Audit log missing"; exit 1; }

echo "✅ Integration test passed"

# Verify workflow.md references match actual tool files
grep -q "parse_invoice_input.py" workflow.md || { echo "workflow.md missing tool reference"; exit 1; }
grep -q "manage_counter.py" workflow.md || { echo "workflow.md missing tool reference"; exit 1; }
grep -q "generate_invoice_pdf.py" workflow.md || { echo "workflow.md missing tool reference"; exit 1; }
grep -q "save_invoice.py" workflow.md || { echo "workflow.md missing tool reference"; exit 1; }

# Verify CLAUDE.md documents all tools and subagents
grep -q "invoice-parser-specialist" CLAUDE.md || { echo "CLAUDE.md missing subagent"; exit 1; }
grep -q "counter-manager-specialist" CLAUDE.md || { echo "CLAUDE.md missing subagent"; exit 1; }
grep -q "pdf-generator-specialist" CLAUDE.md || { echo "CLAUDE.md missing subagent"; exit 1; }
grep -q "output-handler-specialist" CLAUDE.md || { echo "CLAUDE.md missing subagent"; exit 1; }

# Verify .github/workflows/ YAML is valid
python -c "import yaml; yaml.safe_load(open('.github/workflows/generate_invoice.yml'))"

echo "✅ All integration checks passed"
```

---

## Final Validation Checklist
- [ ] All tools pass Level 1 (syntax, imports, structure)
- [ ] All tools pass Level 2 (unit tests with sample data)
- [ ] Pipeline passes Level 3 (integration test end-to-end)
- [ ] workflow.md has failure modes and fallbacks for every step
- [ ] CLAUDE.md documents all tools, subagents, MCPs, and secrets
- [ ] .github/workflows/ has timeout-minutes and failure notifications
- [ ] .env.example lists all required environment variables (none for this system)
- [ ] .gitignore excludes .env, __pycache__/, credentials, *.pyc
- [ ] README.md covers all three execution paths (CLI, Actions, Agent HQ)
- [ ] No hardcoded secrets anywhere in the codebase (N/A — no secrets needed)
- [ ] Subagent files have valid YAML frontmatter and specific system prompts
- [ ] requirements.txt lists all Python dependencies
- [ ] Counter file uses atomic file locking to prevent race conditions
- [ ] PDF generation uses Decimal for currency to prevent rounding errors
- [ ] Filename generation properly slugifies client names (no special chars)
- [ ] Config loader provides sensible defaults when config missing
- [ ] Input validation checks business rules (due_date >= invoice_date, quantity > 0)

---

## Anti-Patterns to Avoid
- Do not hardcode API keys, tokens, or credentials — use GitHub Secrets or .env (N/A for this system)
- Do not use `git add -A` or `git add .` — stage only specific files (output/*.pdf, state/, logs/)
- Do not skip validation because "it should work" — run all three levels
- Do not catch bare `except:` — always catch specific exception types
- Do not build tools that require interactive input — all tools must run unattended
- Do not use float for currency calculations — use Decimal to prevent rounding errors
- Do not fail invoice generation if logo is missing — skip logo and continue (degraded output is better than failure)
- Do not write to counter file without file locking — use filelock for atomic read-modify-write
- Do not allow negative quantities or rates — validate input before processing
- Do not allow due_date < invoice_date — validate business rules
- Do not generate filename without slugifying client_name — special characters cause filesystem errors
- Do not commit .env files, credentials, or API keys to the repository (N/A — no secrets)
- Do not ignore failing tests — fix the root cause, never mock to pass
- Do not generate workflow steps without failure modes and fallback actions
- Do not write tools without try/except, logging, type hints, and a main() function

---

## Confidence Score: 8/10

**Score rationale:**
- [Input/Output specification]: Clear, well-defined JSON schema and PDF output format — Confidence: **high**
- [Technology choice]: ReportLab is mature, well-documented, pure Python — no external dependencies or browser automation needed — Confidence: **high**
- [Workflow pattern]: Classic Collect > Transform > Store pipeline with clear sequential steps — Confidence: **high**
- [Branding placeholders]: Interpreted as configurable company name/logo/address fields in config JSON. User may have different expectation. — Confidence: **medium**
- [Concurrent execution]: GitHub Actions may trigger multiple workflows simultaneously. Counter locking handles this, but needs testing. — Confidence: **medium**
- [Logo rendering]: ReportLab image handling can be finicky with different image formats. Graceful degradation needed. — Confidence: **medium**

**Ambiguity flags** (areas requiring clarification before building):
- [ ] **Branding placeholders**: Does "branding placeholders" mean (a) empty placeholder text fields in the PDF to be filled manually, OR (b) configurable company name/logo/address fields populated from config? **Assumption: (b) configurable fields.** If (a) is intended, tools need modification to render placeholder text instead of config values.

**If any ambiguity flag is checked, DO NOT proceed to build. Ask the user to clarify first.**

---

## Factory Build Prompt

When this PRP is ready, execute the build with:

```
/execute-prp PRPs/invoice-generator.md
```

This will trigger `factory/workflow.md` with the above requirements as structured input.
