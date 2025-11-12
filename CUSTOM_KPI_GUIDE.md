# Custom KPI Feature - Implementation Guide

## ✅ What's Been Built

### Backend (`/backend/modules/custom_kpi_calculator.py`)
A **safe** custom KPI calculator that:
- ✅ Shows available numeric columns
- ✅ Validates formulas before execution
- ✅ Handles divide by zero gracefully (returns error, not crash)
- ✅ Handles NaN/Inf values
- ✅ Prevents code injection (no `eval()` attacks)
- ✅ Supports aggregations: `sum()`, `avg()`, `count()`, `min()`, `max()`
- ✅ Provides pre-built templates

### API Endpoints (`/backend/server/integrated_api.py`)

#### 1. GET `/api/custom_kpi/columns/{file_id}`
Returns available columns and formula templates:
```json
{
  "columns": {
    "numeric": ["revenue", "quantity", "price"],
    "all": ["revenue", "quantity", "price", "product_name", "date"]
  },
  "templates": [
    {
      "name": "Average Order Value",
      "formula": "sum(\"revenue\") / count(\"order_id\")",
      "description": "Total revenue divided by number of orders",
      "requires": ["revenue column (numeric)", "order_id column"]
    }
  ]
}
```

#### 2. POST `/api/custom_kpi/calculate/{file_id}`
Calculate a custom KPI:
```
POST /api/custom_kpi/calculate/abc123
Form Data:
  - kpi_name: "Average Order Value"
  - formula: sum("revenue") / count("order_id")

Response:
{
  "success": true,
  "kpi": {
    "name": "Average Order Value",
    "value": 125.50,
    "formula": "sum(\"revenue\") / count(\"order_id\")",
    "description": "Calculates sum using columns: revenue, order_id"
  }
}
```

## 🔧 Formula Syntax

### Basic Operations
```
sum("revenue") / count("order_id")          # Average Order Value
(count("conversions") / count("visitors")) * 100   # Conversion Rate %
sum("revenue") - sum("cost")                # Profit
```

### Supported Aggregations
- `sum("column")` - Total sum
- `avg("column")` or `mean("column")` - Average
- `count("column")` - Count of non-null values
- `min("column")` - Minimum value
- `max("column")` - Maximum value
- `median("column")` - Median value

### Safety Features
✅ **Divide by Zero**: Returns error message instead of crashing
✅ **Invalid Columns**: Validates before execution
✅ **Code Injection**: Blocks dangerous operations (`import`, `exec`, etc.)
✅ **NaN/Inf**: Detects and reports invalid results

## 🎨 UI Integration (Next Steps)

### Option 1: Simple Modal (Recommended for MVP)
Add a "Create Custom KPI" button in the KPI detection view:

```typescript
// After KPI detection completes:
<button onClick={() => setShowCustomKPIModal(true)}>
  + Create Custom KPI
</button>

<CustomKPIModal
  fileId={fileId}
  availableColumns={columns}
  templates={templates}
  onCalculate={(kpi) => {
    // Add to existing KPIs
    setKpis([...kpis, kpi]);
  }}
/>
```

### Option 2: Inline Builder
Show available columns and a formula input box:

```
Available Columns (numeric):
[revenue] [quantity] [price] [cost]

Formula: sum("revenue") / count("order_id")
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         [Insert Column] [Templates ▼]

Preview: Average Order Value = $125.50

[Calculate] [Cancel]
```

### Where to Add It
**Best Place**: After KPI detection, before generating the report
- User uploads CSV
- System detects auto KPIs → Shows 12 KPIs
- **→ User can add custom KPIs here** ← NEW STEP
- User confirms and generates report

## 📋 Pre-Built Templates

1. **Average Order Value** - `sum("revenue") / count("order_id")`
2. **Conversion Rate** - `(count("conversions") / count("visitors")) * 100`
3. **Average Revenue Per Customer** - `sum("revenue") / count("customer_id")`
4. **Profit Margin** - `((sum("revenue") - sum("cost")) / sum("revenue")) * 100`
5. **Average Transaction Size** - `sum("quantity") / count("order_id")`

## 🚀 Quick Test

### Test the Backend
```bash
# 1. Restart backend
python backend/server/integrated_api.py

# 2. Upload a file and get file_id
curl -X POST http://localhost:8000/api/upload -F "file=@sales_data.csv"

# 3. Get available columns
curl http://localhost:8000/api/custom_kpi/columns/{file_id}

# 4. Calculate a custom KPI
curl -X POST http://localhost:8000/api/custom_kpi/calculate/{file_id} \
  -F "kpi_name=Average Order Value" \
  -F "formula=sum(\"revenue\") / count(\"order_id\")"
```

## 💡 Recommendations

### For MVP (Quick Win):
1. ✅ Use **template-based approach**
   - Show 5 pre-built templates
   - User just maps column names
   - Faster, safer, less prone to errors

### For Full Feature:
1. ✅ Free-text formula input
2. ✅ Column picker (click to insert)
3. ✅ Real-time validation (show green ✓ or red ✗)
4. ✅ Preview result before adding

## 🎯 Next Actions

**To finish this feature, you need to:**

1. **Add UI Component** - A modal/dialog for custom KPI creation
2. **Call the APIs** - Fetch columns, validate formula, calculate KPI
3. **Update Workflow** - Add custom KPI step after auto-detection
4. **Testing** - Test with edge cases (divide by zero, missing columns)

**Estimated Time**: 1-2 hours for simple template-based UI

Let me know if you want me to:
- Create the React component
- Use template-based (simpler) or free-form (flexible) approach
- Add this after KPI detection or somewhere else

