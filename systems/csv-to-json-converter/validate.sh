#!/bin/bash
# Three-Level Validation Script for CSV-to-JSON Converter
# Run this script to validate the system before deployment

set -e

echo "============================================"
echo "CSV-to-JSON Converter - Validation Suite"
echo "============================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

echo "============================================"
echo "LEVEL 1: Syntax & Structure"
echo "============================================"
echo ""

# Test each tool file
for tool in tools/*.py; do
    echo "Testing $(basename $tool)..."
    
    # AST parse
    python3 -c "import ast; ast.parse(open('$tool').read())" && \
        echo "  ✓ Valid Python syntax" || \
        (echo "  ✗ Syntax error" && exit 1)
    
    # Check for main() function
    if grep -q "^def main(" "$tool"; then
        echo "  ✓ Has main() function"
    else
        echo "  ⚠ No main() function (may be a module)"
    fi
    
    # Check for docstring
    if head -20 "$tool" | grep -q '"""'; then
        echo "  ✓ Has module docstring"
    else
        echo "  ✗ Missing module docstring"
        exit 1
    fi
    
    # Check for try/except
    if grep -q "try:" "$tool" && grep -q "except" "$tool"; then
        echo "  ✓ Has error handling"
    else
        echo "  ⚠ Limited error handling"
    fi
    
    echo ""
done

# Verify workflow.md structure
echo "Testing workflow.md..."
grep -q "## Inputs" workflow.md && echo "  ✓ Has Inputs section" || (echo "  ✗ Missing Inputs" && exit 1)
grep -q "## Outputs" workflow.md && echo "  ✓ Has Outputs section" || (echo "  ✗ Missing Outputs" && exit 1)
grep -q "Failure" workflow.md && echo "  ✓ Has Failure modes" || (echo "  ✗ Missing Failure modes" && exit 1)
echo ""

# Verify CLAUDE.md structure
echo "Testing CLAUDE.md..."
grep -q "csv-analyzer" CLAUDE.md && echo "  ✓ Documents csv-analyzer" || (echo "  ✗ Missing csv-analyzer" && exit 1)
grep -q "type-inference-specialist" CLAUDE.md && echo "  ✓ Documents type-inference-specialist" || (echo "  ✗ Missing type-inference-specialist" && exit 1)
grep -q "data-validator" CLAUDE.md && echo "  ✓ Documents data-validator" || (echo "  ✗ Missing data-validator" && exit 1)
grep -q "json-writer" CLAUDE.md && echo "  ✓ Documents json-writer" || (echo "  ✗ Missing json-writer" && exit 1)
echo ""

# Verify subagent files
echo "Testing subagent files..."
for agent in .claude/agents/*.md; do
    echo "  Checking $(basename $agent)..."
    
    # Check YAML frontmatter
    if head -10 "$agent" | grep -q "^---$"; then
        echo "    ✓ Has YAML frontmatter"
    else
        echo "    ✗ Missing YAML frontmatter"
        exit 1
    fi
    
    # Check required fields
    grep -q "^name:" "$agent" && echo "    ✓ Has name field" || (echo "    ✗ Missing name" && exit 1)
    grep -q "^description:" "$agent" && echo "    ✓ Has description field" || (echo "    ✗ Missing description" && exit 1)
    grep -q "^tools:" "$agent" && echo "    ✓ Has tools field" || (echo "    ✗ Missing tools" && exit 1)
done
echo ""

echo "✓ Level 1 validation PASSED"
echo ""

echo "============================================"
echo "LEVEL 2: Unit Tests"
echo "============================================"
echo ""

# Create test CSV
mkdir -p /tmp/csv_test
cat > /tmp/csv_test/test.csv << 'EOF'
id,name,active,score,created
1,Alice,true,95.5,2024-01-15
2,Bob,false,87.2,2024-02-20
3,Charlie,yes,92.0,2024-03-10
EOF

echo "Created test CSV with 3 rows"
echo ""

# Test csv_analyzer.py
echo "Testing csv_analyzer.py..."
cd tools
python3 csv_analyzer.py /tmp/csv_test/test.csv > /tmp/csv_test/analysis.json && \
    echo "  ✓ Executed successfully" || \
    (echo "  ✗ Execution failed" && exit 1)

# Verify output structure
python3 -c "
import json
with open('/tmp/csv_test/analysis.json') as f:
    data = json.load(f)
assert 'encoding' in data, 'Missing encoding'
assert 'delimiter' in data, 'Missing delimiter'
assert 'column_count' in data, 'Missing column_count'
assert data['column_count'] == 5, f'Expected 5 columns, got {data[\"column_count\"]}'
print('  ✓ Output structure valid')
" && echo "  ✓ Output contains required fields" || (echo "  ✗ Invalid output" && exit 1)
cd ..
echo ""

# Test converter.py help
echo "Testing converter.py help..."
cd tools
python3 converter.py --help > /dev/null && \
    echo "  ✓ Help command works" || \
    (echo "  ✗ Help command failed" && exit 1)
cd ..
echo ""

echo "✓ Level 2 validation PASSED"
echo ""

echo "============================================"
echo "LEVEL 3: Integration Tests"
echo "============================================"
echo ""

# Test full pipeline
echo "Running full conversion pipeline..."
cd tools
python3 converter.py /tmp/csv_test/test.csv --output-directory /tmp/csv_test/output && \
    echo "  ✓ Conversion completed" || \
    (echo "  ✗ Conversion failed" && exit 1)
cd ..
echo ""

# Verify output files
echo "Verifying output files..."
[ -f /tmp/csv_test/output/test.json ] && echo "  ✓ test.json created" || (echo "  ✗ test.json missing" && exit 1)
[ -f /tmp/csv_test/output/run_summary.json ] && echo "  ✓ run_summary.json created" || (echo "  ✗ run_summary.json missing" && exit 1)
[ -f /tmp/csv_test/output/validation_report.md ] && echo "  ✓ validation_report.md created" || (echo "  ✗ validation_report.md missing" && exit 1)
echo ""

# Verify JSON structure
echo "Verifying JSON output structure..."
python3 -c "
import json
with open('/tmp/csv_test/output/test.json') as f:
    data = json.load(f)
assert isinstance(data, list), 'Expected list'
assert len(data) == 3, f'Expected 3 records, got {len(data)}'
assert data[0]['id'] == 1, 'ID should be int, not string'
assert data[0]['active'] == True, 'Active should be boolean'
print('  ✓ Output structure valid')
print('  ✓ Type inference worked (id=int, active=bool)')
"
echo ""

# Verify run summary
echo "Verifying run summary..."
python3 -c "
import json
with open('/tmp/csv_test/output/run_summary.json') as f:
    summary = json.load(f)
assert summary['files_processed'] == 1, 'Expected 1 file processed'
assert summary['successful'] == 1, 'Expected 1 successful file'
assert summary['failed'] == 0, 'Expected 0 failed files'
assert summary['total_rows'] == 3, 'Expected 3 total rows'
print('  ✓ Run summary valid')
"
echo ""

# Check for hardcoded secrets
echo "Checking for hardcoded secrets..."
if grep -r "sk-\|api_key=\|bearer " tools/ --exclude="*.pyc"; then
    echo "  ✗ Hardcoded secret found"
    exit 1
else
    echo "  ✓ No hardcoded secrets"
fi
echo ""

# Verify workflow references match tools
echo "Verifying workflow references..."
python3 -c "
import re
import os

# Get tool names from workflow.md
with open('workflow.md') as f:
    workflow = f.read()
tool_refs = set(re.findall(r'(\w+\.py)', workflow))

# Get actual tool files
actual_tools = set(os.listdir('tools'))
actual_tools = {t for t in actual_tools if t.endswith('.py') and not t.startswith('__')}

# Check all references exist
for ref in tool_refs:
    if ref not in actual_tools:
        print(f'  ✗ workflow.md references {ref} which does not exist')
        exit(1)

print('  ✓ All workflow tool references exist')
"
echo ""

echo "✓ Level 3 validation PASSED"
echo ""

echo "============================================"
echo "VALIDATION COMPLETE"
echo "============================================"
echo ""
echo "✅ All three validation levels passed!"
echo ""
echo "The system is ready for deployment."
echo ""

# Cleanup
rm -rf /tmp/csv_test
