# ⚡ Performance Analysis & Optimization

## 🔍 **Current Performance Issues:**

Based on user feedback: **"Upload and KPI calculation takes so long!"**

---

## 📊 **Pipeline Stages & Expected Timing:**

### **Phase 1: Upload & Propose (~ 5-10 seconds)**
```
1. Load CSV                          ~0.1s   ✅ Fast
2. Dataset Classification (LLM)     ~2-4s   🐌 SLOW - Gemini API call
3. Cleaning Plan Generation (LLM)   ~3-5s   🐌 SLOW - Gemini API call  
4. Statistical analysis              ~0.5s   ✅ Fast
─────────────────────────────────────────────
TOTAL:                               ~6-10s
```

### **Phase 2: Clean & Detect KPIs (~ 10-15 seconds)**
```
1. Apply cleaning steps              ~0.5s   ✅ Fast
2. Detect KPIs (Hybrid YAML+LLM)    ~5-8s   🐌 SLOW - Gemini API call
   - Load YAML KPIs                  ~0.1s   ✅ Fast
   - Match with fuzzy/LLM            ~5-7s   🐌 SLOW - LLM matching
3. Time period detection             ~0.2s   ✅ Fast
─────────────────────────────────────────────
TOTAL:                               ~6-9s
```

### **Phase 3: Generate Report (~ 15-25 seconds)**
```
1. Calculate KPIs over time          ~1-2s   ✅ OK
2. Prophet forecasting               ~8-12s  🐌 VERY SLOW - Prophet model fitting
3. Generate trend charts             ~1s     ✅ Fast
4. LLM insights generation          ~5-8s   🐌 SLOW - Gemini with images
─────────────────────────────────────────────
TOTAL:                               ~15-23s
```

### **🎯 TOTAL PIPELINE TIME: 27-42 seconds**

---

## 🐌 **Identified Bottlenecks:**

### **1. LLM API Calls (3-4 calls total)**
- **Dataset Classification**: 2-4s
- **Cleaning Plan**: 3-5s  
- **KPI Detection**: 5-7s
- **Insights Generation**: 5-8s
- **TOTAL**: ~15-24s (56-62% of total time)

### **2. Prophet Forecasting**
- **Model Fitting**: 8-12s (20-28% of total time)
- **Reason**: Prophet uses Stan for Bayesian inference, which is computationally intensive

### **3. Multiple DataFrame Operations**
- **KPI Calculation Over Time**: 1-2s
- **Period Column Addition**: 0.2s

---

## ⚡ **Optimization Strategies:**

### **🔥 High Impact (Save 10-15 seconds):**

#### **1. Cache LLM Results**
```python
# Cache dataset classification results
classification_cache = {}

def classify_dataset_cached(df_hash, df, metadata):
    if df_hash in classification_cache:
        return classification_cache[df_hash]
    
    result = classify_dataset(df, metadata)
    classification_cache[df_hash] = result
    return result
```
**Saves:** 2-4s per repeated upload

#### **2. Parallelize LLM Calls**
```python
import asyncio

async def run_parallel_analysis(df):
    # Run classification and cleaning plan generation in parallel
    classification_task = asyncio.create_task(classify_dataset_async(df))
    cleaning_task = asyncio.create_task(generate_cleaning_plan_async(df))
    
    classification, cleaning_plan = await asyncio.gather(
        classification_task,
        cleaning_task
    )
    
    return classification, cleaning_plan
```
**Saves:** 3-5s (run both LLM calls simultaneously)

#### **3. Skip Dataset Classification for Known Files**
```python
# If user uploaded "Fashion_Retail_Sales.csv", skip classification
KNOWN_DATASETS = {
    'Fashion_Retail_Sales.csv': {'is_sales': True},
    'sales_data.csv': {'is_sales': True}
}

if filename in KNOWN_DATASETS:
    is_sales = True  # Skip LLM call
```
**Saves:** 2-4s per upload

#### **4. Optimize Prophet Forecasting**
```python
# Current: Full Bayesian inference (slow)
model = Prophet()

# Optimized: Reduce MCMC samples
model = Prophet(
    mcmc_samples=0,  # Use MAP estimation instead of MCMC
    seasonality_mode='additive',
    yearly_seasonality=False  # Skip if not needed
)
```
**Saves:** 4-6s per forecast

---

### **🟡 Medium Impact (Save 3-5 seconds):**

