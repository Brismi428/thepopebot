# Airtable Automation Workflows

## Overview

This guide covers building automation workflows with Airtable, including scheduled syncs, data validation, and integration patterns.

## Scheduled Sync Workflow

### Sync Between Bases

```python
#!/usr/bin/env python3
"""
Sync records between two Airtable bases on a schedule.
Run with: python sync_workflow.py
Schedule with cron: 0 * * * * python /path/to/sync_workflow.py
"""

import os
import time
import logging
from datetime import datetime
from pyairtable import Api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirtableSync:
    def __init__(self, api_key: str):
        self.api = Api(api_key)

    def sync_tables(
        self,
        source_base: str,
        source_table: str,
        target_base: str,
        target_table: str,
        key_field: str = "Email",
        field_mapping: dict = None
    ) -> dict:
        """
        Sync records from source to target table.

        Args:
            source_base: Source base ID
            source_table: Source table name
            target_base: Target base ID
            target_table: Target table name
            key_field: Field to match records on
            field_mapping: Optional {source_field: target_field} mapping

        Returns:
            Dict with created, updated, and skipped counts
        """
        source = self.api.table(source_base, source_table)
        target = self.api.table(target_base, target_table)

        # Get all records
        source_records = source.all()
        target_records = {
            r["fields"].get(key_field): r
            for r in target.all()
        }

        to_create = []
        to_update = []
        skipped = 0

        for record in source_records:
            key = record["fields"].get(key_field)
            if not key:
                skipped += 1
                continue

            # Apply field mapping if provided
            fields = record["fields"]
            if field_mapping:
                fields = {
                    field_mapping.get(k, k): v
                    for k, v in fields.items()
                    if field_mapping.get(k, k) is not None
                }

            if key in target_records:
                to_update.append({
                    "id": target_records[key]["id"],
                    "fields": fields
                })
            else:
                to_create.append({"fields": fields})

        # Execute batches with rate limiting
        created = self._batch_create(target, to_create)
        updated = self._batch_update(target, to_update)

        return {
            "created": len(created),
            "updated": len(updated),
            "skipped": skipped
        }

    def _batch_create(self, table, records: list, batch_size: int = 10) -> list:
        created = []
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            created.extend(table.batch_create(batch))
            time.sleep(0.2)  # Rate limiting
        return created

    def _batch_update(self, table, records: list, batch_size: int = 10) -> list:
        updated = []
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            updated.extend(table.batch_update(batch))
            time.sleep(0.2)
        return updated


def main():
    api_key = os.environ["AIRTABLE_API_KEY"]
    sync = AirtableSync(api_key)

    # Example: Sync CRM contacts to Marketing list
    result = sync.sync_tables(
        source_base="appCRMXXXXXX",
        source_table="Contacts",
        target_base="appMarketingXXXXXX",
        target_table="Email List",
        key_field="Email",
        field_mapping={
            "Full Name": "Name",
            "Email": "Email",
            "Company": "Company",
            "Status": None,  # Don't sync this field
        }
    )

    logger.info(f"Sync complete: {result}")


if __name__ == "__main__":
    main()
```

## Data Validation Pipeline

