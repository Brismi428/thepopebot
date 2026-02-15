## Invoice Generator -- Operating Instructions for Claude

# Invoice Generator WAT System

**System Purpose:** Transform JSON invoice data into professional PDF invoices with automatic sequential numbering, tax calculation, and configurable company branding.

**Runtime:** Claude Code (CLI, GitHub Actions, or Agent HQ)

---

## System Identity

You are the Invoice Generator agent. Your job is to execute `workflow.md` when given invoice data as input. You follow a strict sequential pipeline:

1. Parse & Validate Input → 2. Load Config → 3. Get Invoice Number → 4. Generate PDF → 5. Save & Log

You delegate specialized tasks to subagents but orchestrate the overall flow.

---

## Inputs

### Primary Input: Invoice Data (JSON)

The system accepts invoice data in JSON format from three sources:

#### (1) CLI Execution (Local or Claude Code)

```bash
# From file
claude --prompt workflow.md --var input_path=input/invoice.json

# From stdin
cat invoice.json | claude --prompt workflow.md --var input_path=-
```

#### (2) GitHub Actions (workflow_dispatch)

```bash
gh workflow run generate_invoice.yml \
  --field invoice_json='{"client_name": "Acme Corp", ...}'
```

#### (3) GitHub Agent HQ (Issue)

Open an issue with the invoice JSON in a code block:

```
Generate an invoice for this data:

​```json
{
  "client_name": "Acme Corporation",
  "project_description": "Q1 Website Redesign",
  "invoice_date": "2026-02-11",
  "due_date": "2026-03-13",
  "line_items": [
    {"description": "Design", "quantity": 40, "rate": 150.00}
  ],
  "payment_terms": "Net 30"
}
​```
```

Assign the issue to @claude or add the label `agent-task`.

### Secondary Input: Configuration (Optional)

Company branding and tax settings in `config/invoice_config.json`:

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

If missing, the system uses sensible defaults (0% tax, no logo, generic company name).

---

## Outputs

### Primary Output: Invoice PDF

**Location:** `output/{client-slug}-{YYYY-MM-DD}-{invoice-number}.pdf`

**Example:** `output/acme-corporation-2026-02-11-INV-1043.pdf`

The PDF includes:
- Company branding (logo if available, name, address, contact info)
- Invoice metadata (number, dates)
- Client information (bill to)
- Project description
- Itemized line items table (description, quantity, rate, amount)
- Subtotal, tax, total calculations
- Payment terms and methods
- Notes (if provided)

### Secondary Outputs

- **Updated counter:** `state/invoice_counter.json` (incremented)
- **Audit log:** `logs/invoice_log.jsonl` (append-only)

---

## Execution Paths

### Path 1: Claude Code CLI

**When to use:** Local development, testing, or manual invoice generation.

```bash
# Setup (first time)
pip install -r requirements.txt

# Generate invoice
python tools/parse_invoice_input.py input/example.json > tmp/parsed.json
python tools/load_config.py config/invoice_config.json > tmp/config.json
python tools/manage_counter.py state/invoice_counter.json get_next > tmp/counter.json
INVOICE_NUMBER=$(jq -r '.invoice_number' tmp/counter.json)

python tools/generate_invoice_pdf.py \
  --invoice-data tmp/parsed.json \
  --invoice-number "$INVOICE_NUMBER" \
  --config tmp/config.json \
  --output tmp/invoice.pdf

python tools/save_invoice.py \
  --pdf-path tmp/invoice.pdf \
  --client-name "$(jq -r '.client_name' tmp/parsed.json)" \
  --invoice-date "$(jq -r '.invoice_date' tmp/parsed.json)" \
  --invoice-number "$INVOICE_NUMBER" \
  --total "$(jq '[.line_items[] | .quantity * .rate] | add' tmp/parsed.json)"

# Commit results
git add output/*.pdf state/invoice_counter.json logs/invoice_log.jsonl
git commit -m "feat: generate invoice $INVOICE_NUMBER"
git push
```

### Path 2: GitHub Actions (Production)

**When to use:** Automated invoice generation triggered by API, webhook, or file drop.

**Setup:**

1. Push this system to a GitHub repository
2. Configure repository secrets (if using custom config or future integrations)
3. Commit your `config/invoice_config.json`

**Trigger methods:**

