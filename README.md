# 🤖 AI Sales Data Analyst

**An intelligent, full-stack analytics platform that transforms raw CSV data into actionable business insights using AI.**

Upload your sales data → Get automated cleaning suggestions → Detect KPIs intelligently → Generate AI-powered reports with forecasts and recommendations.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![Demo](https://via.placeholder.com/800x400?text=AI+Sales+Data+Analyst+Demo)

---

## ✨ Key Features

### 🧹 **Intelligent Data Cleaning**
- **Statistical profiling** - Automatically analyzes column types, data quality, and anomalies
- **Rule-based cleaning** - Handles missing values, outliers, duplicates, and type conversions
- **User control** - Column-wise cleaning plan with toggle buttons to select which steps to apply

### 🎯 **Hybrid KPI Detection**
- **LLM-powered column mapping** - Uses Google Gemini to understand semantic meaning (e.g., "purchase_amount" = "selling_price")
- **YAML-based KPI library** - 12+ pre-defined business metrics with fuzzy matching
- **Dynamic KPI generation** - AI creates custom KPIs based on available columns when needed
- **Custom KPI support** - Users can add their own metrics with pandas formulas

### 📈 **Time-Series Forecasting**
- **Prophet integration** - Facebook's forecasting library for trend analysis
- **Automatic visualization** - Generates trend charts with seasonal decomposition
- **Multi-period analysis** - Calculate KPIs across daily, weekly, or monthly periods

### 🤖 **AI-Powered Insights**
- **Executive summaries** - Google Gemini generates business insights from data
- **Actionable recommendations** - Context-aware suggestions based on trends and KPIs
- **Interactive chat** - Ask questions about your report using AI assistant

### 🎨 **Modern Frontend**
- **Beautiful UI** - Clean, responsive design with Tailwind CSS
- **4-phase workflow** - Upload → Review Plan → Select KPIs → View Report
- **Real-time updates** - Live progress tracking during processing
- **PDF export** - Download reports for sharing

---

## 🏗️ Architecture

```
┌─────────────────┐
│   React + Vite  │  Modern TypeScript frontend
│   Frontend      │  
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   FastAPI       │  Python backend with AI modules
│   Backend       │  
└────────┬────────┘
         │
    ┌────┴─────┬─────────┬──────────┐
    ▼          ▼         ▼          ▼
┌────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
│Cleaning│ │  KPI   │ │ Trends  │ │ Insights │
│Module  │ │ Engine │ │Prophet  │ │ Gemini   │
└────────┘ └────────┘ └─────────┘ └──────────┘
```

### Tech Stack

**Backend:**
- **FastAPI** - High-performance async API framework
- **LangGraph** - Agentic workflow orchestration
- **Pandas** - Data manipulation and analysis
- **Prophet** - Time-series forecasting
- **Google Gemini** - LLM for column mapping, KPI generation, and insights
- **Sentence Transformers** - Semantic similarity matching

**Frontend:**
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Gemini API Key ([Get one here](https://ai.google.dev/))

### 1. Clone Repository

```bash
git clone https://github.com/azkaaqeel/AI-Sales-Data-Analyst.git
cd AI-Sales-Data-Analyst
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env
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

### 5. Open Browser

Navigate to `http://localhost:3000` and upload your CSV file!

---

## 📖 User Guide

### Phase 1: Upload & Data Profiling

1. **Upload CSV** - Drag & drop or click to upload your sales data
2. **Review Plan** - System analyzes your data and proposes cleaning steps:
   - Missing value handling
   - Duplicate removal
   - Outlier detection
   - Type conversions
   - Date parsing

### Phase 2: Select Cleaning Steps

- **Column-wise view** - See cleaning suggestions organized by column
- **Toggle controls** - Check/uncheck steps you want to apply
- **Smart recommendations** - System highlights critical cleaning actions

### Phase 3: KPI Detection & Selection

- **Auto-detected KPIs** - System finds relevant metrics using:
  - LLM column mapping (understands semantic meaning)
  - Fuzzy matching (handles typos and variations)
  - Dynamic generation (creates custom KPIs for your data)
- **Add custom KPIs** - Define your own metrics with pandas formulas
- **Select KPIs** - Choose which metrics to calculate

### Phase 4: Report Generation

- **KPI Dashboard** - View all calculated metrics
- **Trend Analysis** - Interactive charts with forecasts
- **AI Insights** - Executive summary with recommendations
- **Chat Assistant** - Ask questions about your data
- **Export PDF** - Download report for sharing

---

## 📊 Example Use Cases

### Retail Sales Analysis
```csv
order_id,date,product,quantity,price,customer_id
1001,2024-01-15,Laptop,1,899.99,C001
1002,2024-01-16,Mouse,2,25.50,C002
```

**Auto-detected KPIs:**
- Total Revenue
- Average Order Value
- Unique Customers
- Revenue by Product
- Sales Trend

### Fashion Retail
```csv
customer_reference_id,item_purchased,purchase_amount_(usd),date_purchase,review_rating
REF001,Shirt,49.99,2024-01-10,4.5
REF002,Jeans,89.99,2024-01-11,5.0
```

**Auto-detected KPIs:**
- Total Orders
- Average Selling Price
- Customer Satisfaction Score
- Revenue by Product Category
- High-Value Transactions

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```properties
# Required
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
PORT=8000
FRONTEND_PORT=3000
```

### Custom KPI Definitions

Edit `backend/Sales_KPI.YAML` to add your own KPI templates:

```yaml
- name: "Customer Lifetime Value"
  columns: ["customer_id", "revenue", "date"]
  formula: "df.groupby('customer_id')['revenue'].sum().mean()"
  dependencies: []
  description: "Average revenue per customer"
  type: "numeric"
```

---

## 📡 API Documentation

### Backend Endpoints

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

#### `POST /api/upload`
Upload CSV and get cleaning plan.

**Request:**
- `file`: CSV file (multipart/form-data)

**Response:**
```json
{
  "file_id": "unique-id",
  "cleaning_plan": {
    "columns": [
      {
        "column": "Purchase Amount",
        "steps": [
          {
            "id": "step-id",
            "action": "fix_negative",
            "description": "Convert negative values to positive",
            "recommended": true
          }
        ]
      }
    ],
    "global_steps": [
      {"id": "remove_duplicates", "action": "Remove duplicates", "count": 10}
    ]
  },
  "original_shape": [1000, 8],
  "data_preview": [{...}]
}
```

#### `POST /api/clean_and_detect_kpis`
Apply cleaning and detect KPIs.

**Request:**
```json
{
  "file_id": "unique-id",
  "selected_steps": ["step-id-1", "step-id-2"]
}
```

**Response:**
```json
{
  "detected_kpis": [
    {
      "name": "Total Revenue",
      "description": "Sum of all sales",
      "formula": "df['revenue'].sum()",
      "type": "numeric"
    }
  ],
  "cleaning_summary": "Applied 5 cleaning steps"
}
```

#### `POST /api/generate_report`
Generate full report with insights.

**Request:**
```json
{
  "file_id": "unique-id",
  "selected_kpis": ["Total Revenue", "Average Order Value"],
  "custom_kpis": [
    {
      "name": "Custom Metric",
      "formula": "df['column'].mean()"
    }
  ]
}
```

**Response:**
```json
{
  "report": {
    "reportTitle": "Sales Analysis Report",
    "summary": "Executive summary...",
    "kpis": [...],
    "trends": [...],
    "insights": [...],
    "recommendations": [...]
  }
}
```

---

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd newfrontend/new-frontend
npm test
```

### Test with Sample Data

A sample CSV (`Fashion_Retail_Sales.csv`) is included for testing:

```bash
# Upload sample data
curl -X POST http://localhost:8000/api/upload \
  -F "file=@Fashion_Retail_Sales.csv"
```

---

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**
```bash
lsof -i :8000
kill -9 $(lsof -t -i :8000)
```

**API key not detected:**
- Ensure `.env` file is in the root directory
- Check that both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set
- Restart backend after updating `.env`

**KPI detection returns 0:**
- Verify CSV has proper column headers
- Check that data types are recognized (dates, numbers)
- LLM will auto-generate KPIs if matching fails

### Frontend Issues

**CORS errors:**
- Backend must be running on `http://localhost:8000`
- Check CORS configuration in `backend/server/integrated_api.py`

**Build errors:**
```bash
cd newfrontend/new-frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 🔒 Security Notes

⚠️ **Development Mode:**
- CORS is open (`allow_origins=["*"]`)
- No authentication required
- API keys in `.env` file

✅ **Production Recommendations:**
- Restrict CORS to specific domains
- Add authentication (JWT, OAuth)
- Use environment secrets (AWS Secrets Manager, etc.)
- Enable HTTPS
- Add rate limiting
- Implement file size limits

---

## 📦 Project Structure

```
AI-Sales-Data-Analyst/
├── backend/
│   ├── agent/
│   │   └── business_analyst_agent.py    # LangGraph workflow
│   ├── modules/
│   │   ├── Cleaning_Module/
│   │   │   └── statistical_cleaner.py   # Auto-cleaning logic
│   │   ├── KPI_Module/
│   │   │   ├── KPI_Engine.py            # KPI matching & calculation
│   │   │   ├── KPI_Detection.py         # Hybrid detection
│   │   │   └── llm_kpi_generator.py     # AI KPI generation
│   │   ├── Trend_Extractor/
│   │   │   └── Trend_Extraction.py      # Prophet forecasting
│   │   └── Insights_Generator/
│   │       └── generate_insights.py     # Gemini insights
│   ├── server/
│   │   └── integrated_api.py            # FastAPI endpoints
│   ├── Sales_KPI.YAML                   # KPI definitions
│   └── utils/                           # Helper functions
├── newfrontend/
│   └── new-frontend/
│       ├── components/
│       │   ├── FileUpload.tsx           # Upload UI
│       │   ├── CleaningPlanView.tsx     # Cleaning step selector
│       │   ├── KPISelectionWithCustom.tsx # KPI selector
│       │   └── ReportView.tsx           # Report display
│       ├── services/
│       │   └── backendService.ts        # API client
│       ├── types.ts                     # TypeScript interfaces
│       └── App.tsx                      # Main app component
├── Fashion_Retail_Sales.csv             # Sample data
├── requirements.txt                     # Python dependencies
├── .env                                 # Environment variables (create this)
├── .gitignore                           # Git ignore rules
└── README.md                            # This file
```

---

## 🚧 Roadmap

- [ ] Multi-file upload support
- [ ] Database integration (PostgreSQL, MongoDB)
- [ ] Real-time data streaming
- [ ] Advanced visualizations (D3.js)
- [ ] User authentication & workspaces
- [ ] Scheduled reports
- [ ] Email notifications
- [ ] Mobile app
- [ ] Cloud deployment templates (AWS, Azure, GCP)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Azka Aqeel**

- GitHub: [@azkaaqeel](https://github.com/azkaaqeel)
- Repository: [AI-Sales-Data-Analyst](https://github.com/azkaaqeel/AI-Sales-Data-Analyst)

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) - LLM for intelligent analysis
- [Meta Prophet](https://facebook.github.io/prophet/) - Time-series forecasting
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - Frontend library
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent workflow framework

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](https://github.com/azkaaqeel/AI-Sales-Data-Analyst/issues)
3. Create a [new issue](https://github.com/azkaaqeel/AI-Sales-Data-Analyst/issues/new)

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by [Azka Aqeel](https://github.com/azkaaqeel)

</div>