```python
#!/usr/bin/env python3
"""
Validate records and flag issues in Airtable.
"""

import os
import re
from pyairtable import Api

class DataValidator:
    def __init__(self, api_key: str, base_id: str, table_name: str):
        self.api = Api(api_key)
        self.table = self.api.table(base_id, table_name)

    def validate_all(self, rules: list) -> dict:
        """
        Validate all records against rules.

        Args:
            rules: List of validation rule dicts:
                   {"field": "Email", "type": "email", "required": True}

        Returns:
            Dict with valid, invalid counts and error details
        """
        records = self.table.all()
        valid = []
        invalid = []

        for record in records:
            errors = self._validate_record(record["fields"], rules)
            if errors:
                invalid.append({
                    "id": record["id"],
                    "errors": errors
                })
            else:
                valid.append(record["id"])

        return {
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "invalid_records": invalid
        }

    def _validate_record(self, fields: dict, rules: list) -> list:
        errors = []

        for rule in rules:
            field_name = rule["field"]
            value = fields.get(field_name)

            # Required check
            if rule.get("required") and not value:
                errors.append(f"{field_name} is required")
                continue

            if not value:
                continue

            # Type validation
            rule_type = rule.get("type")

            if rule_type == "email":
                if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", str(value)):
                    errors.append(f"{field_name} is not a valid email")

            elif rule_type == "phone":
                cleaned = re.sub(r"[\s\-\(\)]", "", str(value))
                if not re.match(r"^\+?\d{10,15}$", cleaned):
                    errors.append(f"{field_name} is not a valid phone number")

            elif rule_type == "url":
                if not re.match(r"^https?://[\w\.-]+", str(value)):
                    errors.append(f"{field_name} is not a valid URL")

            elif rule_type == "number":
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"{field_name} is not a valid number")

            elif rule_type == "min_length":
                min_len = rule.get("value", 0)
                if len(str(value)) < min_len:
                    errors.append(f"{field_name} must be at least {min_len} characters")

            elif rule_type == "max_length":
                max_len = rule.get("value", float("inf"))
                if len(str(value)) > max_len:
                    errors.append(f"{field_name} must be at most {max_len} characters")

            elif rule_type == "regex":
                pattern = rule.get("pattern")
                if not re.match(pattern, str(value)):
                    errors.append(f"{field_name} does not match required format")

            elif rule_type == "enum":
                allowed = rule.get("values", [])
                if value not in allowed:
                    errors.append(f"{field_name} must be one of: {', '.join(allowed)}")

        return errors

    def flag_invalid_records(self, rules: list, error_field: str = "Validation Errors"):
        """
        Validate and update records with error messages.
        """
        result = self.validate_all(rules)

        # Update invalid records with errors
        updates = [
            {"id": r["id"], "fields": {error_field: "\n".join(r["errors"])}}
            for r in result["invalid_records"]
        ]

        # Clear errors on valid records (get current records with errors)
        current_errors = self.table.all(formula=f"{{{error_field}}} != BLANK()")
        valid_ids = set(r["id"] for r in self.table.all()) - set(r["id"] for r in result["invalid_records"])
        clears = [
            {"id": r["id"], "fields": {error_field: ""}}
            for r in current_errors
            if r["id"] in valid_ids
        ]

        # Batch update
        for i in range(0, len(updates), 10):
            self.table.batch_update(updates[i:i+10])

        for i in range(0, len(clears), 10):
            self.table.batch_update(clears[i:i+10])

        return result


# Usage
def main():
    validator = DataValidator(
        os.environ["AIRTABLE_API_KEY"],
        "appXXXXXX",
        "Contacts"
    )

    rules = [
        {"field": "Name", "type": "min_length", "value": 2, "required": True},
        {"field": "Email", "type": "email", "required": True},
        {"field": "Phone", "type": "phone"},
        {"field": "Website", "type": "url"},
        {"field": "Status", "type": "enum", "values": ["Lead", "Customer", "Churned"]},
    ]

    result = validator.flag_invalid_records(rules)
    print(f"Valid: {result['valid_count']}, Invalid: {result['invalid_count']}")


if __name__ == "__main__":
    main()
```

## Webhook Handler

```python
#!/usr/bin/env python3
"""
Flask webhook handler for Airtable events.
Run with: python webhook_handler.py
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import os

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get("AIRTABLE_WEBHOOK_SECRET", "")

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Airtable webhook signature."""
    if not WEBHOOK_SECRET:
        return True  # Skip verification if no secret

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)


@app.route("/webhook/airtable", methods=["POST"])
def handle_webhook():
    # Verify signature
    signature = request.headers.get("X-Airtable-Content-MAC", "")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    data = request.json
    base_id = data.get("base", {}).get("id")
    webhook_id = data.get("webhook", {}).get("id")

    for payload in data.get("payloads", []):
        table_id = payload.get("tableId")
        changed_records = payload.get("changedRecordsById", {})

        for record_id, changes in changed_records.items():
            current = changes.get("current", {})
            previous = changes.get("previous", {})

            # Detect what changed
            current_fields = current.get("cellValuesByFieldId", {})
            previous_fields = previous.get("cellValuesByFieldId", {})

            for field_id, new_value in current_fields.items():
                old_value = previous_fields.get(field_id)
                if new_value != old_value:
                    handle_field_change(
                        table_id=table_id,
                        record_id=record_id,
                        field_id=field_id,
                        old_value=old_value,
                        new_value=new_value
                    )

    return jsonify({"status": "ok"})


def handle_field_change(table_id, record_id, field_id, old_value, new_value):
    """Process a field change event."""
    print(f"Record {record_id} changed: {field_id}")
    print(f"  Old: {old_value}")
    print(f"  New: {new_value}")

    # Add your custom logic here:
    # - Send notifications
    # - Update related records
    # - Trigger external workflows
    # - Log to analytics


if __name__ == "__main__":
    app.run(port=5000, debug=True)
```