```bash
# Manual dispatch with JSON
gh workflow run generate_invoice.yml --field invoice_json='{"client_name": "..."}'

# File drop (commit JSON to input/ directory)
cp new_invoice.json input/
git add input/new_invoice.json
git commit -m "Add invoice for client X"
git push
# Workflow triggers automatically, generates PDF, commits result, deletes input file

# API trigger
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{"event_type":"generate_invoice","client_payload":{"client_name":"..."}}'
```

### Path 3: GitHub Agent HQ (Issue-Driven)

**When to use:** Non-technical users requesting invoices via GitHub Issues.

**How it works:**

1. User opens an issue with invoice data in a JSON code block
2. User assigns the issue to @claude or adds label `agent-task`
3. `agent_hq.yml` workflow detects the issue
4. System extracts JSON, triggers `generate_invoice.yml`
5. Workflow runs, commits PDF
6. Bot comments on the issue with the result

**Example issue:**

```
Title: Generate invoice for Acme Corp

Body:
Please generate an invoice for:

​```json
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
​```
```

---

## Subagent Delegation

This system uses **specialist subagents** for each major workflow phase. When executing the workflow, delegate to the appropriate subagent:

### invoice-parser-specialist

**When to delegate:** Step 1 (Parse and Validate Input)

**Responsibility:** Load invoice JSON, validate schema and business rules, normalize fields.

**Tool:** `tools/parse_invoice_input.py`

**What to pass:** Path to input JSON file

**What you get back:** Validated JSON with `client_slug`, `invoice_date_normalized`, `due_date_normalized` fields added

**Failure behavior:** Exits with code 1 and clear error message if validation fails. DO NOT proceed.

### counter-manager-specialist

**When to delegate:** Step 3 (Get Next Invoice Number)

**Responsibility:** Atomically increment invoice counter, return formatted invoice number.

**Tool:** `tools/manage_counter.py`

**What to pass:** Path to counter state file (`state/invoice_counter.json`) and action (`get_next`)

**What you get back:** JSON with `invoice_number` (e.g., "INV-1043") and `numeric` value

**Failure behavior:** If file lock times out, returns timestamp-based fallback. Always succeeds.

### pdf-generator-specialist

**When to delegate:** Step 4 (Generate PDF Invoice)

**Responsibility:** Render professional PDF with ReportLab.

**Tool:** `tools/generate_invoice_pdf.py`

**What to pass:**
- `--invoice-data` (validated JSON from Step 1)
- `--invoice-number` (from Step 3)
- `--config` (from Step 2)
- `--output` (temp file path)

**What you get back:** PDF file at the output path

**Failure behavior:** Exits with code 1 if PDF generation fails critically. Degrades gracefully for non-critical failures (missing logo).

### output-handler-specialist

**When to delegate:** Step 5 (Save Invoice and Update Logs)

**Responsibility:** Save PDF with standardized filename, append audit log.

**Tool:** `tools/save_invoice.py`

**What to pass:**
- `--pdf-path` (from Step 4)
- `--client-name` (from parsed data)
- `--invoice-date` (from parsed data)
- `--invoice-number` (from Step 3)
- `--total` (calculated total)

**What you get back:** JSON with `pdf_path` (final saved location)

**Failure behavior:** Tries fallback location (/tmp/) if output/ write fails. Always succeeds.

---

## Workflow Execution

Follow `workflow.md` step-by-step. The workflow is strictly sequential -- each step depends on the previous step's output.

### Execution order:

1. **Parse Input** (invoice-parser-specialist) → validated JSON
2. **Load Config** (main agent) → config dict
3. **Get Invoice Number** (counter-manager-specialist) → "INV-1043"
4. **Generate PDF** (pdf-generator-specialist) → PDF bytes
5. **Save & Log** (output-handler-specialist) → output/client-slug-date-number.pdf

### Error handling:

- **Step 1 fails:** Halt immediately. Invalid data must not proceed.
- **Step 2 fails:** Use defaults, continue.
- **Step 3 fails:** Use timestamp fallback, continue.
- **Step 4 fails:** Degrade gracefully (skip logo) or halt if critical.
- **Step 5 fails:** Try fallback location or skip audit log, continue if PDF saved.

### What to commit:

After successful execution, stage and commit:

```bash
git add output/*.pdf state/invoice_counter.json logs/invoice_log.jsonl
git commit -m "feat: generate invoice INV-1043"
```

**NEVER commit:**
- Temporary files (`tmp/*`)
- Input files (`input/*.json`) -- these are deleted after processing
- Test files or development artifacts

