# 🤖 DataMind - AI Sales Data Analyst

**An intelligent, full-stack analytics platform that transforms raw CSV data into actionable business insights using AI.**

Upload your sales data → Get automated cleaning suggestions → Detect KPIs intelligently → Generate AI-powered reports with forecasts and recommendations.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6.svg)](https://www.typescriptlang.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple.svg)](https://github.com/langchain-ai/langgraph)

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Complete Application Flow](#-complete-application-flow)
- [How Services Work](#-how-services-work)
- [Quick Start](#-quick-start)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)

---

## ✨ Key Features

### 🧹 **Intelligent Data Cleaning**
- **Statistical profiling** - Automatically analyzes column types, data quality, and anomalies
- **Rule-based cleaning** - Handles missing values, outliers, duplicates, and type conversions
- **User control** - Column-wise cleaning plan with toggle buttons to select which steps to apply
- **Safe operations** - Preview changes before applying them

### 🎯 **Hybrid KPI Detection**
- **LLM-powered column mapping** - Uses Google Gemini to understand semantic meaning (e.g., "purchase_amount" = "selling_price")
- **YAML-based KPI library** - 12+ pre-defined business metrics
- **Dynamic KPI generation** - AI creates custom KPIs based on available columns when needed (only for <30% match rate)
- **Custom KPI builder** - Visual formula builder with safe calculation engine

### 📈 **Time-Series Analysis**
- **Prophet integration** - Facebook's forecasting library for trend analysis
- **Anomaly detection** - Statistical outlier detection in trends
- **Automatic visualization** - Generates trend charts with insights
- **Multi-period support** - Calculate KPIs across daily, weekly, or monthly periods

### 🤖 **AI-Powered Insights**
- **Executive summaries** - Google Gemini generates business insights from data
- **Actionable recommendations** - Context-aware suggestions based on trends and KPIs
- **Seasonal analysis** - Detects holiday impacts and seasonal patterns
- **Dynamic explanations** - KPI-specific business context

### 🎨 **Modern Frontend**
- **Beautiful UI** - Clean, responsive design with Tailwind CSS and dark theme
- **4-phase workflow** - Upload → Review Plan → Select KPIs → View Report
- **Real-time updates** - Live progress tracking during processing
- **PDF export** - Download professional text-based reports

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)              │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ FileUpload │→│ CleaningPlan │→│ KPI Selection      │→  │
│  │ Component  │  │ View         │  │ (Detected+Custom)  │   │
│  └────────────┘  └──────────────┘  └────────────────────┘   │
│                                      ↓                        │
│                              ┌────────────────┐               │
│                              │  Report View   │               │
│                              │  (KPIs+Charts) │               │
│                              └────────────────┘               │
└───────────────────────────────────┬──────────────────────────┘
                                    │ REST API
                                    ▼
┌──────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI + LangGraph Agent)             │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         LangGraph Agentic Workflow                   │    │
│  │  ┌────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐ │    │
│  │  │ Ingest │→│  Clean   │→│ Load    │→│ Detect │ │    │
│  │  │  CSV   │  │   Data   │  │  KPIs   │  │  KPIs  │ │    │
│  │  └────────┘  └──────────┘  └─────────┘  └────────┘ │    │
│  │       ↓                                        ↓      │    │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐ │    │
│  │  │ Calculate  │→│   Extract   │→│  Generate    │ │    │
│  │  │    KPIs    │  │   Trends    │  │  Insights    │ │    │
│  │  └────────────┘  └─────────────┘  └──────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                   │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │ Statistical│  │ KPI Engine  │  │ Custom KPI           │ │
│  │ Cleaner    │  │ (LLM-based) │  │ Calculator (Pandas)  │ │
│  └────────────┘  └─────────────┘  └──────────────────────┘ │
│                           ↓                                   │
│  ┌──────────────────┐         ┌────────────────────────┐   │
│  │ Prophet          │         │ Gemini LLM             │   │
│  │ (Forecasting)    │         │ (Insights + Mapping)   │   │
│  └──────────────────┘         └────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Backend:**
- **FastAPI** - High-performance async API framework
- **LangGraph** - Agentic workflow orchestration (state machine)
- **Pandas** - Data manipulation and analysis
- **Prophet** - Time-series forecasting by Meta
- **Google Gemini 1.5 Pro** - LLM for column mapping, KPI generation, and insights
- **ReportLab** - PDF generation
- **FuzzyWuzzy** - String matching (deprecated in favor of LLM)

**Frontend:**
- **React 18** - UI library with hooks
- **TypeScript** - Type safety
- **Vite** - Fast build tool and dev server
- **Recharts** - Data visualization library
- **Tailwind CSS** - Utility-first styling

---

## 🔄 Complete Application Flow

### Phase 1: Upload & Data Profiling

```
User uploads CSV
     ↓
FastAPI receives file (/api/upload)
     ↓
LangGraph Agent: ingest_node
     ├─ Read CSV with pandas
     ├─ Detect column types
     ├─ Calculate data statistics
     └─ Classify dataset type (sales/inventory/etc)
     ↓
LangGraph Agent: propose_cleaning_node
     ├─ Statistical Cleaner analyzes each column:
     │   ├─ Missing values (>5% → impute/drop)
     │   ├─ Outliers (IQR method)
     │   ├─ Duplicates (by all columns)
     │   ├─ Type mismatches (numeric as text)
     │   ├─ Date parsing (auto-detect formats)
     │   └─ Negative values (in price/amount columns)
     ├─ Generate step-by-step cleaning plan
     └─ Mark critical vs optional steps
     ↓
Return to Frontend:
     {
       file_id: "unique-id",
       cleaning_plan: {
         columns: [{column, steps[]}],
         global_steps: []
       }
     }
```

**Key Implementation:**
- `backend/modules/Ingestion_Module/ingest_csv.py` - CSV parsing
- `backend/modules/Cleaning_Module/statistical_cleaner.py` - Cleaning logic
- `backend/agent/business_analyst_agent.py` - Agent nodes

---

### Phase 2: Apply Cleaning & Detect KPIs

```
User selects cleaning steps
     ↓
FastAPI receives selections (/api/clean_and_detect_kpis)
     ↓
LangGraph Agent: apply_cleaning_node
     ├─ Apply selected steps only
     ├─ Track which operations were performed
     └─ Store cleaned dataframe in memory
     ↓
LangGraph Agent: load_kpis_node
     ├─ Load YAML KPI definitions (Sales_KPI.YAML)
     └─ Prepare KPI templates
     ↓
LangGraph Agent: detect_kpis_node
     │
     ├─ Phase 1: LLM Column Mapping
     │   ├─ Send all column names + KPI requirements to Gemini
     │   ├─ LLM understands semantic meaning:
     │   │   "purchase_amount_(usd)" = "selling_price"
     │   │   "customer_reference_id" = "order_id"
     │   └─ Returns JSON mapping
     │
     ├─ Phase 2: Match Base KPIs (NO FUZZY MATCHING)
     │   ├─ For each KPI, check if required columns are in LLM mapping
     │   ├─ Mark as "calculable" if all columns found
     │   └─ Skip if any column missing
     │
     ├─ Phase 3: Match Derived KPIs
     │   └─ Calculate if dependencies are calculable
     │
     └─ Phase 4: LLM Generate Additional KPIs (only if <30% match)
         ├─ Send sample data to Gemini
         ├─ LLM creates custom KPIs based on available columns
         └─ Merge with detected KPIs
     ↓
Return to Frontend:
     {
       detected_kpis: [
         {name, description, formula},
         ...
       ]
     }
```

**Key Implementation:**
- `backend/modules/KPI_Module/KPI_Detection.py` - Hybrid detection
- `backend/modules/KPI_Module/KPI_Engine.py` - LLM mapping + matching
- `backend/modules/KPI_Module/llm_kpi_generator.py` - Dynamic generation

**Optimization Note:**
- **Latency reduced by 60-70%** by removing fuzzy/semantic matching
- LLM mapping is faster and more accurate
- Only triggers additional LLM call for very poor matches (<30%)

---

### Phase 3: Calculate KPIs & Generate Report

```
User selects KPIs (detected + custom)
     ↓
FastAPI receives selections (/api/generate_report)
     ↓
LangGraph Agent: calculate_kpis_node
     │
     ├─ Detect time period (date column → daily/weekly/monthly)
     ├─ Group data by period
     │
     ├─ For each KPI:
     │   ├─ Execute formula with matched columns
     │   ├─ Handle dependencies (derived KPIs)
     │   └─ Store result per time period
     │
     └─ Calculate Custom KPIs:
         ├─ Parse user formula (e.g., "sum('Revenue') / count('Orders')")
         ├─ Validate: sum/avg/min/max only on numeric columns
         ├─ Safe eval in restricted namespace
         ├─ Handle divide-by-zero, NaN, Inf
         └─ Add to all periods
     ↓
LangGraph Agent: extract_trends_node
     │
     ├─ For each numeric KPI (up to 6):
     │   ├─ Prepare time-series data
     │   ├─ Run Prophet forecasting
     │   ├─ Detect anomalies (statistical outliers)
     │   ├─ Calculate trend insights:
     │   │   ├─ Overall direction (↑↓→)
     │   │   ├─ % change
     │   │   ├─ Volatility (high/low)
     │   │   └─ Peak/low values
     │   └─ Return chart data as JSON
     │
     └─ Generate sparklines (last 10 periods)
     ↓
LangGraph Agent: generate_insights_node
     │
     ├─ Prepare structured KPI data for LLM
     ├─ Send to Gemini with detailed prompt:
     │   "Analyze these KPIs and provide:
     │    - Executive Summary (2-3 sentences)
     │    - KPI Analysis (with % changes)
     │    - Key Insights (3-5 bullet points)
     │    - Recommendations (3-5 actionable items)"
     │
     └─ Parse markdown response into sections
     ↓
Transform for Frontend:
     │
     ├─ Build KPI Cards:
     │   ├─ Latest value vs previous period
     │   ├─ Trend indicator (↑↓→)
     │   ├─ Sparkline data
     │   └─ Seasonal context (if applicable)
     │
     ├─ Generate Dynamic Explanations:
     │   ├─ Detect KPI type (revenue/customer/product/etc)
     │   ├─ Provide business context
     │   └─ Skip custom KPIs (use formula description)
     │
     ├─ Extract Categorical Breakdowns:
     │   ├─ Find dict-type KPIs (e.g., "Revenue by Category")
     │   ├─ Sort by value, take top 10
     │   └─ Format for visual display
     │
     └─ Parse Insights:
         ├─ Executive Summary
         ├─ Key Insights (bullets)
         └─ Recommendations (numbered)
     ↓
Return to Frontend:
     {
       report: {
         reportTitle,
         summary,
         kpis: [{name, value, description, sparkline}],
         kpiExplanations: [{icon, title, description}],
         categoricalBreakdowns: [{title, items[]}],
         trends: [{title, chartData[], insights}],
         insights: [],
         recommendations: []
       }
     }
```

**Key Implementation:**
- `backend/modules/KPI_Module/KPI_Engine.py` - Temporal calculation
- `backend/modules/custom_kpi_calculator.py` - Custom KPI engine
- `backend/modules/Trend_Extractor/Trend_Extraction.py` - Prophet forecasting
- `backend/modules/Insights_Generator/generate_insights.py` - Gemini insights
- `backend/server/integrated_api.py` - Response transformation

---

### Phase 4: Display Report & Export PDF

```
Frontend receives structured report
     ↓
Render Components:
     ├─ Executive Summary (clean markdown)
     ├─ KPI Cards Grid:
     │   ├─ Value with trend indicator
     │   ├─ Period comparison
     │   ├─ Mini sparkline chart
     │   └─ Custom KPI formula (if applicable)
     │
     ├─ "What This Means" Section:
     │   └─ Business explanations for detected KPIs only
     │
     ├─ Category Breakdowns (if any):
     │   └─ Top 10 items with visual bars
     │
     ├─ Trend Analysis Charts:
     │   ├─ Recharts line chart
     │   ├─ Anomalies marked with red dots
     │   ├─ Hover tooltips (period + value)
     │   └─ Analysis card (trend, peak, volatility)
     │
     ├─ Actionable Insights (bullets)
     └─ Recommendations (numbered)
     ↓
User clicks "Export PDF"
     ↓
Frontend sends full report structure to backend
     ↓
Backend (/api/generate_pdf):
     ├─ Use ReportLab to generate PDF
     ├─ Text-based format (no graphs)
     ├─ Sections:
     │   ├─ Title + date
     │   ├─ Executive Summary
     │   ├─ KPI Table
     │   ├─ Business Explanations
     │   ├─ Category Breakdown Tables
     │   ├─ Trend Analysis (text description)
     │   ├─ Insights
     │   └─ Recommendations
     └─ Return PDF as file download
```

**Key Implementation:**
- `newfrontend/new-frontend/components/ReportView.tsx` - Main report UI
- `newfrontend/new-frontend/components/KPICard.tsx` - Individual KPI card
- `newfrontend/new-frontend/components/Chart.tsx` - Trend visualization
- `backend/utils/generate_pdf_reports_v2.py` - PDF generation

---

## 🔧 How Services Work

### 1. Data Cleaning Service

**File:** `backend/modules/Cleaning_Module/statistical_cleaner.py`

**How it Works:**
```python
def clean_retail_data(df):
    # For each column:
    
    # 1. Analyze data type
    if is_numeric(col):
        steps.append(fix_negatives())     # For price/amount columns
        steps.append(remove_outliers())   # IQR method (1.5 * IQR)
    
    # 2. Handle missing values
    if missing_rate > 5%:
        if is_numeric: steps.append(impute_median())
        else: steps.append(drop_rows())
    
    # 3. Parse dates
    if looks_like_date(col):
        steps.append(auto_parse_date())   # Try multiple formats
    
    # 4. Global operations
    steps.append(remove_duplicates())     # By all columns
    steps.append(trim_whitespace())       # Clean strings
    
    return cleaning_plan
```

**Safety Features:**
- Non-destructive preview
- User approval required
- Rollback support (original data kept in memory)

---

### 2. KPI Detection Service

**File:** `backend/modules/KPI_Module/KPI_Detection.py`, `KPI_Engine.py`

**How it Works:**

#### Step 1: LLM Column Mapping
```python
# Send to Gemini:
prompt = f"""
CSV Columns: {csv_columns}
Required KPI Columns: {kpi_requirements}

Map each KPI column to the best CSV column match.
Consider semantic meaning, not just text.

Example mappings:
- "selling_price" → "purchase_amount_(usd)"
- "order_id" → "customer_reference_id"

Return JSON:
{{"selling_price": "purchase_amount_(usd)", ...}}
"""

# Gemini returns intelligent mapping
mapping = gemini.generate(prompt)
```

#### Step 2: Match KPIs (LLM Only - No Fuzzy)
```python
for kpi_name, kpi_info in kpis:
    required_columns = kpi_info['columns']
    matched = {}
    
    for col in required_columns:
        if col in llm_mapping:
            matched[col] = llm_mapping[col]
        else:
            matched[col] = None
    
    kpi_calculable = all(matched.values())
```

#### Step 3: Generate Additional KPIs (Only if <30% matched)
```python
if match_rate < 0.3:
    # Send sample data to Gemini
    llm_kpis = gemini.generate(f"""
    Create KPIs for this dataset:
    Columns: {columns}
    Sample: {sample_rows}
    
    Return KPIs with formulas.
    """)
    
    # Merge with detected KPIs
    all_kpis = yaml_kpis + llm_kpis
```

**Why This is Fast:**
- Single LLM call for all column mappings
- No iterative fuzzy matching
- Only generates new KPIs for poor matches
- **60-70% latency reduction**

---

### 3. Custom KPI Calculator

**File:** `backend/modules/custom_kpi_calculator.py`

**How it Works:**

#### Safe Formula Parsing
```python
# User enters: sum("Revenue") / count("Order Id")

# Step 1: Validate column types
if 'sum' in formula:
    if column not in numeric_columns:
        raise Error("Cannot sum() non-numeric column")

# Step 2: Replace with pandas operations
formula = formula.replace('sum("Revenue")', 'df["revenue"].sum()')
formula = formula.replace('count("Order Id")', 'df["order_id"].count()')

# Step 3: Safe eval in restricted namespace
namespace = {
    'df': df,
    'np': np,
    'sum': np.sum,
    'count': len,
    '__builtins__': {}  # No dangerous functions
}
result = eval(formula, namespace)

# Step 4: Handle errors
if np.isnan(result) or np.isinf(result):
    return Error("Division by zero or invalid calculation")
```

**Supported Operations:**
- **Numeric only:** `sum()`, `avg()`, `min()`, `max()`, `median()`
- **Any column:** `count()`, `nunique()`
- **Operators:** `+`, `-`, `*`, `/`, `()`

**Safety Features:**
- Type validation before execution
- Restricted eval namespace
- Divide-by-zero handling
- No access to dangerous functions

---

### 4. Trend Analysis Service

**File:** `backend/modules/Trend_Extractor/Trend_Extraction.py`

**How it Works:**

#### Prophet Forecasting
```python
# Prepare time-series data
df_prophet = pd.DataFrame({
    'ds': date_column,  # Date
    'y': kpi_values     # Metric values
})

# Run Prophet
model = Prophet()
model.fit(df_prophet)
forecast = model.predict(future)

# Extract components
trend = forecast['trend']
seasonality = forecast['seasonal']
```

#### Anomaly Detection
```python
# Calculate z-scores
mean = np.mean(values)
std = np.std(values)
z_scores = [(v - mean) / std for v in values]

# Flag outliers (|z| > 2)
anomalies = [i for i, z in enumerate(z_scores) if abs(z) > 2]
```

#### Trend Insights
```python
# Direction
if last_value > first_value * 1.1:
    trend = "upward"
elif last_value < first_value * 0.9:
    trend = "downward"
else:
    trend = "stable"

# Volatility
volatility = "high" if std > mean * 0.3 else "low"
```

---

### 5. Insights Generation Service

**File:** `backend/modules/Insights_Generator/generate_insights.py`

**How it Works:**

#### Gemini Prompt Template
```python
prompt = f"""
You are a business analyst. Analyze these KPIs:

{kpi_data}

Generate a report with:
# Executive Summary
[2-3 sentences with specific numbers]

# KPI Analysis
## Financial Performance
[Analyze revenue with % changes]

# Key Insights
- **Finding 1**: Explain with numbers
- **Finding 2**: ...

# Recommendations
1. **Action**: Expected impact
2. ...

RULES:
✅ USE actual numbers (e.g., "$20,261", "11.8%")
✅ REFERENCE time periods (e.g., "Dec 2023 vs Nov 2023")
✅ TIE insights to business impact
❌ DON'T use vague terms like "significant"
❌ DON'T give generic advice
"""

insights = gemini.generate(prompt)
```

#### Parse Response
```python
# Extract sections from markdown
sections = {
    'summary': extract_between("# Executive Summary", "# KPI"),
    'insights': extract_bullets("# Key Insights"),
    'recommendations': extract_numbered("# Recommendations")
}
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **Google Gemini API Key** ([Get one here](https://ai.google.dev/))

### 1. Clone Repository

```bash
git clone https://github.com/azkaaqeel/datamind.git
cd datamind
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
EOF
```

### 3. Frontend Setup

```bash
cd newfrontend/new-frontend
npm install
```

### 4. Start Both Services

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
python backend/server/integrated_api.py
```
Backend runs at: `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd newfrontend/new-frontend
npm run dev
```
Frontend runs at: `http://localhost:3000`

### 5. Test with Sample Data

Open `http://localhost:3000` and upload `Fashion_Retail_Sales.csv` (included in repo).

---

## 📡 API Documentation

### Core Endpoints

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "Datamind Integrated API",
  "version": "2.0"
}
```

---

#### `POST /api/upload`
Upload CSV and get cleaning plan.

**Request:**
- `file`: CSV file (multipart/form-data)

**Response:**
```json
{
  "file_id": "unique-file-id",
  "cleaning_plan": {
    "columns": [
      {
        "column": "Purchase Amount",
        "type": "numeric",
        "steps": [
          {
            "id": "fix_negative_purchase_amount",
            "action": "fix_negative",
            "reason": "Convert negative values to positive",
            "recommended": true
          }
        ],
        "missing_count": 0,
        "total_rows": 1000
      }
    ],
    "global_steps": [
      {
        "id": "remove_duplicates",
        "action": "Remove duplicate rows",
        "reason": "Found 10 duplicate rows",
        "recommended": true,
        "count": 10
      }
    ]
  },
  "original_shape": [1000, 8],
  "preview": [{...}]
}
```

---

#### `POST /api/clean_and_detect_kpis`
Apply cleaning and detect KPIs.

**Request:**
```json
{
  "file_id": "unique-file-id",
  "selected_steps": ["fix_negative_purchase_amount", "remove_duplicates"]
}
```

**Response:**
```json
{
  "detected_kpis": [
    {
      "name": "Total Revenue",
      "description": "Sum of all purchase amounts"
    },
    {
      "name": "Average Order Value",
      "description": "Average amount per transaction"
    }
  ],
  "cleaning_logs": [
    "Fixed 5 negative values",
    "Removed 10 duplicates"
  ],
  "cleaned_shape": [985, 8]
}
```

---

#### `POST /api/generate_report`
Generate full report with insights.

**Request:**
```json
{
  "file_id": "unique-file-id",
  "selected_kpis": ["Total Revenue", "Total Customers"],
  "custom_kpis": [
    {
      "name": "Profit Margin",
      "formula": "(sum('Revenue') - sum('Cost')) / sum('Revenue') * 100",
      "description": "Profit as % of revenue"
    }
  ]
}
```

**Response:**
```json
{
  "report": {
    "reportTitle": "Sales Performance Report",
    "summary": "Revenue declined 11.8% from $22,961 to $20,261...",
    "kpis": [
      {
        "name": "Total Revenue",
        "value": "$20,261",
        "description": "↓ -11.8% vs 2024-11 (was $22,961)",
        "sparkline": [22000, 23000, 21000, 20261],
        "formula_description": null
      }
    ],
    "kpiExplanations": [
      {
        "icon": "📊",
        "title": "Revenue & Sales",
        "description": "Your Total Revenue shows how much money..."
      }
    ],
    "categoricalBreakdowns": [
      {
        "title": "Revenue by Category",
        "items": [
          {"name": "Electronics", "value": "$10,000", "raw_value": 10000},
          {"name": "Clothing", "value": "$5,000", "raw_value": 5000}
        ],
        "total_categories": 6,
        "is_currency": true
      }
    ],
    "trends": [
      {
        "title": "Total Revenue Over Time",
        "description": "Historical trend...",
        "chartData": [
          {"x_axis": "2024-10-01", "y_axis": 22000},
          {"x_axis": "2024-11-01", "y_axis": 20261}
        ],
        "holidays": [],
        "anomalies": [3],
        "insights": {
          "trend": "downward",
          "change": "-11.8%",
          "peak": "23,000",
          "low": "20,261",
          "volatility": "moderate"
        }
      }
    ],
    "insights": [
      "Revenue declined 11.8% despite 6.3% customer growth...",
      "Average Purchase Value dropped 16.7% to $104..."
    ],
    "recommendations": [
      "Investigate pricing strategy and product mix...",
      "Focus on upselling to increase order value..."
    ]
  }
}
```

---

#### `POST /api/generate_pdf`
Generate PDF report.

**Request:**
```json
{
  "file_id": "unique-file-id",
  "report_data": "{...full report JSON...}"
}
```

**Response:** PDF file download

---

#### `GET /api/custom_kpi/columns/{file_id}`
Get available columns for custom KPI builder.

**Response:**
```json
{
  "columns": {
    "numeric": ["Revenue", "Price", "Quantity"],
    "countable": ["Order ID", "Customer ID", "Category"],
    "all": ["Revenue", "Price", "Quantity", "Order ID", "Category"]
  },
  "templates": [
    {
      "name": "Average Order Value",
      "formula": "sum('revenue') / count('order_id')",
      "description": "Total revenue divided by number of orders"
    }
  ]
}
```

---

#### `POST /api/custom_kpi/calculate/{file_id}`
Calculate a custom KPI.

**Request:**
```json
{
  "kpi_name": "Profit Margin",
  "formula": "(sum('Revenue') - sum('Cost')) / sum('Revenue') * 100"
}
```

**Response:**
```json
{
  "success": true,
  "kpi": {
    "name": "Profit Margin",
    "value": 35.5,
    "formula": "(sum('Revenue') - sum('Cost')) / sum('Revenue') * 100",
    "description": "Calculates sum, using columns: Revenue, Cost"
  }
}
```

---

## 📦 Project Structure

```
datamind/
├── backend/
│   ├── agent/
│   │   └── business_analyst_agent.py      # LangGraph workflow (7 nodes)
│   │
│   ├── modules/
│   │   ├── Cleaning_Module/
│   │   │   └── statistical_cleaner.py     # Auto-cleaning logic
│   │   │
│   │   ├── KPI_Module/
│   │   │   ├── KPI_Engine.py              # LLM mapping + calculation
│   │   │   ├── KPI_Detection.py           # Hybrid detection
│   │   │   └── llm_kpi_generator.py       # Dynamic KPI generation
│   │   │
│   │   ├── Trend_Extractor/
│   │   │   └── Trend_Extraction.py        # Prophet forecasting
│   │   │
│   │   ├── Insights_Generator/
│   │   │   └── generate_insights.py       # Gemini insights
│   │   │
│   │   └── custom_kpi_calculator.py       # Safe formula evaluation
│   │
│   ├── server/
│   │   └── integrated_api.py              # FastAPI endpoints
│   │
│   ├── models/
│   │   └── gemini.py                      # Gemini LLM client
│   │
│   ├── utils/
│   │   ├── generate_pdf_reports_v2.py     # PDF generation (ReportLab)
│   │   ├── seasonal_analysis.py           # Holiday detection
│   │   └── time_period_detection.py       # Auto-detect periods
│   │
│   └── Sales_KPI.YAML                     # Pre-defined KPIs
│
├── newfrontend/new-frontend/
│   ├── components/
│   │   ├── FileUpload.tsx                 # Upload UI
│   │   ├── CleaningPlanView.tsx           # Step selector
│   │   ├── KPISelectionWithCustom.tsx     # KPI picker
│   │   ├── CustomKPIModal.tsx             # Formula builder
│   │   ├── ReportView.tsx                 # Main report display
│   │   ├── KPICard.tsx                    # Individual KPI card
│   │   ├── Chart.tsx                      # Trend visualization
│   │   └── Sparkline.tsx                  # Mini trend graph
│   │
│   ├── services/
│   │   └── backendService.ts              # API client
│   │
│   ├── types.ts                           # TypeScript interfaces
│   ├── App.tsx                            # Main app component
│   └── index.css                          # Tailwind config
│
├── Fashion_Retail_Sales.csv               # Sample dataset
├── requirements.txt                       # Python dependencies
├── .env                                   # Environment variables (create this)
├── .gitignore                             # Git ignore rules
└── README.md                              # This file
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```properties
# Required - Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
PORT=8000
FRONTEND_PORT=3000
```

