# Invoice Generator

**A WAT System for transforming JSON invoice data into professional PDF invoices with automatic sequential numbering, tax calculation, and configurable branding.**

---

## Features

- ✅ **Professional PDF invoices** with company branding, itemized tables, and calculations
- ✅ **Automatic sequential numbering** with atomic file locking (INV-1001, INV-1002, ...)
- ✅ **Tax calculation** with configurable rates
- ✅ **Configurable branding** (company name, logo, address, contact info)
- ✅ **Input validation** with business rule enforcement
- ✅ **Audit trail** (JSONL log of all generated invoices)
- ✅ **Three execution paths** (CLI, GitHub Actions, Agent HQ)
- ✅ **Zero external dependencies** (no API calls, all local processing)
- ✅ **Graceful degradation** (continues without logo if missing)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Git
- GitHub repository (for GitHub Actions / Agent HQ paths)

### Installation

```bash
# Clone or copy this system
git clone <your-repo-url>
cd invoice-generator

# Install Python dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p output logs state input config
```

### Configuration

Edit `config/invoice_config.json` with your company details:

```json
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
```

**Note:** `company_logo_path` is optional. If omitted or the file is missing, the system renders text-only branding.

---

## Usage

There are **three ways** to generate invoices with this system:

### Path 1: Claude Code CLI (Local)

**Best for:** Development, testing, manual generation

```bash
# 1. Create invoice data file
cat > input/my_invoice.json << 'EOF'
{
  "client_name": "Acme Corporation",
  "project_description": "Q1 Website Redesign",
  "invoice_date": "2026-02-11",
  "due_date": "2026-03-13",
  "line_items": [
    {"description": "Design (40 hours)", "quantity": 40, "rate": 150.00},
    {"description": "Development (80 hours)", "quantity": 80, "rate": 175.00}
  ],
  "payment_terms": "Net 30",
  "payment_methods": ["Bank Transfer", "Check"],
  "notes": "Thank you for your business"
}
EOF

# 2. Run the pipeline
mkdir -p tmp

python tools/parse_invoice_input.py input/my_invoice.json > tmp/parsed.json
python tools/load_config.py config/invoice_config.json > tmp/config.json
python tools/manage_counter.py state/invoice_counter.json get_next > tmp/counter.json

INVOICE_NUMBER=$(jq -r '.invoice_number' tmp/counter.json)

python tools/generate_invoice_pdf.py \
  --invoice-data tmp/parsed.json \
  --invoice-number "$INVOICE_NUMBER" \
  --config tmp/config.json \
  --output tmp/invoice.pdf

CLIENT_NAME=$(jq -r '.client_name' tmp/parsed.json)
INVOICE_DATE=$(jq -r '.invoice_date' tmp/parsed.json)
SUBTOTAL=$(jq '[.line_items[] | .quantity * .rate] | add' tmp/parsed.json)
TAX_RATE=$(jq -r '.tax_rate // 0' tmp/config.json)
TOTAL=$(echo "$SUBTOTAL * (1 + $TAX_RATE)" | bc -l)

python tools/save_invoice.py \
  --pdf-path tmp/invoice.pdf \
  --client-name "$CLIENT_NAME" \
  --invoice-date "$INVOICE_DATE" \
  --invoice-number "$INVOICE_NUMBER" \
  --total "$TOTAL"

# 3. Commit results
git add output/*.pdf state/invoice_counter.json logs/invoice_log.jsonl
git commit -m "feat: generate invoice $INVOICE_NUMBER"
git push
```

### Path 2: GitHub Actions (Automated)

**Best for:** Production, API integration, scheduled generation

#### Setup

1. Push this system to a GitHub repository
2. (Optional) Add secrets in **Settings → Secrets** if you add future integrations
3. Commit your `config/invoice_config.json`

#### Trigger Methods

##### (a) Manual Dispatch with JSON

```bash
gh workflow run generate_invoice.yml \
  --field invoice_json='{
    "client_name": "Acme Corporation",
    "project_description": "Q1 Website Redesign",
    "invoice_date": "2026-02-11",
    "due_date": "2026-03-13",
    "line_items": [
      {"description": "Design", "quantity": 40, "rate": 150.00}
    ],
    "payment_terms": "Net 30"
  }'
```

