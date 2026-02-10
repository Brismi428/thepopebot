---
name: airtable
description: Comprehensive Airtable integration for managing bases, tables, records, and automation workflows. When Claude needs to create, read, update, or delete Airtable records, sync data between bases, bulk import/export data, or build automation workflows with Airtable.
---

# Airtable Integration Guide

## Overview

This skill provides powerful Airtable API integration for:
- CRUD operations on records
- Base and table management
- Bulk operations and data sync
- Advanced filtering, sorting, and views
- Attachment handling
- Automation workflows

For detailed API reference, see [reference.md](reference.md).
For automation workflows, see [automations.md](automations.md).

## Quick Start

```python
# Install dependencies
# pip install pyairtable python-dotenv requests

from pyairtable import Api, Table
import os

# Initialize with API key
api = Api(os.environ["AIRTABLE_API_KEY"])

# Access a table
table = api.table("appXXXXXXXXXXXXXX", "Table Name")

# Get all records
records = table.all()

# Create a record
new_record = table.create({"Name": "John Doe", "Email": "john@example.com"})

# Update a record
table.update(record_id, {"Status": "Active"})

# Delete a record
table.delete(record_id)
```

## Environment Setup

Create a `.env` file or set environment variables:

```env
AIRTABLE_API_KEY=patXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

Get your API key from: https://airtable.com/create/tokens

**Required scopes for Personal Access Token:**
- `data.records:read`
- `data.records:write`
- `schema.bases:read`
- `schema.bases:write` (for table creation)

## Record Operations

### Create Record

```python
from pyairtable import Api
import os

api = Api(os.environ["AIRTABLE_API_KEY"])
table = api.table("appXXXXXX", "Contacts")

# Single record
record = table.create({
    "Name": "Jane Smith",
    "Email": "jane@example.com",
    "Phone": "555-1234",
    "Status": "Lead"
})
print(f"Created: {record['id']}")
```

### Get Records

```python
# All records
records = table.all()

# With formula filter
records = table.all(formula="{Status} = 'Active'")

# With sorting
records = table.all(sort=["Name"])  # Ascending
records = table.all(sort=["-Created"])  # Descending

# With field selection
records = table.all(fields=["Name", "Email"])

# With view
records = table.all(view="Grid view")

# Paginated (max 100 per page)
for records in table.iterate(page_size=100):
    for record in records:
        print(record["fields"])
```

### Update Record

```python
# Update single record
table.update(record_id, {"Status": "Customer", "Notes": "Converted on 2024-01"})

# Update with typecast (auto-convert values)
table.update(record_id, {"Date": "2024-01-15"}, typecast=True)
```

### Delete Record

```python
# Delete single record
table.delete(record_id)

# Delete multiple records
table.batch_delete([record_id_1, record_id_2, record_id_3])
```

## Bulk Operations

### Batch Create (up to 10 records)

```python
records_to_create = [
    {"fields": {"Name": "Alice", "Email": "alice@example.com"}},
    {"fields": {"Name": "Bob", "Email": "bob@example.com"}},
    {"fields": {"Name": "Charlie", "Email": "charlie@example.com"}},
]

created = table.batch_create(records_to_create)
print(f"Created {len(created)} records")
```

### Batch Update

```python
records_to_update = [
    {"id": "recXXXXXX", "fields": {"Status": "Active"}},
    {"id": "recYYYYYY", "fields": {"Status": "Active"}},
]

updated = table.batch_update(records_to_update)
```

### Import from CSV

```python
import csv
from pyairtable import Api

def import_csv_to_airtable(csv_path, base_id, table_name):
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(base_id, table_name)

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        records = [{"fields": row} for row in reader]

    # Batch create in chunks of 10
    created = []
    for i in range(0, len(records), 10):
        batch = records[i:i+10]
        created.extend(table.batch_create(batch))

    return created

# Usage
created = import_csv_to_airtable("contacts.csv", "appXXXXXX", "Contacts")
print(f"Imported {len(created)} records")
```

### Export to CSV

```python
import csv

def export_airtable_to_csv(base_id, table_name, output_path, fields=None):
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(base_id, table_name)

    records = table.all(fields=fields) if fields else table.all()

    if not records:
        print("No records found")
        return

    # Get all field names from first record
    fieldnames = list(records[0]["fields"].keys())

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record["fields"])

    print(f"Exported {len(records)} records to {output_path}")

# Usage
export_airtable_to_csv("appXXXXXX", "Contacts", "export.csv")
```

## Formula Filters

Airtable uses its own formula syntax for filtering:

```python
# Exact match
records = table.all(formula="{Status} = 'Active'")

# Not equal
records = table.all(formula="{Status} != 'Archived'")

# Contains text
records = table.all(formula="FIND('gmail', {Email}) > 0")

# Numeric comparison
records = table.all(formula="{Amount} > 1000")

# Date comparison
records = table.all(formula="IS_AFTER({Created}, '2024-01-01')")

# Multiple conditions (AND)
records = table.all(formula="AND({Status} = 'Active', {Amount} > 100)")