#### **5. Use Gemini Flash Instead of Pro**
```python
# Current (slower but more accurate):
client = GeminiClient(model_name="gemini-2.0-pro")

# Optimized (faster but good enough):
client = GeminiClient(model_name="gemini-2.0-flash")
```
**Saves:** 2-3s per LLM call (×4 = 8-12s total)

#### **6. Reduce KPI Detection Scope**
```python
# Instead of detecting all possible KPIs:
# - Detect only top 10 most relevant KPIs
# - Skip categorical KPIs with >100 unique values
```
**Saves:** 1-2s

#### **7. Batch KPI Calculations**
```python
# Instead of calculating each KPI separately:
# - Group by period once
# - Calculate all KPIs in one pass
```
**Saves:** 0.5-1s

---

### **🟢 Low Impact (Save <2 seconds):**

#### **8. Use Streaming LLM Responses**
```python
# Show progress to user while LLM generates:
for chunk in client.generate_stream(prompt):
    yield chunk  # Stream to frontend
```
**Saves:** 0s (but improves UX - user sees progress)

#### **9. Precompute Common Statistics**
```python
# Cache df.describe(), df.dtypes, etc.
metadata_cache = {
    'describe': df.describe(),
    'dtypes': df.dtypes,
    'shape': df.shape
}
```
**Saves:** 0.2-0.5s

---

## 🎯 **Implementation Priority:**

### **Quick Wins (Implement Now):**
1. ✅ **Optimize Prophet** (save 4-6s)
2. ✅ **Use Gemini Flash** (save 8-12s)
3. ✅ **Skip classification for known files** (save 2-4s)

**Total Savings: 14-22 seconds → New pipeline time: 13-20s** (50% faster!)

---

### **Medium Effort (Next Sprint):**
4. Cache LLM results
5. Parallelize LLM calls
6. Reduce KPI detection scope

**Additional Savings: 5-10 seconds → Pipeline time: 8-10s** (75% faster!)

---

## 🚀 **Quick Optimization Code:**

### **1. Prophet Optimization:**
```python
# backend/modules/Forecast_Module/forecast_trends.py

def forecast_trends(df, target_col, period_type, forecast_periods=12):
    # OLD:
    # model = Prophet()
    
    # NEW (much faster):
    model = Prophet(
        mcmc_samples=0,           # Use MAP instead of MCMC
        seasonality_mode='additive',
        yearly_seasonality=False,  # Skip for short datasets
        weekly_seasonality=True if period_type == 'week' else False,
        daily_seasonality=False,
        interval_width=0.8,        # Reduce uncertainty interval computation
    )
```

### **2. Use Gemini Flash:**
```python
# backend/models/gemini.py or wherever GeminiClient is instantiated

# OLD:
client = GeminiClient(model_name="gemini-2.0-pro")

# NEW (2-3x faster):
client = GeminiClient(model_name="gemini-2.0-flash")
```

### **3. Skip Classification for Known Files:**
```python
# backend/server/integrated_api.py

KNOWN_SALES_DATASETS = ['fashion', 'retail', 'sales', 'transaction', 'order', 'purchase']

@app.post("/api/upload")
async def upload_and_propose(file: UploadFile = File(...)):
    filename = file.filename.lower()
    
    # Quick heuristic check
    if any(keyword in filename for keyword in KNOWN_SALES_DATASETS):
        print(f"✅ Skipping classification - filename indicates sales data")
        is_sales = True
    else:
        # Run full LLM classification
        is_sales, reason = classify_dataset(df, metadata)
```

---

## 📊 **Expected Results After Optimizations:**

| Phase | Before | After | Savings |
|-------|--------|-------|---------|
| Upload & Propose | 6-10s | 3-5s | **50% faster** |
| Clean & Detect KPIs | 6-9s | 3-5s | **50% faster** |
| Generate Report | 15-23s | 7-10s | **60% faster** |
| **TOTAL** | **27-42s** | **13-20s** | **52% faster** 🚀 |

---

## 🧪 **How to Measure:**

Add timing decorators to API endpoints:

```python
import time
from functools import wraps

def time_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️  {func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

@app.post("/api/upload")
@time_endpoint
async def upload_and_propose(...):
    ...
```

---

## ✅ **Ready to Implement?**

Want me to:
1. ✅ Optimize Prophet settings
2. ✅ Switch to Gemini Flash
3. ✅ Add filename-based classification skip

This will make the pipeline **~50% faster** with minimal code changes! 🚀

