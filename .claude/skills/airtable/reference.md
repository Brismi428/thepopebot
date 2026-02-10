# Airtable API Reference

## pyairtable Library Reference

### Installation

```bash
pip install pyairtable python-dotenv requests
```

### Api Class

The main entry point for all Airtable operations.

```python
from pyairtable import Api

# Initialize
api = Api("patXXXXXXXXXXXXXX")

# Or from environment
import os
api = Api(os.environ["AIRTABLE_API_KEY"])

# Access a table
table = api.table("appXXXXXX", "Table Name")

# Access base metadata
base = api.base("appXXXXXX")
```

### Table Class Methods

#### `table.all(**options)`
Retrieve all records from the table.

**Parameters:**
- `formula` (str): Airtable formula for filtering
- `sort` (list): Field names to sort by (prefix with `-` for descending)
- `fields` (list): Field names to return
- `view` (str): Name of view to use
- `max_records` (int): Maximum records to return
- `page_size` (int): Records per page (max 100)

**Returns:** List of record dicts

```python
# Examples
records = table.all()
records = table.all(formula="{Status} = 'Active'", sort=["Name"], fields=["Name", "Email"])
records = table.all(view="Active Contacts", max_records=50)
```

#### `table.first(**options)`
Get the first matching record.

```python
record = table.first(formula="{Email} = 'john@example.com'")
```

#### `table.get(record_id)`
Get a single record by ID.

```python
record = table.get("recXXXXXXXXXXXXXX")
# Returns: {"id": "recXXX", "createdTime": "...", "fields": {...}}
```

#### `table.iterate(**options)`
Iterate through records in pages.

```python
for page in table.iterate(page_size=100):
    for record in page:
        process(record)
```

#### `table.create(fields, typecast=False)`
Create a new record.

**Parameters:**
- `fields` (dict): Field name to value mapping
- `typecast` (bool): Auto-convert values to field types

```python
record = table.create({
    "Name": "John Doe",
    "Email": "john@example.com",
    "Amount": 100
})
# Returns: {"id": "recXXX", "createdTime": "...", "fields": {...}}
```

#### `table.update(record_id, fields, typecast=False)`
Update an existing record.

```python
record = table.update("recXXXXXX", {"Status": "Complete"})
```

#### `table.delete(record_id)`
Delete a record.

```python
deleted = table.delete("recXXXXXX")
# Returns: {"id": "recXXX", "deleted": True}
```

#### `table.batch_create(records, typecast=False)`
Create multiple records (max 10 per call).

```python
records = table.batch_create([
    {"fields": {"Name": "Alice"}},
    {"fields": {"Name": "Bob"}},
])
```

#### `table.batch_update(records, typecast=False)`
Update multiple records (max 10 per call).

```python
records = table.batch_update([
    {"id": "recXXX", "fields": {"Status": "Active"}},
    {"id": "recYYY", "fields": {"Status": "Active"}},
])
```

#### `table.batch_delete(record_ids)`
Delete multiple records (max 10 per call).

```python
deleted = table.batch_delete(["recXXX", "recYYY", "recZZZ"])
```

#### `table.batch_upsert(records, key_fields, typecast=False)`
Create or update records based on key fields.

```python
records = table.batch_upsert(
    [
        {"fields": {"Email": "john@example.com", "Name": "John"}},
        {"fields": {"Email": "jane@example.com", "Name": "Jane"}},
    ],
    key_fields=["Email"]
)
```

## Metadata API

### Get All Bases

```python
from pyairtable.metadata import get_api_bases

bases = get_api_bases(api)
for base in bases:
    print(f"ID: {base.id}")
    print(f"Name: {base.name}")
    print(f"Permission: {base.permission_level}")
```

### Get Base Schema

```python
from pyairtable.metadata import get_base_schema

schema = get_base_schema(api, "appXXXXXX")

for table in schema.tables:
    print(f"\n=== {table.name} ===")
    print(f"ID: {table.id}")
    print(f"Primary Field: {table.primary_field_id}")

    print("\nFields:")
    for field in table.fields:
        print(f"  {field.name} ({field.type})")
        if hasattr(field, 'options'):
            print(f"    Options: {field.options}")

    print("\nViews:")
    for view in table.views:
        print(f"  {view.name} ({view.type})")
```

### Create Table

