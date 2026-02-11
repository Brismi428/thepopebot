# Invoice Generator -- Quick Deployment Guide

## 1. Initial Setup (5 minutes)

```bash
# Create new GitHub repository
gh repo create invoice-generator --public --clone

# Copy system files
cp -r /path/to/systems/invoice-generator/* ./
cd invoice-generator

# Configure company branding
nano config/invoice_config.json
# Edit: company_name, company_address, company_email, company_phone, tax_rate

# (Optional) Add company logo
# Place PNG file at assets/logo.png

# Commit and push
git add .
git commit -m "Initial deployment of invoice generator"
git push origin main
```

## 2. Test with Example Invoice (2 minutes)

```bash
# Trigger workflow with example data
gh workflow run generate_invoice.yml \
  --field invoice_json="$(cat input/example.json | jq -c .)"

# Wait 30 seconds, then check results
gh run list --limit 1
gh run view --log

# Download generated PDF
gh run download
```

## 3. Production Use

### Method A: Manual Dispatch

```bash
gh workflow run generate_invoice.yml \
  --field invoice_json='{
    "client_name": "Your Client",
    "project_description": "Project Name",
    "invoice_date": "2026-02-11",
    "due_date": "2026-03-13",
    "line_items": [
      {"description": "Service", "quantity": 10, "rate": 100.00}
    ],
    "payment_terms": "Net 30"
  }'
```

### Method B: File Drop

```bash
# Create invoice JSON file
cat > input/client_invoice.json << 'INVOICE'
{
  "client_name": "Client Name",
  ...
}
INVOICE

# Commit (triggers workflow automatically)
git add input/client_invoice.json
git commit -m "Add invoice for Client Name"
git push
```

### Method C: GitHub Issues (Non-Technical Users)

1. Open new issue
2. Paste invoice JSON in code block
3. Assign to @claude or add label `agent-task`
4. Bot generates invoice and comments with download link

## 4. Retrieve Generated Invoices

### From Repository

```bash
git pull
ls output/
# PDFs are committed: output/client-name-2026-02-11-INV-1001.pdf
```

### From GitHub Actions Artifacts

```bash
gh run download <run-id>
```

### From Web UI

- Navigate to Actions tab
- Click on workflow run
- Download artifact from "Summary" section

## 5. Monitoring

### View Audit Log

```bash
cat logs/invoice_log.jsonl
# One line per invoice with timestamp, client, amount, path
```

### Check Invoice Counter

```bash
cat state/invoice_counter.json
# {"last_invoice_number": 1042, "prefix": "INV-", "padding": 4}
```

### View Workflow Logs

```bash
gh run list
gh run view <run-id> --log
```

## Troubleshooting

### "Validation failed"

Check input JSON matches schema in README.md. Common issues:
- Missing required field
- due_date before invoice_date
- Negative quantity or rate

### "Lock timeout"

Multiple workflows running concurrently. System uses timestamp fallback automatically. Check logs for fallback invoice number.

### "PDF generation failed"

Check logo path in config. System should skip missing logo and continue. View workflow logs for details.

## Cost

**$0/month** for typical usage (within GitHub Actions free tier: 2,000 minutes/month for private repos, unlimited for public).

## Support

- README.md -- Full documentation
- CLAUDE.md -- Agent operating instructions
- workflow.md -- Technical workflow details
- BUILD_REPORT.md -- System architecture and decisions
