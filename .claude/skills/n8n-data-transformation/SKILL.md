---
name: n8n-data-transformation
description: "Expert knowledge for data manipulation, transformation, and mapping in n8n workflows. Activates when: transforming JSON, mapping data, restructuring objects, filtering arrays."
version: 1.0.0
---

# n8n Data Transformation Skill

## Overview

Master data transformation in n8n using expressions, Set nodes, Code nodes, and specialized transformation nodes.

---

## Transformation Nodes

### Set Node
Best for: Simple field mapping and restructuring

```json
{
  "type": "n8n-nodes-base.set",
  "parameters": {
    "mode": "manual",
    "duplicateItem": false,
    "assignments": {
      "assignments": [
        {
          "name": "fullName",
          "value": "={{ $json.firstName }} {{ $json.lastName }}",
          "type": "string"
        },
        {
          "name": "processed",
          "value": true,
          "type": "boolean"
        }
      ]
    },
    "options": {
      "includeBinary": false
    }
  }
}
```

### Code Node
Best for: Complex transformations, loops, conditionals

```javascript
// Transform all items
const items = $input.all();

return items.map(item => ({
  json: {
    id: item.json.id,
    fullName: `${item.json.first} ${item.json.last}`,
    email: item.json.email.toLowerCase(),
    createdAt: new Date(item.json.created).toISOString()
  }
}));
```

### Item Lists Node
Best for: Array operations (split, aggregate, sort)

```json
{
  "type": "n8n-nodes-base.itemLists",
  "parameters": {
    "operation": "splitOutItems",
    "fieldToSplitOut": "items",
    "options": {}
  }
}
```

---

## Expression Patterns

### Object Access
```javascript
// Direct access
{{ $json.field }}

// Nested access
{{ $json.user.address.city }}

// With default
{{ $json.field || 'default' }}

// Dynamic key
{{ $json[$json.keyName] }}
```

### Array Operations
```javascript
// First item
{{ $json.items[0] }}

// Last item
{{ $json.items.at(-1) }}

// Length
{{ $json.items.length }}

// Map
{{ $json.items.map(i => i.name) }}

// Filter
{{ $json.items.filter(i => i.active) }}

// Find
{{ $json.items.find(i => i.id === '123') }}

// Reduce
{{ $json.items.reduce((sum, i) => sum + i.amount, 0) }}
```

### String Operations
```javascript
// Concatenation
{{ $json.first + ' ' + $json.last }}

// Template literal
{{ `Hello ${$json.name}` }}

// Split
{{ $json.tags.split(',') }}

// Join
{{ $json.items.join(', ') }}

// Case conversion
{{ $json.name.toLowerCase() }}
{{ $json.name.toUpperCase() }}

// Trim
{{ $json.input.trim() }}

// Replace
{{ $json.text.replace(/old/g, 'new') }}

// Substring
{{ $json.text.substring(0, 10) }}
```

### Date/Time
```javascript
// Current timestamp
{{ $now.toISO() }}

// Parse date
{{ DateTime.fromISO($json.date) }}

// Format date
{{ DateTime.fromISO($json.date).toFormat('yyyy-MM-dd') }}

// Add days
{{ DateTime.fromISO($json.date).plus({days: 7}).toISO() }}

// Difference
{{ DateTime.fromISO($json.end).diff(DateTime.fromISO($json.start), 'days').days }}
```

### Number Operations
```javascript
// Round
{{ Math.round($json.value) }}

// Floor/Ceil
{{ Math.floor($json.value) }}
{{ Math.ceil($json.value) }}

// Format currency
{{ $json.amount.toFixed(2) }}

// Parse string to number
{{ parseInt($json.stringNum) }}
{{ parseFloat($json.stringFloat) }}
```

---

## Common Transformations

### Flatten Nested Object
```javascript
// Input: { user: { name: 'John', address: { city: 'NYC' } } }
// Output: { userName: 'John', userCity: 'NYC' }

const flatten = (obj, prefix = '') => {
  return Object.entries(obj).reduce((acc, [key, value]) => {
    const newKey = prefix ? `${prefix}${key.charAt(0).toUpperCase()}${key.slice(1)}` : key;
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      return { ...acc, ...flatten(value, newKey) };
    }
    return { ...acc, [newKey]: value };
  }, {});
};

return { json: flatten($json) };
```

### Rename Fields
```javascript
// Rename multiple fields
const fieldMap = {
  'old_name': 'newName',
  'created_at': 'createdAt',
  'user_id': 'userId'
};

const renamed = Object.entries($json).reduce((acc, [key, value]) => {
  const newKey = fieldMap[key] || key;
  return { ...acc, [newKey]: value };
}, {});

return { json: renamed };
```