# Multiple conditions (OR)
records = table.all(formula="OR({Status} = 'Lead', {Status} = 'Prospect')")

# Empty/not empty
records = table.all(formula="{Email} = BLANK()")
records = table.all(formula="{Email} != BLANK()")

# Linked record matching
records = table.all(formula="FIND('rec123', ARRAYJOIN({Linked Field})) > 0")
```

## Field Types

### Text Fields
```python
table.create({"Name": "John Doe", "Notes": "Long text here..."})
```

### Number Fields
```python
table.create({"Amount": 99.99, "Quantity": 5})
```

### Single Select
```python
table.create({"Status": "Active"})  # Must match existing option
```

### Multiple Select
```python
table.create({"Tags": ["Important", "Follow-up"]})
```

### Date Fields
```python
table.create({"Due Date": "2024-12-31"})  # ISO format
```

### Checkbox
```python
table.create({"Completed": True})
```

### Linked Records
```python
table.create({"Company": ["recXXXXXX"]})  # Array of record IDs
```

### Attachments
```python
table.create({
    "Documents": [
        {"url": "https://example.com/file.pdf"},
        {"url": "https://example.com/image.png"}
    ]
})
```

## Base & Schema Discovery

### List All Bases

```python
from pyairtable.metadata import get_api_bases

api = Api(os.environ["AIRTABLE_API_KEY"])
bases = get_api_bases(api)

for base in bases:
    print(f"{base.id}: {base.name}")
```

### Get Table Schema

```python
from pyairtable.metadata import get_base_schema

api = Api(os.environ["AIRTABLE_API_KEY"])
schema = get_base_schema(api, "appXXXXXX")

for table in schema.tables:
    print(f"\nTable: {table.name} ({table.id})")
    for field in table.fields:
        print(f"  - {field.name}: {field.type}")
```

## Error Handling

```python
from pyairtable.api.types import AirtableError

try:
    record = table.create({"Invalid Field": "value"})
except AirtableError as e:
    print(f"Airtable error: {e.error_message}")
    print(f"Status code: {e.status_code}")
```

**Common errors:**
- `INVALID_PERMISSIONS` - Check API key scopes
- `NOT_FOUND` - Invalid base/table/record ID
- `INVALID_REQUEST` - Field validation failed
- `RATE_LIMIT_EXCEEDED` - Slow down requests (5/sec limit)

## Rate Limiting

Airtable limits to 5 requests/second. Use delays for bulk operations:

```python
import time

for record in large_record_list:
    table.create(record)
    time.sleep(0.2)  # 200ms delay = 5 requests/sec max
```

Or use the built-in rate limiting:

```python
from pyairtable import Api

api = Api(os.environ["AIRTABLE_API_KEY"])
# pyairtable handles rate limiting automatically
```

## Sync Between Tables

```python
def sync_tables(source_base, source_table, target_base, target_table, key_field="Email"):
    """Sync records from source to target, matching on key_field"""
    api = Api(os.environ["AIRTABLE_API_KEY"])

    source = api.table(source_base, source_table)
    target = api.table(target_base, target_table)

    # Get all source records
    source_records = source.all()

    # Get existing target records indexed by key
    target_records = {r["fields"].get(key_field): r for r in target.all()}

    to_create = []
    to_update = []

    for record in source_records:
        key = record["fields"].get(key_field)
        if not key:
            continue

        if key in target_records:
            # Update existing
            to_update.append({
                "id": target_records[key]["id"],
                "fields": record["fields"]
            })
        else:
            # Create new
            to_create.append({"fields": record["fields"]})

    # Execute in batches
    created = []
    for i in range(0, len(to_create), 10):
        created.extend(target.batch_create(to_create[i:i+10]))

    updated = []
    for i in range(0, len(to_update), 10):
        updated.extend(target.batch_update(to_update[i:i+10]))

    return {"created": len(created), "updated": len(updated)}
```

## Common Patterns

### Upsert (Create or Update)

```python
def upsert_record(table, key_field, key_value, data):
    """Create record if not exists, otherwise update"""
    existing = table.all(formula=f"{{{key_field}}} = '{key_value}'")

    if existing:
        return table.update(existing[0]["id"], data)
    else:
        return table.create({key_field: key_value, **data})
```

### Find Record by ID

```python
def get_record(table, record_id):
    """Get single record by ID"""
    return table.get(record_id)
```

### Search Records

```python
def search_records(table, search_term, search_fields):
    """Search across multiple text fields"""
    conditions = [f"FIND(LOWER('{search_term}'), LOWER({{{f}}})) > 0" for f in search_fields]
    formula = f"OR({', '.join(conditions)})"
    return table.all(formula=formula)

# Usage
results = search_records(table, "john", ["Name", "Email", "Notes"])
```

## Resources

- [Airtable API Documentation](https://airtable.com/developers/web/api/introduction)
- [pyairtable Documentation](https://pyairtable.readthedocs.io/)
- [Airtable Formula Reference](https://support.airtable.com/docs/formula-field-reference)
- [Personal Access Tokens](https://airtable.com/create/tokens)