```python
from pyairtable.metadata import create_table

table_schema = create_table(
    api,
    "appXXXXXX",
    "New Table",
    fields=[
        {"name": "Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "Status", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Active", "color": "greenLight2"},
                {"name": "Inactive", "color": "redLight2"},
            ]
        }},
        {"name": "Amount", "type": "number", "options": {
            "precision": 2
        }},
        {"name": "Created", "type": "dateTime", "options": {
            "dateFormat": {"name": "iso"},
            "timeFormat": {"name": "24hour"}
        }},
    ]
)
```

## Field Type Reference

### Text Fields

| Type | Description | Options |
|------|-------------|---------|
| `singleLineText` | Single line text | None |
| `multilineText` | Multi-line text | None |
| `richText` | Rich text with formatting | None |
| `email` | Email address | None |
| `url` | URL | None |
| `phoneNumber` | Phone number | None |

### Number Fields

| Type | Description | Options |
|------|-------------|---------|
| `number` | Decimal number | `precision` (0-8) |
| `currency` | Currency value | `precision`, `symbol` |
| `percent` | Percentage | `precision` |
| `rating` | Star rating | `max` (1-10), `icon` |
| `duration` | Time duration | `durationFormat` |

### Date/Time Fields

| Type | Description | Options |
|------|-------------|---------|
| `date` | Date only | `dateFormat` |
| `dateTime` | Date and time | `dateFormat`, `timeFormat`, `timeZone` |
| `createdTime` | Auto created time | Read-only |
| `lastModifiedTime` | Auto modified time | Read-only |

### Selection Fields

| Type | Description | Options |
|------|-------------|---------|
| `singleSelect` | Single option | `choices` array |
| `multipleSelects` | Multiple options | `choices` array |
| `checkbox` | Boolean checkbox | None |

### Linked Fields

| Type | Description | Options |
|------|-------------|---------|
| `multipleRecordLinks` | Link to records | `linkedTableId`, `isReversed` |
| `lookup` | Lookup from linked | `recordLinkFieldId`, `fieldIdInLinkedTable` |
| `rollup` | Aggregate linked | `recordLinkFieldId`, `fieldIdInLinkedTable`, `referencedFieldIds` |
| `count` | Count linked records | `recordLinkFieldId` |

### Other Fields

| Type | Description | Options |
|------|-------------|---------|
| `multipleAttachments` | File attachments | None |
| `barcode` | Barcode/QR code | None |
| `button` | Action button | `label`, `style` |
| `formula` | Calculated field | `formula` (read-only) |
| `autoNumber` | Auto-increment | Read-only |
| `createdBy` | Created by user | Read-only |
| `lastModifiedBy` | Modified by user | Read-only |

## Formula Reference

### Text Functions

```
CONCATENATE(text1, text2, ...)  - Join text
FIND(needle, haystack)          - Find position (1-indexed, 0 if not found)
LEFT(text, count)               - Left characters
RIGHT(text, count)              - Right characters
MID(text, start, count)         - Substring
LEN(text)                       - Length
LOWER(text)                     - Lowercase
UPPER(text)                     - Uppercase
TRIM(text)                      - Remove whitespace
SUBSTITUTE(text, old, new)      - Replace text
REGEX_MATCH(text, regex)        - Regex match
REGEX_EXTRACT(text, regex)      - Extract regex match
REGEX_REPLACE(text, regex, new) - Replace with regex
```

### Numeric Functions

```
SUM(num1, num2, ...)      - Add numbers
AVERAGE(num1, num2, ...)  - Average
MAX(num1, num2, ...)      - Maximum
MIN(num1, num2, ...)      - Minimum
ROUND(num, precision)     - Round
ROUNDUP(num, precision)   - Round up
ROUNDDOWN(num, precision) - Round down
CEILING(num, significance) - Round up to significance
FLOOR(num, significance)  - Round down to significance
ABS(num)                  - Absolute value
MOD(num, divisor)         - Remainder
POWER(base, power)        - Exponent
SQRT(num)                 - Square root
LOG(num, base)            - Logarithm
EXP(num)                  - e^num
```

### Date Functions