### Filter and Transform Array
```javascript
// Filter active users and transform
const users = $json.users
  .filter(u => u.status === 'active')
  .map(u => ({
    id: u.id,
    displayName: `${u.firstName} ${u.lastName}`,
    email: u.email.toLowerCase()
  }));

return { json: { users } };
```

### Group By
```javascript
// Group items by category
const grouped = $json.items.reduce((acc, item) => {
  const key = item.category;
  if (!acc[key]) acc[key] = [];
  acc[key].push(item);
  return acc;
}, {});

return { json: grouped };
```

### Deduplicate
```javascript
// Remove duplicates by ID
const seen = new Set();
const unique = $json.items.filter(item => {
  if (seen.has(item.id)) return false;
  seen.add(item.id);
  return true;
});

return { json: { items: unique } };
```

### Merge Objects
```javascript
// Deep merge two objects
const deepMerge = (target, source) => {
  for (const key in source) {
    if (source[key] instanceof Object && key in target) {
      Object.assign(source[key], deepMerge(target[key], source[key]));
    }
  }
  return { ...target, ...source };
};

const merged = deepMerge($json.base, $json.override);
return { json: merged };
```

### Pivot Data
```javascript
// Rows to columns
// Input: [{month: 'Jan', value: 100}, {month: 'Feb', value: 200}]
// Output: {Jan: 100, Feb: 200}

const pivoted = $json.data.reduce((acc, row) => {
  acc[row.month] = row.value;
  return acc;
}, {});

return { json: pivoted };
```

### Unpivot Data
```javascript
// Columns to rows
// Input: {Jan: 100, Feb: 200}
// Output: [{month: 'Jan', value: 100}, {month: 'Feb', value: 200}]

const unpivoted = Object.entries($json).map(([key, value]) => ({
  month: key,
  value: value
}));

return unpivoted.map(item => ({ json: item }));
```

---

## Multi-Item Processing

### Process All Items Together
```javascript
// Use $input.all() to access all items
const items = $input.all();
const total = items.reduce((sum, item) => sum + item.json.amount, 0);

return items.map(item => ({
  json: {
    ...item.json,
    percentOfTotal: (item.json.amount / total * 100).toFixed(2)
  }
}));
```

### Create Multiple Output Items
```javascript
// Split one item into multiple
const items = $json.items;
return items.map(item => ({ json: item }));
```

### Aggregate Multiple Items
```javascript
// Combine all items into one
const items = $input.all();
const aggregated = {
  count: items.length,
  total: items.reduce((sum, i) => sum + i.json.value, 0),
  items: items.map(i => i.json)
};

return [{ json: aggregated }];
```

---

## Node Data Access

### Access Other Nodes
```javascript
// Previous node output
{{ $('Previous Node').item.json.field }}

// All items from node
{{ $('Node Name').all() }}

// First item from node
{{ $('Node Name').first().json.field }}

// Last item from node
{{ $('Node Name').last().json.field }}
```

### Access by Index
```javascript
// Specific item by index
{{ $('Node Name').item(0).json.field }}
```

### Item Matching
```javascript
// Match items between nodes
{{ $('Node1').item.json.id === $('Node2').item.json.id }}
```

---

## Merge Node Strategies

### Append
Combine items from both inputs:
```
Input 1: [A, B]
Input 2: [C, D]
Output: [A, B, C, D]
```

### Combine by Position
Match items by index:
```
Input 1: [A, B]
Input 2: [1, 2]
Output: [A+1, B+2]
```

### Combine by Field
Match items by field value:
```
Input 1: [{id: 1, name: 'A'}]
Input 2: [{id: 1, value: 100}]
Output: [{id: 1, name: 'A', value: 100}]
```

### Multiplex
Create all combinations:
```
Input 1: [A, B]
Input 2: [1, 2]
Output: [A+1, A+2, B+1, B+2]
```

---

## Performance Tips

1. **Use Set Node** for simple mappings (faster than Code)
2. **Batch Process** large arrays in chunks
3. **Avoid N+1** - transform in single pass
4. **Pre-filter** before expensive transformations
5. **Use Item Lists** for built-in array operations

---

## Quick Reference

### JMESPath (Alternative Query Syntax)
```javascript
{{ $jmespath($json, 'users[?active].name') }}
```

### Type Conversion
```javascript
String($json.number)
Number($json.string)
Boolean($json.value)
JSON.parse($json.jsonString)
JSON.stringify($json.object)
```

### Null Handling
```javascript
{{ $json.field ?? 'default' }}      // Nullish coalescing
{{ $json.field?.nested?.value }}    // Optional chaining
```