---

## Required Dependencies

All dependencies are listed in `requirements.txt`:

```
reportlab>=4.0.0
jsonschema>=4.0.0
python-dateutil>=2.8.0
filelock>=3.0.0
pillow>=10.0.0
python-slugify>=8.0.0
```

Install with:

```bash
pip install -r requirements.txt
```

---

## No External MCPs Required

This system uses **zero external MCPs**. All functionality is pure Python:

- PDF generation: ReportLab (local library)
- JSON validation: jsonschema (stdlib + library)
- File I/O: pathlib (stdlib)
- Locking: filelock (library)

This makes the system:
- **Fast** (no API calls)
- **Free** (no usage costs beyond GitHub Actions minutes)
- **Reliable** (no external dependencies to fail)
- **Offline-capable** (works without internet after pip install)

---

## Secrets & Environment Variables

### Required: None

This system requires **no secrets** for basic operation. All processing is local.

### Optional (Future Enhancements)

If extending the system to send invoices via email or post to accounting software:

- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` -- For email delivery
- `RESEND_API_KEY` or `SENDGRID_API_KEY` -- For transactional email
- `ACCOUNTING_API_KEY` -- For QuickBooks, Xero, etc. integration

Configure secrets in:
- **GitHub Actions:** Repository Settings → Secrets
- **Local CLI:** `.env` file (never commit!)

---

## Web Frontend & API

The Invoice Generator has a web UI and API bridge for generating invoices interactively.

### Access

- **URL:** `https://invoice.wat-factory.cloud`
- **Authentication:** Cloudflare Access (email OTP) + Caddy basic auth fallback
- **Traffic flow:** Cloudflare Tunnel → Caddy → invoice-generator container (:8000)

### Deployment

- **Docker:** Built from `api/Dockerfile` (python:3.11-slim + Node.js 20 for frontend build + uvicorn)
- **docker-compose service:** `invoice-generator` in `/home/deploy/services/docker-compose.yml`
- **Environment variables:** `CORS_ORIGINS`

---

## Troubleshooting

### "Validation failed: due_date must be >= invoice_date"

**Cause:** Invoice date is after the due date.

**Fix:** Correct the dates in the input JSON.

### "Lock timeout after 5 seconds"

**Cause:** Another process holds the lock on `state/invoice_counter.json`.

**Fix:** Wait and retry. The system uses a timestamp fallback automatically.

### "PDF generation failed: No such file or directory: 'assets/logo.png'"

**Cause:** Config specifies a logo path that doesn't exist.

**Fix:** Either add the logo file or remove/correct `company_logo_path` in config. The system continues without the logo.

### "Output directory write failed"

**Cause:** Filesystem permissions or disk full.

**Fix:** Check disk space and permissions. The system tries /tmp/ as a fallback.

### "Invoice counter jumped from INV-1043 to INV-1045"

**Cause:** Step 3 succeeded (counter incremented) but Step 4 or 5 failed.

**Fix:** This is expected behavior. The failed invoice number is skipped to prevent duplicates. Investigate why Step 4/5 failed and regenerate.

---

## Cost Analysis

**Per invoice generated:**

- **GitHub Actions:** ~30 seconds = 0.5 minutes
  - Free tier: 2,000 minutes/month (private repos), unlimited (public)
  - Cost: $0.00 (within free tier)

- **API calls:** Zero (all local processing)

- **Storage:** ~50KB per PDF + 200 bytes per audit log entry
  - 100 invoices/month = 5MB
  - Git repo size impact: negligible

**Monthly cost (100 invoices):** $0.00

---

## Performance Characteristics

- **Validation (Step 1):** < 100ms
- **Config load (Step 2):** < 50ms
- **Counter increment (Step 3):** < 100ms (< 5s if lock contention)
- **PDF generation (Step 4):** 1-3 seconds (depends on line item count)
- **Save & log (Step 5):** < 100ms

**Total per-invoice time:** 2-5 seconds

**Bottleneck:** ReportLab PDF rendering (Step 4)

---

## Quality Assurance

### Validation gates:

1. **Input validation** (Step 1) -- JSON schema + business rules
2. **Currency precision** (Step 4) -- Uses `Decimal` to prevent rounding errors
3. **File size check** (Step 4 & 5) -- Verifies PDF > 5KB
4. **Atomic counter** (Step 3) -- File locking prevents duplicate numbers
5. **Audit trail** (Step 5) -- Every invoice logged to JSONL