##### (b) File Drop

Commit a JSON file to `input/` directory:

```bash
cp new_invoice.json input/
git add input/new_invoice.json
git commit -m "Add invoice for Acme Corp"
git push
```

The workflow triggers automatically, generates the invoice, commits the result, and **deletes the input file**.

##### (c) API / Webhook

```bash
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{
    "event_type": "generate_invoice",
    "client_payload": {
      "client_name": "Acme Corporation",
      "project_description": "Q1 Website Redesign",
      "invoice_date": "2026-02-11",
      "due_date": "2026-03-13",
      "line_items": [
        {"description": "Design", "quantity": 40, "rate": 150.00}
      ]
    }
  }'
```

### Path 3: GitHub Agent HQ (Issue-Driven)

**Best for:** Non-technical users requesting invoices

#### Setup

1. Complete "Path 2: GitHub Actions" setup
2. Add `ANTHROPIC_API_KEY` to repository secrets (for general task handling)

#### How to Use

Open a GitHub Issue with the invoice data in a JSON code block:

````markdown
**Title:** Generate invoice for Acme Corp

**Body:**
Please generate an invoice for:

```json
{
  "client_name": "Acme Corporation",
  "project_description": "Q1 Website Redesign",
  "invoice_date": "2026-02-11",
  "due_date": "2026-03-13",
  "line_items": [
    {"description": "Design (40 hours)", "quantity": 40, "rate": 150.00},
    {"description": "Development (80 hours)", "quantity": 80, "rate": 175.00}
  ],
  "payment_terms": "Net 30",
  "payment_methods": ["Bank Transfer", "Check"],
  "notes": "Thank you for your business"
}
```
````

**Then:**
- Assign the issue to `@claude`, OR
- Add the label `agent-task`

The system will:
1. Detect the issue
2. Extract the JSON
3. Trigger `generate_invoice.yml`
4. Comment on the issue with the result

---

## Input Schema

The invoice JSON must include these required fields:

| Field | Type | Description |
|-------|------|-------------|
| `client_name` | string | Client name (min 1 char) |
| `project_description` | string | Project or service description |
| `invoice_date` | string | Invoice date (ISO 8601 or parseable) |
| `due_date` | string | Payment due date (must be >= invoice_date) |
| `line_items` | array | Array of line items (min 1) |
| `line_items[].description` | string | Item description |
| `line_items[].quantity` | number | Quantity (must be > 0) |
| `line_items[].rate` | number | Rate per unit (must be >= 0) |

**Optional fields:**

- `client_address` -- Client address (string)
- `client_email` -- Client email (string)
- `payment_terms` -- Payment terms text (string)
- `payment_methods` -- Array of payment method strings
- `notes` -- Additional notes (string)

See `input/example.json` for a complete example.

---

## Output Files

### Generated Invoice

**Location:** `output/{client-slug}-{YYYY-MM-DD}-{invoice-number}.pdf`

**Example:** `output/acme-corporation-2026-02-11-INV-1043.pdf`

### State Files

- **Counter:** `state/invoice_counter.json` -- Current invoice number
- **Audit log:** `logs/invoice_log.jsonl` -- All generated invoices (JSONL format)

---

## Validation & Business Rules

The system enforces strict validation:

- ✅ All required fields must be present
- ✅ `due_date` must be >= `invoice_date`
- ✅ All line item `quantity` values must be > 0
- ✅ All line item `rate` values must be >= 0
- ✅ Client name must be convertible to a safe filename

**If validation fails**, the system exits with a clear error message and does NOT generate an invoice.

---

## Cost Analysis

**Per invoice:**
- GitHub Actions minutes: ~30 seconds (0.5 minutes)
- API calls: Zero (all local processing)
- Storage: ~50KB per PDF

**Monthly cost for 100 invoices:**
- GitHub Actions: $0 (within free tier: 2,000 min/month for private repos, unlimited for public)
- APIs: $0 (no external API calls)
- **Total: $0**

---

## Troubleshooting

### "Validation failed: due_date must be >= invoice_date"

**Cause:** Invoice date is after the due date.