## Deduplication Workflow

```python
#!/usr/bin/env python3
"""
Find and merge duplicate records.
"""

import os
from collections import defaultdict
from pyairtable import Api

class Deduplicator:
    def __init__(self, api_key: str, base_id: str, table_name: str):
        self.api = Api(api_key)
        self.table = self.api.table(base_id, table_name)

    def find_duplicates(self, key_field: str, normalize: bool = True) -> dict:
        """
        Find duplicate records based on a key field.

        Args:
            key_field: Field to check for duplicates
            normalize: Lowercase and strip whitespace

        Returns:
            Dict mapping key values to list of record IDs
        """
        records = self.table.all()
        groups = defaultdict(list)

        for record in records:
            value = record["fields"].get(key_field)
            if not value:
                continue

            if normalize:
                value = str(value).lower().strip()

            groups[value].append(record)

        # Filter to only duplicates
        return {k: v for k, v in groups.items() if len(v) > 1}

    def merge_duplicates(
        self,
        key_field: str,
        merge_strategy: str = "keep_first",
        dry_run: bool = True
    ) -> dict:
        """
        Merge duplicate records.

        Args:
            key_field: Field to identify duplicates
            merge_strategy: "keep_first", "keep_last", "keep_most_complete"
            dry_run: If True, only report what would be done

        Returns:
            Dict with merge results
        """
        duplicates = self.find_duplicates(key_field)
        merged = 0
        deleted = 0
        to_delete = []

        for key_value, records in duplicates.items():
            if merge_strategy == "keep_first":
                keeper = records[0]
                dupes = records[1:]
            elif merge_strategy == "keep_last":
                keeper = records[-1]
                dupes = records[:-1]
            elif merge_strategy == "keep_most_complete":
                # Keep record with most non-empty fields
                records.sort(key=lambda r: -len([v for v in r["fields"].values() if v]))
                keeper = records[0]
                dupes = records[1:]
            else:
                raise ValueError(f"Unknown strategy: {merge_strategy}")

            # Merge fields from duplicates into keeper
            merged_fields = dict(keeper["fields"])
            for dupe in dupes:
                for field, value in dupe["fields"].items():
                    if not merged_fields.get(field) and value:
                        merged_fields[field] = value

            if not dry_run:
                # Update keeper with merged fields
                self.table.update(keeper["id"], merged_fields)

                # Delete duplicates
                for dupe in dupes:
                    to_delete.append(dupe["id"])

            merged += 1
            deleted += len(dupes)

        # Batch delete
        if not dry_run and to_delete:
            for i in range(0, len(to_delete), 10):
                self.table.batch_delete(to_delete[i:i+10])

        return {
            "duplicate_groups": len(duplicates),
            "records_merged": merged,
            "records_deleted": deleted,
            "dry_run": dry_run
        }


# Usage
def main():
    dedup = Deduplicator(
        os.environ["AIRTABLE_API_KEY"],
        "appXXXXXX",
        "Contacts"
    )

    # First, preview what would be merged
    result = dedup.merge_duplicates("Email", strategy="keep_most_complete", dry_run=True)
    print(f"Would merge {result['duplicate_groups']} groups, delete {result['records_deleted']} records")

    # Then actually merge
    # result = dedup.merge_duplicates("Email", strategy="keep_most_complete", dry_run=False)


if __name__ == "__main__":
    main()
```

## Report Generator