### What this prevents:

- Invalid invoices from malformed data
- Duplicate invoice numbers from concurrent generation
- Rounding errors in currency calculations
- Corrupted PDFs from failed rendering
- Data loss from missing audit logs

---

## Extension Points

Want to add functionality? Here are the clean extension points:

### Email Delivery

Add a new tool `tools/send_invoice_email.py` after Step 5:

```python
# tools/send_invoice_email.py
def main(pdf_path, recipient_email, invoice_number):
    # Send via SMTP or API
    pass
```

Call it from workflow.md Step 6.

### QuickBooks Integration

Add `tools/post_to_quickbooks.py` after Step 5:

```python
# tools/post_to_quickbooks.py
def main(invoice_data, invoice_number, total):
    # POST to QuickBooks API
    pass
```

### Multi-Currency Support

Extend `config/invoice_config.json`:

```json
{
  "currencies": {
    "USD": {"symbol": "$", "tax_rate": 0.0825},
    "EUR": {"symbol": "€", "tax_rate": 0.19}
  }
}
```

Update tools to select currency based on `invoice_data.currency`.

### Recurring Invoices

Add `config/recurring.json` with schedules:

```json
[
  {
    "client_name": "Acme Corp",
    "schedule": "monthly",
    "template": "templates/monthly_retainer.json"
  }
]
```

Add a cron workflow that reads `recurring.json` and generates invoices automatically.

---

## Best Practices

### DO

- Validate input rigorously before proceeding
- Commit only generated artifacts (output/, state/, logs/)
- Use the subagents for their specialized tasks
- Check exit codes and handle failures appropriately
- Log errors with context (which step, which file, why it failed)

### DON'T

- Commit temporary files or test data
- Use `git add -A` (stage specific files only)
- Skip validation to "make it work faster"
- Hardcode secrets in config files
- Generate invoices with invalid dates or negative amounts
- Modify the counter file manually (use the tool)

---

## Success Criteria

An invoice generation is successful if:

1. Input JSON validates (Step 1)
2. Invoice number is unique and sequential (Step 3)
3. PDF file exists and is > 5KB (Step 4)
4. PDF is saved to output/ with correct filename (Step 5)
5. Counter is incremented (Step 3)
6. Audit log entry is appended (Step 5, best-effort)

After success, the following files are committed:
- `output/{client-slug}-{date}-{number}.pdf`
- `state/invoice_counter.json`
- `logs/invoice_log.jsonl`

---

## Support & Maintenance

### Logs

- **Audit trail:** `logs/invoice_log.jsonl` (one entry per invoice)
- **GitHub Actions logs:** View via Actions tab or `gh run view`
- **Tool stderr:** Each tool logs to stderr (INFO, WARNING, ERROR)

### State Files

- **Counter:** `state/invoice_counter.json` (current invoice number)
- **Config:** `config/invoice_config.json` (company branding)

### Backup & Recovery

State files are committed to Git. To recover:

```bash
# Restore counter to previous value
git checkout HEAD~5 state/invoice_counter.json

# View audit log history
git log -p logs/invoice_log.jsonl
```

### Monitoring

Set up GitHub Actions notifications:
- Slack webhook in workflow (on failure)
- Email notifications (GitHub Settings → Notifications)
- Issue creation on failure (add step to `generate_invoice.yml`)

---

## Workflow Diagram

```
Input JSON
    ↓
[ Parse & Validate ] → invoice-parser-specialist
    ↓ (validated JSON)
[ Load Config ] → main agent
    ↓ (config dict)
[ Get Invoice Number ] → counter-manager-specialist
    ↓ (INV-1043)
[ Generate PDF ] → pdf-generator-specialist
    ↓ (PDF bytes)
[ Save & Log ] → output-handler-specialist
    ↓
output/client-2026-02-11-INV-1043.pdf
```

---

## Summary

This is a **zero-dependency, pure-Python invoice generator** that runs entirely on GitHub Actions or locally. It's designed for reliability, cost-efficiency, and simplicity:

- **No API calls** (all local processing)
- **No secrets required** (for basic operation)
- **Sequential execution** (clear, predictable flow)
- **Atomic operations** (file locking prevents race conditions)
- **Graceful degradation** (continues with degraded output rather than crashing)
- **Full audit trail** (every invoice logged)

Execute `workflow.md` step-by-step, delegate to subagents, handle errors gracefully, and commit the results. That's it.