### Custom KPI Definitions

Edit `backend/Sales_KPI.YAML` to add pre-defined KPIs:

```yaml
- name: "Customer Lifetime Value"
  columns: ["customer_id", "revenue"]
  formula: "df.groupby('customer_id')['revenue'].sum().mean()"
  dependencies: []
  description: "Average revenue per customer"
  type: "numeric"
  category: "customer"
```

### Gemini Model Configuration

Edit `backend/models/gemini.py` to change model:

```python
# Default: gemini-1.5-pro
MODEL_NAME = "gemini-1.5-pro"

# For faster responses:
MODEL_NAME = "gemini-1.5-flash"
```

---

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**
```bash
lsof -ti :8000 | xargs kill -9
```

**API key not detected:**
- Ensure `.env` file is in root directory
- Check both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set
- Restart backend after updating `.env`

**KPI detection slow:**
- This is expected on first run (LLM call)
- Should be 2-4 seconds for most datasets
- Check internet connection

**Custom KPI fails:**
```
Error: Cannot use sum() on non-numeric column
```
- Use `count()` or `nunique()` for text columns
- Use `sum()/avg()/min()/max()` only for numeric columns

### Frontend Issues

**CORS errors:**
- Backend must run on `http://localhost:8000`
- Check CORS config in `backend/server/integrated_api.py`