**Fix:** Correct the dates in your input JSON.

---

### "Lock timeout after 5 seconds"

**Cause:** Another workflow holds the lock on `state/invoice_counter.json`.

**Fix:** The system automatically uses a timestamp-based fallback invoice number. Check logs for details.

---

### "PDF generation failed: No such file or directory: 'assets/logo.png'"

**Cause:** Config specifies a logo path that doesn't exist.

**Fix:**
- Add the logo file to the specified path, OR
- Set `company_logo_path` to `null` in config, OR
- Remove the `company_logo_path` field

The system continues without the logo (text-only branding).

---

### "Invoice counter jumped from INV-1043 to INV-1045"

**Cause:** The counter was incremented (Step 3) but PDF generation or saving (Steps 4-5) failed.

**Fix:** This is expected behavior. The skipped number prevents duplicate invoice numbers. Investigate why the later step failed and regenerate.

---

## Architecture

This system uses the **WAT framework**:

- **W**orkflow: `workflow.md` -- sequential pipeline (5 steps)
- **A**gents: `.claude/agents/*` -- 4 specialist subagents
- **T**ools: `tools/*.py` -- 5 Python tools

### Tools

1. `parse_invoice_input.py` -- Validate and normalize input JSON
2. `load_config.py` -- Load company config with defaults
3. `manage_counter.py` -- Atomic invoice numbering
4. `generate_invoice_pdf.py` -- Render PDF with ReportLab
5. `save_invoice.py` -- Save PDF and append audit log

### Subagents

1. `invoice-parser-specialist` -- Input validation
2. `counter-manager-specialist` -- Sequential numbering
3. `pdf-generator-specialist` -- PDF rendering
4. `output-handler-specialist` -- File output and logging

### Execution Flow

```
Input JSON
    ↓
Parse & Validate (invoice-parser-specialist)
    ↓
Load Config (main agent)
    ↓
Get Invoice Number (counter-manager-specialist)
    ↓
Generate PDF (pdf-generator-specialist)
    ↓
Save & Log (output-handler-specialist)
    ↓
output/client-2026-02-11-INV-1043.pdf
```

---

## Extending the System

### Add Email Delivery

Create `tools/send_invoice_email.py`:

```python
def main(pdf_path, recipient_email, invoice_number):
    # Send via SMTP or transactional email API
    pass
```

Add a new step to `workflow.md` after Step 5.

### Add QuickBooks Integration

Create `tools/post_to_quickbooks.py`:

```python
def main(invoice_data, invoice_number, total):
    # POST to QuickBooks API
    pass
```

Add OAuth secrets to GitHub Secrets.

### Add Recurring Invoices

Create `config/recurring.json` with schedules, then add a cron workflow that reads the schedule and triggers invoice generation.

---

## Security

- **No secrets required** for basic operation
- All processing is local (no API calls)
- Input validation prevents injection attacks
- File locking prevents race conditions
- State files are version-controlled (Git tracks all changes)

**Never commit:**
- `.env` files
- API keys or passwords
- Test data with real client information

---

## Support

### Logs

- **Audit trail:** `logs/invoice_log.jsonl` (one line per invoice)
- **GitHub Actions logs:** View in Actions tab or `gh run view`
- **Tool output:** Each tool logs to stderr (INFO, WARNING, ERROR)

### Backup & Recovery

All state files are committed to Git:

```bash
# Restore counter to previous value
git checkout HEAD~5 state/invoice_counter.json

# View invoice history
git log -p logs/invoice_log.jsonl
```

---

## License

[Choose appropriate license: MIT, Apache 2.0, etc.]

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run validation: `python -m pytest tests/` (if tests exist)
5. Commit your changes (`git commit -m "feat: add feature"`)
6. Push to the branch (`git push origin feature/my-feature`)
7. Open a Pull Request

---

## Acknowledgments

Built with:
- [ReportLab](https://www.reportlab.com/) -- PDF generation
- [python-slugify](https://github.com/un33k/python-slugify) -- Filename normalization
- [filelock](https://github.com/tox-dev/py-filelock) -- Atomic file operations

Part of the **WAT Systems Factory** -- a meta-system for building GitHub-native AI agents.
