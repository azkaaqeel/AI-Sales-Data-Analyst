## Quick orientation — BusinessAnalyst (AI agent)

This repo is a small toolkit for detecting, calculating and explaining KPIs from tabular sales data and generating multimodal insights (trend images + KPIs) via a large language model.

Keep guidance short and focused on discoverable behavior. Use the file references below when you need examples.

### Big picture (components & data flow)
- KPI definition loader: `KPI_Calculator.py::load_kpis_from_yaml` — reads YAML(s) under `user_data/custom_kpis.yaml` (custom) and a general path (`/content/Sales_KPI.YAML` in code). KPI entries contain `name`, `columns` (placeholders), `formula`, `dependencies`, `description`.
- KPI detection & matching: `KPI_Calculator.py::KPI_Detection` — normalizes input dataframe columns, fuzzy-matches placeholders (rapidfuzz) and optionally uses semantic embeddings (SentenceTransformer) to map KPI placeholders to real columns.
- KPI calculation: `KPI_Calculator.py::KPI_Calculation` and `calculate_kpis` — builds dependency order (topological sort), substitutes placeholders in KPI `formula` strings (expects occurrences like `df['Column Placeholder']` or `'Placeholder'`), then evaluates formulas with a safe eval context (exports `df`, `np`, `pd`). Result shape: {kpi_name: {value, success, error}} per period.
- Temporal handling: `calculate_kpis_temporal` detects a date column, buckets by period (WoW or MoM) and computes KPIs per period.
- Trend extraction: `Trend_Extraction.py::detect_trends` — finds sales/time columns, fits Prophet, returns a list of BytesIO PNG images (trend plot and components).
- Insight generation: `generate_insights.py::generate_insights` — expects `trend_imgs: List[BytesIO]` and `kpi_data` (must contain `calculated_kpis`). Uses Google Gemini SDK (`google.generativeai`) and requires `GOOGLE_API_KEY` in env.
- Small utilities: `extract_kpi_summary.py` (prunes calculated_kpis into a compact dict per period), `generate_markdown_summary.py` (simple markdown formatter).

### Project-specific conventions & gotchas (be explicit)
- Column normalization: code expects normalized column names via `normalize_column_name` (Title Case, special chars removed). When matching, placeholders from YAML are used verbatim but normalized before comparison.
- Placeholder semantics: KPI YAML `columns` are placeholders. The code replaces literal occurrences of `df['<placeholder>']` and string occurrences `'<placeholder>'` in the `formula` before eval. Keep placeholders unchanged in YAML; do not pre-normalize them there.
- Dependency formula format: formulas may reference other KPIs as `kpis['<KPI Name>']`. The engine replaces these with computed values when building the formula string before eval.
- Semantics vs fuzzy matching: `match_column` first tries token-based fuzzy matching (rapidfuzz) with a threshold (default ~55). If that fails, it calls a semantic matcher that uses SentenceTransformer embeddings and cosine similarity — expect extra latency and a model dependency.
- Safety note: KPI evaluation uses Python `eval` with a restricted globals dict (`df`, `np`, `pd`, `kpis`). Be careful when suggesting formula changes.

### Integration & external dependencies (observed from imports)
- Required runtime packages (explicit imports): pandas, numpy, pyyaml, rapidfuzz, sentence_transformers, sklearn, prophet, google-generativeai, matplotlib. There is no `requirements.txt`; add or confirm with repository owner before modifying.
- Credentials: `generate_insights` requires `GOOGLE_API_KEY` in environment. No other credential mechanism present.

### Typical dev flow & quick checks
- Local quick smoke (python REPL):
  - Load KPIs: `from KPI_Calculator import export_kpis; kpis = export_kpis()`
  - Run detection: `from KPI_Calculator import KPI_Detection; KPI_Detection(df, kpis)`
  - Calculate selected KPIs: `from KPI_Calculator import KPI_Calculation; KPI_Calculation(df, kpi_status, selected_kpis)`
  - Generate trends: `from Trend_Extraction import detect_trends; imgs = detect_trends(df)`
  - Generate insights (requires env var): `from generate_insights import generate_insights; generate_insights(imgs, {'calculated_kpis': calculated})`

### Helpful examples from code
- Placeholder replacement: `calculate_kpis` expects formulas like `df['Total Sales'] / df['Orders']` or `kpis['Base Sales'] * 0.1`.
- `Trend_Extraction.detect_trends` returns two PNG images in BytesIO suitable for `generate_insights`.

### When editing code, follow these patterns
- Preserve the placeholder and YAML shape: YAML -> placeholders -> normalization -> matched real columns -> formula string substitution.
- Maintain return shapes: `KPI_Detection` returns {'status', 'kpi_status', 'detected_kpis'}; `KPI_Calculation` returns {'status', 'calculated_kpis'}. Other modules rely on these keys.
- Avoid changing the normalized column format unexpectedly (Title Case) — many matchers assume that form.

### What to ask the repo owner if unclear
- Where are canonical KPI YAMLs stored in this project (production path instead of `/content/Sales_KPI.YAML`)?
- Is there a preferred virtual environment or pinned `requirements.txt` to use?
- Should we add tests and a small sample CSV / sample_kpis.yaml for reproducible local dev?

If anything above looks incomplete or you'd like me to include quick run scripts and a `requirements.txt`, tell me and I will add them.
