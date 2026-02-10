#!/usr/bin/env python3
"""
Airtable Client - A comprehensive Python client for Airtable API operations.

Usage:
    from airtable_client import AirtableClient

    client = AirtableClient()
    records = client.get_records("appXXXXXX", "Table Name")
"""

import os
import time
import csv
import json
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass
from datetime import datetime

try:
    from pyairtable import Api
    from pyairtable.metadata import get_api_bases, get_base_schema
except ImportError:
    raise ImportError("Please install pyairtable: pip install pyairtable")


@dataclass
class SyncResult:
    """Result of a sync operation."""
    created: int
    updated: int
    deleted: int
    skipped: int
    errors: List[str]


class AirtableClient:
    """
    Comprehensive Airtable API client with common operations.

    Environment Variables:
        AIRTABLE_API_KEY: Your Airtable Personal Access Token
        AIRTABLE_BASE_ID: Default base ID (optional)
    """

    def __init__(self, api_key: Optional[str] = None, default_base: Optional[str] = None):
        """
        Initialize the Airtable client.

        Args:
            api_key: Airtable API key (or set AIRTABLE_API_KEY env var)
            default_base: Default base ID (or set AIRTABLE_BASE_ID env var)
        """
        self.api_key = api_key or os.environ.get("AIRTABLE_API_KEY")
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY environment variable or api_key parameter required")

        self.api = Api(self.api_key)
        self.default_base = default_base or os.environ.get("AIRTABLE_BASE_ID")
        self._rate_limit_delay = 0.2  # 5 requests per second

    def _get_table(self, base_id: Optional[str], table_name: str):
        """Get table object, using default base if not specified."""
        base = base_id or self.default_base
        if not base:
            raise ValueError("base_id required (no default set)")
        return self.api.table(base, table_name)

    # ==========================================================================
    # Record Operations
    # ==========================================================================

    def get_records(
        self,
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        formula: Optional[str] = None,
        sort: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        view: Optional[str] = None,
        max_records: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get records from a table.

        Args:
            base_id: Base ID (uses default if not specified)
            table_name: Table name
            formula: Airtable formula filter
            sort: List of field names to sort by (prefix with - for descending)
            fields: List of field names to return
            view: View name to use
            max_records: Maximum records to return

        Returns:
            List of record dicts with id, createdTime, and fields
        """
        table = self._get_table(base_id, table_name)
        return table.all(
            formula=formula,
            sort=sort,
            fields=fields,
            view=view,
            max_records=max_records
        )

    def get_record(
        self,
        record_id: str,
        base_id: Optional[str] = None,
        table_name: str = ""
    ) -> Dict[str, Any]:
        """Get a single record by ID."""
        table = self._get_table(base_id, table_name)
        return table.get(record_id)

    def find_record(
        self,
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        formula: str
    ) -> Optional[Dict[str, Any]]:
        """Find first record matching formula."""
        table = self._get_table(base_id, table_name)
        return table.first(formula=formula)

    def create_record(
        self,
        fields: Dict[str, Any],
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        typecast: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new record.

        Args:
            fields: Field name to value mapping
            base_id: Base ID
            table_name: Table name
            typecast: Auto-convert values to field types

        Returns:
            Created record dict
        """
        table = self._get_table(base_id, table_name)
        return table.create(fields, typecast=typecast)

    def update_record(
        self,
        record_id: str,
        fields: Dict[str, Any],
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        typecast: bool = False
    ) -> Dict[str, Any]:
        """Update an existing record."""
        table = self._get_table(base_id, table_name)
        return table.update(record_id, fields, typecast=typecast)

    def delete_record(
        self,
        record_id: str,
        base_id: Optional[str] = None,
        table_name: str = ""
    ) -> Dict[str, Any]:
        """Delete a record."""
        table = self._get_table(base_id, table_name)
        return table.delete(record_id)

    def upsert_record(
        self,
        key_field: str,
        key_value: Any,
        fields: Dict[str, Any],
        base_id: Optional[str] = None,
        table_name: str = ""
    ) -> Dict[str, Any]:
        """
        Create or update a record based on key field.

        Args:
            key_field: Field to match on
            key_value: Value to match
            fields: Fields to set
            base_id: Base ID
            table_name: Table name

        Returns:
            Created or updated record
        """
        table = self._get_table(base_id, table_name)

        # Escape single quotes in value
        safe_value = str(key_value).replace("'", "\\'")
        existing = table.first(formula=f"{{{key_field}}} = '{safe_value}'")

        if existing:
            return table.update(existing["id"], fields)
        else:
            return table.create({key_field: key_value, **fields})

    # ==========================================================================
    # Bulk Operations
    # ==========================================================================

    def batch_create(
        self,
        records: List[Dict[str, Any]],
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        batch_size: int = 10,
        typecast: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Create multiple records in batches.

        Args:
            records: List of field dicts to create
            base_id: Base ID
            table_name: Table name
            batch_size: Records per batch (max 10)
            typecast: Auto-convert values

        Returns:
            List of created records
        """
        table = self._get_table(base_id, table_name)
        created = []

        # Ensure proper format
        formatted = [
            r if "fields" in r else {"fields": r}
            for r in records
        ]

        for i in range(0, len(formatted), batch_size):
            batch = formatted[i:i + batch_size]
            created.extend(table.batch_create(batch, typecast=typecast))
            time.sleep(self._rate_limit_delay)

        return created

    def batch_update(
        self,
        records: List[Dict[str, Any]],
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        batch_size: int = 10,
        typecast: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Update multiple records in batches.

        Args:
            records: List of {"id": "recXXX", "fields": {...}} dicts
            base_id: Base ID
            table_name: Table name
            batch_size: Records per batch (max 10)
            typecast: Auto-convert values

        Returns:
            List of updated records
        """
        table = self._get_table(base_id, table_name)
        updated = []

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            updated.extend(table.batch_update(batch, typecast=typecast))
            time.sleep(self._rate_limit_delay)

        return updated

    def batch_delete(
        self,
        record_ids: List[str],
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Delete multiple records in batches."""
        table = self._get_table(base_id, table_name)
        deleted = []

        for i in range(0, len(record_ids), batch_size):
            batch = record_ids[i:i + batch_size]
            deleted.extend(table.batch_delete(batch))
            time.sleep(self._rate_limit_delay)

        return deleted

    # ==========================================================================
    # Import/Export
    # ==========================================================================

    def import_csv(
        self,
        csv_path: str,
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        field_mapping: Optional[Dict[str, str]] = None,
        typecast: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Import records from CSV file.

        Args:
            csv_path: Path to CSV file
            base_id: Base ID
            table_name: Table name
            field_mapping: Optional {csv_column: airtable_field} mapping
            typecast: Auto-convert values

        Returns:
            List of created records
        """
        records = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if field_mapping:
                    fields = {
                        field_mapping.get(k, k): v
                        for k, v in row.items()
                        if v and field_mapping.get(k, k) is not None
                    }
                else:
                    fields = {k: v for k, v in row.items() if v}
                records.append(fields)

        return self.batch_create(records, base_id, table_name, typecast=typecast)

    def export_csv(
        self,
        output_path: str,
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        fields: Optional[List[str]] = None,
        formula: Optional[str] = None
    ) -> int:
        """
        Export records to CSV file.

        Args:
            output_path: Output CSV path
            base_id: Base ID
            table_name: Table name
            fields: Fields to export (all if None)
            formula: Filter formula

        Returns:
            Number of records exported
        """
        records = self.get_records(base_id, table_name, fields=fields, formula=formula)

        if not records:
            return 0

        # Get all unique field names
        fieldnames = []
        for record in records:
            for key in record["fields"].keys():
                if key not in fieldnames:
                    fieldnames.append(key)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record["fields"])

        return len(records)

    def import_json(
        self,
        json_path: str,
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        typecast: bool = True
    ) -> List[Dict[str, Any]]:
        """Import records from JSON file (array of field dicts)."""
        with open(json_path, 'r', encoding='utf-8') as f:
            records = json.load(f)

        return self.batch_create(records, base_id, table_name, typecast=typecast)

    def export_json(
        self,
        output_path: str,
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        fields: Optional[List[str]] = None,
        formula: Optional[str] = None,
        include_metadata: bool = False
    ) -> int:
        """
        Export records to JSON file.

        Args:
            output_path: Output JSON path
            include_metadata: Include id and createdTime

        Returns:
            Number of records exported
        """
        records = self.get_records(base_id, table_name, fields=fields, formula=formula)

        if include_metadata:
            output = records
        else:
            output = [r["fields"] for r in records]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, default=str)

        return len(records)

    # ==========================================================================
    # Sync Operations
    # ==========================================================================

    def sync_to_table(
        self,
        source_records: List[Dict[str, Any]],
        key_field: str,
        target_base: Optional[str] = None,
        target_table: str = "",
        *,
        field_mapping: Optional[Dict[str, str]] = None,
        delete_missing: bool = False
    ) -> SyncResult:
        """
        Sync records to target table.

        Args:
            source_records: List of field dicts to sync
            key_field: Field to match on
            target_base: Target base ID
            target_table: Target table name
            field_mapping: Optional field name mapping
            delete_missing: Delete records not in source

        Returns:
            SyncResult with counts
        """
        table = self._get_table(target_base, target_table)

        # Get existing records indexed by key
        existing = {}
        for record in table.all():
            key = record["fields"].get(key_field)
            if key:
                existing[key] = record

        to_create = []
        to_update = []
        errors = []
        skipped = 0

        for source in source_records:
            # Apply field mapping
            if field_mapping:
                fields = {
                    field_mapping.get(k, k): v
                    for k, v in source.items()
                    if field_mapping.get(k, k) is not None
                }
            else:
                fields = source

            key = fields.get(key_field)
            if not key:
                skipped += 1
                continue

            if key in existing:
                to_update.append({
                    "id": existing[key]["id"],
                    "fields": fields
                })
                del existing[key]  # Mark as processed
            else:
                to_create.append({"fields": fields})

        # Execute operations
        created = self.batch_create(to_create, target_base, target_table) if to_create else []
        updated = self.batch_update(to_update, target_base, target_table) if to_update else []

        # Delete orphaned records
        deleted = []
        if delete_missing and existing:
            orphan_ids = [r["id"] for r in existing.values()]
            deleted = self.batch_delete(orphan_ids, target_base, target_table)

        return SyncResult(
            created=len(created),
            updated=len(updated),
            deleted=len(deleted),
            skipped=skipped,
            errors=errors
        )

    # ==========================================================================
    # Metadata
    # ==========================================================================

    def list_bases(self) -> List[Dict[str, str]]:
        """List all accessible bases."""
        bases = get_api_bases(self.api)
        return [{"id": b.id, "name": b.name} for b in bases]

    def get_schema(self, base_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get base schema with tables and fields.

        Returns:
            Dict with tables, each containing fields and views
        """
        base = base_id or self.default_base
        if not base:
            raise ValueError("base_id required")

        schema = get_base_schema(self.api, base)
        result = {"tables": []}

        for table in schema.tables:
            table_info = {
                "id": table.id,
                "name": table.name,
                "primary_field_id": table.primary_field_id,
                "fields": [],
                "views": []
            }

            for field in table.fields:
                field_info = {
                    "id": field.id,
                    "name": field.name,
                    "type": field.type
                }
                if hasattr(field, 'options') and field.options:
                    field_info["options"] = field.options
                table_info["fields"].append(field_info)

            for view in table.views:
                table_info["views"].append({
                    "id": view.id,
                    "name": view.name,
                    "type": view.type
                })

            result["tables"].append(table_info)

        return result

    # ==========================================================================
    # Search
    # ==========================================================================

    def search(
        self,
        query: str,
        search_fields: List[str],
        base_id: Optional[str] = None,
        table_name: str = "",
        *,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search records across multiple fields.

        Args:
            query: Search string
            search_fields: Fields to search in
            base_id: Base ID
            table_name: Table name
            case_sensitive: Case-sensitive search

        Returns:
            List of matching records
        """
        if case_sensitive:
            conditions = [
                f"FIND('{query}', {{{f}}}) > 0"
                for f in search_fields
            ]
        else:
            conditions = [
                f"FIND(LOWER('{query}'), LOWER({{{f}}})) > 0"
                for f in search_fields
            ]

        formula = f"OR({', '.join(conditions)})"
        return self.get_records(base_id, table_name, formula=formula)


# ==========================================================================
# CLI Interface
# ==========================================================================

def main():
    """Command-line interface for common operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Airtable CLI")
    parser.add_argument("--base", "-b", help="Base ID")
    parser.add_argument("--table", "-t", help="Table name")

    subparsers = parser.add_subparsers(dest="command")

    # List bases
    subparsers.add_parser("bases", help="List all bases")

    # Schema
    subparsers.add_parser("schema", help="Show table schema")

    # Get records
    get_parser = subparsers.add_parser("get", help="Get records")
    get_parser.add_argument("--formula", "-f", help="Filter formula")
    get_parser.add_argument("--limit", "-l", type=int, help="Max records")

    # Export
    export_parser = subparsers.add_parser("export", help="Export to file")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument("--format", choices=["csv", "json"], default="csv")

    # Import
    import_parser = subparsers.add_parser("import", help="Import from file")
    import_parser.add_argument("input", help="Input file path")

    args = parser.parse_args()
    client = AirtableClient(default_base=args.base)

    if args.command == "bases":
        bases = client.list_bases()
        for base in bases:
            print(f"{base['id']}: {base['name']}")

    elif args.command == "schema":
        schema = client.get_schema()
        for table in schema["tables"]:
            print(f"\n=== {table['name']} ===")
            for field in table["fields"]:
                print(f"  {field['name']}: {field['type']}")

    elif args.command == "get":
        records = client.get_records(
            table_name=args.table,
            formula=args.formula,
            max_records=args.limit
        )
        for record in records:
            print(json.dumps(record["fields"], indent=2))

    elif args.command == "export":
        if args.format == "csv":
            count = client.export_csv(args.output, table_name=args.table)
        else:
            count = client.export_json(args.output, table_name=args.table)
        print(f"Exported {count} records to {args.output}")

    elif args.command == "import":
        if args.input.endswith(".json"):
            records = client.import_json(args.input, table_name=args.table)
        else:
            records = client.import_csv(args.input, table_name=args.table)
        print(f"Imported {len(records)} records")


if __name__ == "__main__":
    main()