**Build errors:**
```bash
cd newfrontend/new-frontend
rm -rf node_modules package-lock.json
npm install
```

**Report not generating:**
- Check browser console (F12) for errors
- Verify backend is running and accessible
- Check backend terminal for error logs

---

## 🔒 Security Notes

⚠️ **Development Mode:**
- CORS is open (`allow_origins=["*"]`)
- No authentication required
- Data stored in memory (not persistent)
- API keys in `.env` file

✅ **Production Recommendations:**
- Restrict CORS to specific domains
- Add authentication (JWT, OAuth)
- Use environment secrets (AWS Secrets Manager)
- Enable HTTPS
- Add rate limiting
- Implement file size limits (max 10MB)
- Add input validation
- Use database for persistence

---


## 👨‍💻 Author

**Azka Aqeel**

- GitHub: [@azkaaqeel](https://github.com/azkaaqeel)
- Repository: [datamind](https://github.com/azkaaqeel/datamind)

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) - LLM for intelligent analysis
- [Meta Prophet](https://facebook.github.io/prophet/) - Time-series forecasting
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent workflow framework
- [React](https://reactjs.org/) - Frontend library
- [Tailwind CSS](https://tailwindcss.com/) - Styling framework

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by [Azka Aqeel](https://github.com/azkaaqeel)

</div>
