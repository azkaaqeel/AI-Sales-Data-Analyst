# BusinessAnalyst Workflow

This document explains the end-to-end workflow of the BusinessAnalyst tool, from data ingestion to insights generation.

## Table of Contents
- [Overview](#overview)
- [Workflow Steps](#workflow-steps)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

BusinessAnalyst is a tool that processes sales data to generate insights through:
1. Smart CSV ingestion and validation
2. Automated KPI detection and calculation
3. Time series trend analysis using Prophet
4. AI-powered insight generation with visualizations

### System Architecture
```
                ┌──────────┐
                │   CSV    │
                │Ingestion │
                └────┬─────┘
                     ▼
                ┌──────────┐
                │  Data    │
                │ Cleaning │
                └────┬─────┘
                     ▼
                ┌──────────┐
                │ Period   │
                │Detection │
                └────┬─────┘
                     ▼
                ┌──────────┐
                │   KPI    │
                │Detection │
                └────┬─────┘
                     ▼
                ┌──────────┐
                │  User    │
                │Confirm   │
                └────┬─────┘
                     ▼
                ┌──────────┐
                │   KPI    │
                │   Calc   │
                └────┬─────┘
                     ▼
                ┌──────────┐
                │  Trend   │
                │Extraction│
                └────┬─────┘
                     ▼
                ┌──────────┐
                │Insights  │
                │Generator │
                └──────────┘
```

## Workflow Steps

### 1. CSV Ingestion (`modules/ingest_csv.py`)
- Validates and loads CSV files
- Detects file encoding automatically
- Performs sales dataset validation
- Features:
  - Smart date format detection
  - Column type inference (date, numeric, categorical)
  - Sales dataset validation (optional)
  - Configurable row limits and validation rules

```python
from modules.ingest_csv import ingest_csv

df, metadata = ingest_csv(
    'sales_data.csv',
    require_sales=True  # Enforce sales dataset validation
)
```

### 2. Data Cleaning
- Automatic handling of:
  - Missing values
  - Date format standardization
  - Column name normalization
  - Type conversion
- Validation rules ensure data quality

### 3. Period Detection (`utils/time_period_detection.py`)
- Automatically detects time granularity:
  - Daily
  - Weekly (WoW comparisons)
  - Monthly (MoM comparisons)
- Groups data accordingly for consistent KPI calculation

### 4. KPI Detection (`modules/KPI_Module/KPI_Detection.py`)
- Reads KPI definitions from YAML files
- Uses fuzzy matching to map columns to KPI placeholders
- Supports:
  - Custom KPIs via `user_data/custom_kpis.yaml`
  - Semantic column matching (optional)
  - Dependencies between KPIs

Example KPI YAML:
```yaml
- name: "Average Order Value"
  columns: ["Total Sales", "Orders"]
  formula: "df['Total Sales'] / df['Orders']"
  description: "Average amount per order"
```

### 5. User Confirmation
- Shows detected column mappings
- Allows manual override of:
  - Column matches
  - Time period selection
  - KPI selection

### 6. KPI Calculation (`modules/KPI_Module/KPI_Calculation.py`)
- Calculates KPIs based on confirmed mappings
- Handles:
  - Period-over-period comparisons
  - KPI dependencies (topological sort)
  - Missing data cases
- Returns structured results with success/error flags

### 7. Trend Extraction (`modules/Trend_Extraction.py`)
- Uses Prophet for trend analysis
- Matches KPI calculation granularity
- Generates:
  - Trend visualizations
  - Component breakdowns (trend/seasonal/residual)
- Handles:
  - Seasonality detection
  - Changepoint detection
  - Future projections (optional)

### 8. Insights Generation (`modules/generate_insights.py`)
- Uses Google Gemini (or other LLMs) to:
  - Interpret trends
  - Explain KPI changes
  - Generate recommendations
- Creates professional PDF reports with:
  - Executive summary
  - KPI analysis
  - Trend visualizations
  - Actionable recommendations

## Configuration

### Environment Variables
```bash
GOOGLE_API_KEY=your_api_key  # Required for insight generation
```

### Key Configuration Files
- `Sales_KPI.YAML`: Default KPI definitions
- `user_data/custom_kpis.yaml`: User-defined KPIs
- `.env`: Environment variables (create from `.env.example`)

### Customization Points
1. KPI Definitions
   - Add custom KPIs in YAML format
   - Support for complex formulas and dependencies

2. Report Styling (`utils/generate_pdf_reports.py`)
   - Customize PDF layout
   - Multiple style presets available

3. Insight Generation
   - Adjustable prompt templates
   - Configurable analysis depth

## Error Handling

The system includes robust error handling for:
- Invalid CSV formats
- Missing required columns
- Data validation failures
- KPI calculation errors
- API failures (LLM calls)

Each step provides detailed error messages and logging.

## Examples

### Basic Usage
```python
from examples.generate_report import generate_sample_report

# Generate a complete report
pdf_path = generate_sample_report(
    data_path='sales_data.csv',
    output_dir='reports'
)
```

### Custom KPI Example
```yaml
# user_data/custom_kpis.yaml
- name: "Customer Lifetime Value"
  columns: ["Total Sales", "Unique Customers"]
  formula: "df['Total Sales'].sum() / df['Unique Customers'].nunique()"
  description: "Average revenue per unique customer"
```

### Time Period Override
```python
from utils.time_period_detection import set_analysis_period

# Force monthly analysis
set_analysis_period('monthly')
```

## Dependencies

Core requirements:
- pandas
- numpy
- prophet
- google-generativeai
- reportlab (PDF generation)
- pyyaml
- rapidfuzz (fuzzy matching)
- sentence-transformers (semantic matching)

## Tips & Best Practices

1. Data Preparation
   - Ensure clean date formats
   - Include at least sales and order columns
   - Prefer consistent column naming

2. Performance
   - Use appropriate time granularity
   - Consider data volume for Prophet analysis
   - Cache LLM results when possible

3. Customization
   - Start with example KPIs
   - Test custom KPIs with sample data
   - Validate formulas before deployment

## Troubleshooting

Common issues and solutions:
1. CSV Ingestion Failures
   - Check file encoding
   - Verify date formats
   - Ensure numeric columns are clean

2. KPI Detection Issues
   - Review column names
   - Check YAML syntax
   - Verify formula correctness

3. Trend Analysis Errors
   - Ensure sufficient data points
   - Check for date continuity
   - Verify numeric data quality

## Future Improvements

Planned enhancements:
- [ ] Support for more data sources
- [ ] Additional ML models for trend analysis
- [ ] Interactive web dashboard
- [ ] Automated anomaly detection
- [ ] Export to more formats

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new KPIs
- Improving algorithms
- Extending report generation
- Adding new features