```python
#!/usr/bin/env python3
"""
Generate reports from Airtable data.
"""

import os
import csv
from datetime import datetime, timedelta
from pyairtable import Api

class ReportGenerator:
    def __init__(self, api_key: str, base_id: str):
        self.api = Api(api_key)
        self.base_id = base_id

    def table(self, name: str):
        return self.api.table(self.base_id, name)

    def daily_summary(self, table_name: str, date_field: str = "Created") -> dict:
        """Generate daily summary statistics."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        table = self.table(table_name)

        today_records = table.all(
            formula=f"IS_SAME({{{date_field}}}, '{today}', 'day')"
        )
        yesterday_records = table.all(
            formula=f"IS_SAME({{{date_field}}}, '{yesterday}', 'day')"
        )
        total_records = table.all()

        return {
            "date": today,
            "new_today": len(today_records),
            "new_yesterday": len(yesterday_records),
            "total": len(total_records),
            "change": len(today_records) - len(yesterday_records)
        }

    def field_breakdown(self, table_name: str, field: str) -> dict:
        """Get count breakdown by field value."""
        table = self.table(table_name)
        records = table.all(fields=[field])

        breakdown = {}
        for record in records:
            value = record["fields"].get(field, "(empty)")
            if isinstance(value, list):
                for v in value:
                    breakdown[v] = breakdown.get(v, 0) + 1
            else:
                breakdown[value] = breakdown.get(value, 0) + 1

        return dict(sorted(breakdown.items(), key=lambda x: -x[1]))

    def export_report(self, data: dict, output_path: str):
        """Export report data to CSV."""
        if isinstance(data, dict) and all(isinstance(v, (int, float, str)) for v in data.values()):
            # Simple key-value report
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                for key, value in data.items():
                    writer.writerow([key, value])
        elif isinstance(data, dict):
            # Breakdown report
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Category", "Count"])
                for key, value in data.items():
                    writer.writerow([key, value])
        elif isinstance(data, list):
            # List of dicts
            if data:
                fieldnames = list(data[0].keys())
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)


# Usage
def main():
    report = ReportGenerator(
        os.environ["AIRTABLE_API_KEY"],
        "appXXXXXX"
    )

    # Daily summary
    summary = report.daily_summary("Contacts")
    print(f"Daily Summary: {summary}")

    # Status breakdown
    breakdown = report.field_breakdown("Contacts", "Status")
    print(f"Status Breakdown: {breakdown}")

    # Export
    report.export_report(breakdown, "status_report.csv")


if __name__ == "__main__":
    main()
```

## Integration Patterns

### Airtable + Google Sheets Sync

```python
#!/usr/bin/env python3
"""
Two-way sync between Airtable and Google Sheets.
Requires: pip install pyairtable gspread oauth2client
"""

import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pyairtable import Api

def sync_airtable_to_sheets(
    airtable_base: str,
    airtable_table: str,
    spreadsheet_id: str,
    worksheet_name: str
):
    # Airtable
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(airtable_base, airtable_table)
    records = table.all()

    # Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    # Clear and write
    if records:
        headers = list(records[0]["fields"].keys())
        rows = [headers]
        for record in records:
            rows.append([record["fields"].get(h, "") for h in headers])

        sheet.clear()
        sheet.update("A1", rows)

    return len(records)
```

### Airtable + Slack Notifications

```python
#!/usr/bin/env python3
"""
Send Slack notifications on Airtable changes.
Requires: pip install pyairtable slack_sdk
"""

import os
from slack_sdk import WebClient
from pyairtable import Api

def notify_new_records(
    base_id: str,
    table_name: str,
    slack_channel: str,
    since_hours: int = 1
):
    from datetime import datetime, timedelta

    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(base_id, table_name)

    # Get recent records
    cutoff = (datetime.now() - timedelta(hours=since_hours)).isoformat()
    records = table.all(
        formula=f"IS_AFTER(CREATED_TIME(), '{cutoff}')"
    )

    if not records:
        return 0

    # Send Slack message
    slack = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"New {table_name} Records"}
        }
    ]

    for record in records[:10]:  # Limit to 10
        fields = record["fields"]
        text = ", ".join(f"{k}: {v}" for k, v in list(fields.items())[:3])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"• {text}"}
        })

    if len(records) > 10:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_...and {len(records) - 10} more_"}]
        })

    slack.chat_postMessage(channel=slack_channel, blocks=blocks)
    return len(records)
```

## Scheduled Jobs with Cron

```bash
# Edit crontab: crontab -e

# Sync every hour
0 * * * * /usr/bin/python3 /path/to/sync_workflow.py >> /var/log/airtable_sync.log 2>&1

# Daily validation at 6 AM
0 6 * * * /usr/bin/python3 /path/to/validate.py >> /var/log/airtable_validate.log 2>&1

# Weekly deduplication on Sundays at midnight
0 0 * * 0 /usr/bin/python3 /path/to/dedupe.py >> /var/log/airtable_dedupe.log 2>&1

# Daily report at 9 AM
0 9 * * * /usr/bin/python3 /path/to/report.py >> /var/log/airtable_report.log 2>&1
```