```
TODAY()                           - Current date
NOW()                            - Current datetime
DATEADD(date, count, units)      - Add to date (days/months/years)
DATETIME_DIFF(date1, date2, units) - Difference between dates
DATETIME_FORMAT(date, format)    - Format date
DATETIME_PARSE(text, format)     - Parse date string
YEAR(date)                       - Extract year
MONTH(date)                      - Extract month
DAY(date)                        - Extract day
HOUR(datetime)                   - Extract hour
MINUTE(datetime)                 - Extract minute
SECOND(datetime)                 - Extract second
WEEKDAY(date)                    - Day of week (0=Sun)
WEEKNUM(date)                    - Week number
IS_BEFORE(date1, date2)          - date1 < date2
IS_AFTER(date1, date2)           - date1 > date2
IS_SAME(date1, date2, unit)      - Same day/month/year
```

### Logical Functions

```
IF(condition, true_val, false_val)  - Conditional
AND(cond1, cond2, ...)              - All true
OR(cond1, cond2, ...)               - Any true
NOT(condition)                      - Negate
XOR(cond1, cond2, ...)              - Exclusive or
SWITCH(expr, case1, val1, ..., default) - Switch statement
BLANK()                             - Empty value
ERROR()                             - Error value
```

### Array Functions

```
ARRAYJOIN(array, separator)   - Join array to text
ARRAYCOMPACT(array)           - Remove empty values
ARRAYUNIQUE(array)            - Unique values
ARRAYFLATTEN(array)           - Flatten nested arrays
ARRAYSLICE(array, start, end) - Slice array
```

### Record Functions

```
RECORD_ID()           - Current record ID
CREATED_TIME()        - Record created time
LAST_MODIFIED_TIME()  - Record modified time
```

## Common Filter Formulas

```python
# Text matching
formula = "{Name} = 'John Doe'"
formula = "FIND('john', LOWER({Name})) > 0"  # Case-insensitive contains

# Numeric comparison
formula = "{Amount} > 100"
formula = "{Amount} >= 50 AND {Amount} <= 100"  # Range

# Date filters
formula = "{Due Date} = TODAY()"
formula = "IS_BEFORE({Due Date}, TODAY())"  # Overdue
formula = "IS_AFTER({Created}, DATEADD(TODAY(), -7, 'days'))"  # Last 7 days

# Empty/not empty
formula = "{Email} = BLANK()"
formula = "{Email} != BLANK()"

# Single select
formula = "{Status} = 'Active'"
formula = "OR({Status} = 'Active', {Status} = 'Pending')"

# Multiple select (contains)
formula = "FIND('Tag1', ARRAYJOIN({Tags})) > 0"

# Checkbox
formula = "{Completed} = TRUE()"
formula = "{Completed} = FALSE()"

# Linked records
formula = "{Company} != BLANK()"  # Has linked record
formula = "FIND('recXXX', ARRAYJOIN(RECORD_ID({Company}))) > 0"  # Specific link

# Complex conditions
formula = "AND({Status} = 'Active', {Amount} > 100, IS_BEFORE({Due Date}, TODAY()))"
```

## Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 401 | `AUTHENTICATION_REQUIRED` | Check API key |
| 403 | `NOT_AUTHORIZED` | Check token scopes |
| 404 | `NOT_FOUND` | Check base/table/record ID |
| 413 | `REQUEST_ENTITY_TOO_LARGE` | Reduce payload size |
| 422 | `INVALID_REQUEST` | Check field names/values |
| 422 | `UNKNOWN_FIELD_NAME` | Field doesn't exist |
| 422 | `INVALID_VALUE_FOR_COLUMN` | Wrong value type |
| 429 | `RATE_LIMIT_EXCEEDED` | Slow down (5 req/sec) |
| 500 | `SERVER_ERROR` | Retry later |
| 503 | `SERVICE_UNAVAILABLE` | Retry later |

## Webhook Events

Airtable webhooks notify on record changes:

```python
import requests

# Create webhook
webhook = requests.post(
    f"https://api.airtable.com/v0/bases/{base_id}/webhooks",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "notificationUrl": "https://your-server.com/webhook",
        "specification": {
            "options": {
                "filters": {
                    "dataTypes": ["tableData"],
                    "recordChangeScope": "tblXXXXXX"  # Table ID
                }
            }
        }
    }
)
```

Webhook payload structure:
```json
{
  "base": {"id": "appXXX"},
  "webhook": {"id": "achXXX"},
  "timestamp": "2024-01-15T10:30:00.000Z",
  "payloads": [{
    "tableId": "tblXXX",
    "changedRecordsById": {
      "recXXX": {
        "current": {"cellValuesByFieldId": {...}},
        "previous": {"cellValuesByFieldId": {...}}
      }
    }
  }]
}
```
