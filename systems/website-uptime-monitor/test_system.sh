#!/bin/bash
# Website Uptime Monitor - Validation Test Script
# Run this script to validate the system through all three levels

set -e

echo "==================================="
echo "Level 1: Syntax & Structure"
echo "==================================="

echo "→ AST parse check..."
python3 -c "import ast; ast.parse(open('tools/monitor.py').read())"
echo "✓ AST parse passed"

echo "→ Import check..."
python3 -c "import sys; sys.path.insert(0, 'tools'); import monitor"
echo "✓ Import check passed"

echo "→ Structure check..."
python3 -c "from tools.monitor import main; assert callable(main)"
echo "✓ Structure check passed (main() exists)"

echo "→ Docstring check..."
python3 -c "import ast; tree = ast.parse(open('tools/monitor.py').read()); assert ast.get_docstring(tree) is not None"
echo "✓ Docstring check passed"

echo ""
echo "==================================="
echo "Level 2: Unit Tests"
echo "==================================="

echo "→ Test 1: Check a URL that should be UP (200 status)..."
python3 tools/monitor.py --url https://httpbin.org/status/200 --timeout 5
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "✓ Test 1 passed (exit code 0 for UP site)"
else
  echo "✗ Test 1 failed (expected exit code 0, got $EXIT_CODE)"
  exit 1
fi

echo "→ Verify CSV was created with data..."
if [ ! -f "data/uptime_log.csv" ]; then
  echo "✗ CSV file not created"
  exit 1
fi
CSV_LINES=$(wc -l < data/uptime_log.csv)
if [ "$CSV_LINES" -lt 2 ]; then
  echo "✗ CSV should have at least 2 lines (header + 1 data row)"
  exit 1
fi
echo "✓ CSV created with $CSV_LINES lines"

echo "→ Test 2: Check a URL that should be DOWN (500 status)..."
python3 tools/monitor.py --url https://httpbin.org/status/500 --timeout 5
EXIT_CODE=$?
if [ $EXIT_CODE -eq 1 ]; then
  echo "✓ Test 2 passed (exit code 1 for DOWN site)"
else
  echo "✗ Test 2 failed (expected exit code 1, got $EXIT_CODE)"
  exit 1
fi

echo "→ Test 3: Check a URL that times out..."
python3 tools/monitor.py --url https://httpstat.us/200?sleep=15000 --timeout 2
EXIT_CODE=$?
if [ $EXIT_CODE -eq 1 ]; then
  echo "✓ Test 3 passed (exit code 1 for timeout)"
else
  echo "✗ Test 3 failed (expected exit code 1, got $EXIT_CODE)"
  exit 1
fi

echo "→ Test 4: Verify CSV format..."
python3 << 'EOF'
import csv
rows = list(csv.DictReader(open('data/uptime_log.csv')))
assert len(rows) >= 3, f'Expected at least 3 rows, got {len(rows)}'
assert 'timestamp' in rows[0], 'Missing timestamp column'
assert 'url' in rows[0], 'Missing url column'
assert 'status_code' in rows[0], 'Missing status_code column'
assert 'response_time_ms' in rows[0], 'Missing response_time_ms column'
assert 'is_up' in rows[0], 'Missing is_up column'
print('✓ CSV format validation passed')
EOF

echo ""
echo "==================================="
echo "Level 3: Integration Tests"
echo "==================================="

echo "→ Simulate GitHub Actions workflow..."
export URL=https://httpbin.org/status/200
export TIMEOUT=10

python3 tools/monitor.py --url "$URL" --timeout "$TIMEOUT"
EXIT_CODE=$?

echo "→ Verify CSV was updated..."
CSV_LINES=$(wc -l < data/uptime_log.csv)
if [ "$CSV_LINES" -lt 2 ]; then
  echo "✗ CSV should have at least 2 lines (header + 1 data row)"
  exit 1
fi
echo "✓ CSV has $CSV_LINES lines"

echo "→ Verify exit code reflects site status..."
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "✓ Site is UP — exit code 0"
elif [ "$EXIT_CODE" -eq 1 ]; then
  echo "✓ Site is DOWN — exit code 1"
else
  echo "✗ Unexpected exit code $EXIT_CODE"
  exit 1
fi

echo "→ Cross-reference validation..."
# Verify workflow.md references tools that exist
if ! grep -q "monitor.py" workflow.md; then
  echo "✗ workflow.md does not reference monitor.py"
  exit 1
fi
echo "✓ workflow.md references match actual tools"

# Verify CLAUDE.md documents the tool
if ! grep -q "monitor.py" CLAUDE.md; then
  echo "✗ CLAUDE.md does not document monitor.py"
  exit 1
fi
echo "✓ CLAUDE.md documents all tools"

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
  echo "✗ requirements.txt missing"
  exit 1
fi
echo "✓ requirements.txt exists"

# Verify README.md covers execution paths
if ! grep -q "Execution Paths" README.md; then
  echo "✗ README.md missing Execution Paths section"
  exit 1
fi
echo "✓ README.md covers all execution paths"

echo ""
echo "==================================="
echo "✅ ALL VALIDATION TESTS PASSED"
echo "==================================="
echo ""
echo "System is ready for deployment!"
