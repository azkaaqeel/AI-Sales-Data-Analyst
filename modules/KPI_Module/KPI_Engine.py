import pandas as pd
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from collections import defaultdict, deque
import re
from rapidfuzz import process, fuzz
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import util
from utils.time_period_detection import determine_period_type, add_period_column


def load_kpis_from_yaml(path: Path, source: str = "general") -> dict:
    """
    Helper to load KPI definitions from YAML file(s) or directory.
    Returns a dictionary where keys are KPI names and values are metadata.
    """
    kpi_data = {}

    # If directory -> load all YAMLs, if single file -> wrap in list
    yaml_files = list(path.glob("*.yaml")) if path.is_dir() else [path]

    for file in yaml_files:
        if not file.exists() or file.suffix.lower() != ".yaml":
            continue

        with open(file, "r") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"⚠️ Error parsing {file}: {e}")
                continue

        if not data:
            # Skip empty or invalid YAMLs
            continue

        # Handle both dictionary and list formats
        if isinstance(data, dict):
            items = data.items()
        elif isinstance(data, list):
            # Assume list of dictionaries where each dict represents a KPI
            items = enumerate(data)  # Use enumerate to iterate through list
        else:
            continue  # Skip unexpected data types

        for key, value in items:  # Use key, value to handle both dict and list
            if isinstance(value, list):  # Check if value is a list (for dictionary format)
                category = key
                kpi_list = value
            elif isinstance(value, dict):  # Check if value is a dictionary (for list format)
                category = value.get("category", "Unknown")  # Extract category from dict
                kpi_list = [value]  # Wrap the dictionary in a list to process as a single KPI
            else:
                continue

            for kpi in kpi_list:
                name = kpi.get("name")
                if not name:
                    continue

                kpi_data[name] = {
                    "category": category,
                    "formula": kpi.get("formula"),
                    "columns": kpi.get("columns", []),
                    "type": kpi.get("type", "numeric"),
                    "description": kpi.get("description", ""),
                    "dependencies": kpi.get("dependencies", []),
                    "source": source,
                }

    return kpi_data


def export_general_kpis():
    """Loads general KPI definitions from knowledge_base/."""
    return load_kpis_from_yaml(Path("/content/Sales_KPI.YAML"), source="general")


def export_custom_kpis():
    """Loads user-defined KPIs from user_data/custom_kpis.yaml."""
    user_path = Path("user_data/custom_kpis.yaml")
    if not user_path.exists():
        return {}  # ✅ Safe exit if file not found
    return load_kpis_from_yaml(user_path, source="custom")


"""{**dict1, **dict2} unpacks the key-value pairs of both dictionaries.

If both have the same key (like "Profit Margin"), the second one (custom_kpis) wins — it overrides the first.The result is a new dictionary, leaving the originals untouched.
"""


def export_kpis():
    """
    Combines general and custom KPI definitions into one dictionary.
    Custom KPIs override general ones with the same name.
    """
    general_kpis = export_general_kpis()
    custom_kpis = export_custom_kpis()

    combined_kpis = {**general_kpis, **custom_kpis}
    return combined_kpis


def has_minimum_time_coverage(df: pd.DataFrame, date_col: str, period: str = "month", min_periods: int = 2) -> bool:
    """
    Check if the dataset has at least `min_periods` unique months or weeks in the given date column.
    period: 'month' or 'week'
    """
    if date_col not in df.columns:
        return False

    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        if period == "month":
            unique_periods = df[date_col].dt.to_period("M").nunique()
        elif period == "week":
            unique_periods = df[date_col].dt.to_period("W").nunique()
        else:
            raise ValueError("period must be 'month' or 'week'")

        return unique_periods >= min_periods
    except Exception:
        return False


def normalize_column_name(col):
    # 1. Replace underscores and hyphens with spaces
    col = col.replace('_', ' ').replace('-', ' ')
    # 2. Remove all special characters (keep letters, numbers, and spaces)
    col = re.sub(r'[^a-zA-Z0-9\s]', '', col)
    # 3. Split camel case (e.g., TotalSales → Total Sales)
    if ' ' not in col:  # Only split if no spaces exist
        col = re.sub(r'(?<!^)(?=[A-Z])', ' ', col)

    # 4. Convert to title case for consistent matching
    col = col.title()
    # 5. Collapse multiple spaces into one and strip edges
    col = re.sub(r'\s+', ' ', col).strip()

    return col

# Lazy-loaded embedding model to avoid heavy I/O at import time
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _embedding_model


def embed_text(text):
    if text is None:
        return None
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_tensor=True)
    return embedding


def calculate_semantic_similarity(kpi_col, available_columns, threshold=0.8):
    kpi_embedding = embed_text(kpi_col)
    if kpi_embedding is None:
        return None, 0

    kpi_embedding = kpi_embedding.reshape(1, -1)  # reshape into 2D arrays so sklearn’s cosine_similarity accepts them
    available_embeddings = [embed_text(col) for col in available_columns]

    max_similarity = -1
    best_match = None

    for col, col_emb in zip(available_columns, available_embeddings):
        if col_emb is not None:
            sim = cosine_similarity(kpi_embedding, col_emb.reshape(1, -1))[0][0]
            if sim > max_similarity:
                max_similarity = sim
                best_match = col

    # Apply semantic threshold
    if max_similarity >= threshold:
        return best_match, max_similarity
    else:
        return None, max_similarity


def normalize_columns(columns: list) -> list:
    return [normalize_column_name(col) for col in columns]


def match_column(kpi_col: str, available_columns: list, threshold: float, semantic_match_fn=None):
    match, score, _ = process.extractOne(kpi_col, available_columns, scorer=fuzz.token_set_ratio)
    if score >= threshold:
        return match
    elif semantic_match_fn:
        sem_match, score = semantic_match_fn(kpi_col, available_columns)
        return sem_match if sem_match else None
    else:
        return None

def match_column_with_score(kpi_col: str, available_columns: list, threshold: float = 75, semantic_match_fn=None):
    # Fuzzy matching first (0-100)
    match, score, _ = process.extractOne(kpi_col, available_columns, scorer=fuzz.token_set_ratio)
    if score >= threshold:
        return match, score
    
    # Semantic matching fallback (normalize to 0-100)
    if semantic_match_fn:
        sem_match, sem_score = semantic_match_fn(kpi_col, available_columns)
        sem_score = sem_score * 100  # convert 0-1 to 0-100
        if sem_match:
            return sem_match, sem_score
    
    # Nothing matched
    return None, 0

def match_base_kpis(column_names: list, base_kpis: dict, threshold: float, semantic_match_fn):
    normalized_columns = normalize_columns(column_names)
    kpi_status = {}

    for kpi_name, kpi_info in base_kpis.items():
       
        kpi_placeholders = kpi_info.get("columns", [])
        matched_columns = {}
        all_found = True

        for placeholder in kpi_placeholders:
            normalized_placeholder = normalize_column_name(placeholder)
            match = match_column(normalized_placeholder, normalized_columns, threshold, semantic_match_fn=semantic_match_fn)
            if match is None:
                all_found = False
            matched_columns[placeholder] = match  

        kpi_status[kpi_name] = {
            "calculable": all_found,
            "matched_columns": matched_columns,
            "kpi_info": kpi_info
        }

    return kpi_status


def match_derived_kpis(column_names: list, derived_kpis: dict, base_status: dict, df, threshold: float, semantic_match_fn):
    normalized_columns = normalize_columns(column_names)
    kpi_status = {}

    for kpi_name, kpi_info in derived_kpis.items():
        dependencies = kpi_info.get("dependencies", [])

        # Only proceed if all dependencies are calculable
        if all(base_status.get(dep, {}).get("calculable", False) for dep in dependencies):
            available_columns = normalized_columns.copy()

            # Add only calculable dependency KPIs to available pool
            for dep in dependencies:
                if base_status.get(dep, {}).get("calculable", False):
                    # Use the matched column name from base_status
                    matched_base_col = base_status[dep]["matched_columns"].get(dep)
                    if matched_base_col:
                        available_columns.append(normalize_column_name(matched_base_col))


            matched_columns = {}
            all_found = True

        
            for placeholder in kpi_info.get("columns", []):
                normalized_placeholder = normalize_column_name(placeholder)
                match = match_column(normalized_placeholder, available_columns, threshold, semantic_match_fn=semantic_match_fn)
                if match is None:
                    all_found = False
                matched_columns[placeholder] = match

            if kpi_name.lower().startswith(("monthly", "weekly")):
                date_match = next((v for k, v in matched_columns.items() if "date" in k.lower()), None)
                if date_match and date_match in df.columns:
                    period_type = "month" if "monthly" in kpi_name.lower() else "week"
                    enough_data = has_minimum_time_coverage(df, date_match, period=period_type, min_periods=2)
                    if not enough_data:
                        all_found = False


            kpi_status[kpi_name] = {
                "calculable": all_found,
                "matched_columns": matched_columns,
                "kpi_info": kpi_info
            }
        else:
            kpi_status[kpi_name] = {
                "calculable": False,
                "matched_columns": {},
                "kpi_info": kpi_info
            }

    kpi_status = {k: v for k, v in kpi_status.items() if v["calculable"]}

    return kpi_status


def match_kpis(column_names: list, combined_kpis: dict, df, threshold: float = 70, semantic_match_fn=None):
    base_kpis = {k: v for k, v in combined_kpis.items() if not v.get("dependencies")}
    derived_kpis = {k: v for k, v in combined_kpis.items() if v.get("dependencies")}

    base_status = match_base_kpis(column_names, base_kpis, threshold, semantic_match_fn)

    # Match derived KPIs with base columns included
    derived_status = match_derived_kpis(column_names, derived_kpis, base_status, df, threshold, semantic_match_fn)


    # Combine results
    kpi_status = {**base_status, **derived_status}
    return kpi_status


""" Kahn’s Algorithm:
 This helps us figure out the correct order to calculate KPIs.
 It starts with those that don’t depend on anything else,
 then moves on to KPIs that rely on already-computed ones.
 Basically, it ensures everything is calculated in the right sequence
 without missing prerequisites or causing dependency errors.

"""


def topological_sort(dependency_graph):
    # Build a reverse graph: what depends on each node
    reverse_graph = defaultdict(list)
    indegree = defaultdict(int)

    # Initialize indegrees
    for node, deps in dependency_graph.items():
        indegree[node] = indegree.get(node, 0)
        for dep in deps:
            reverse_graph[dep].append(node)
            indegree[node] += 1

    # Queue for nodes with no dependencies
    queue = deque([node for node, degree in indegree.items() if degree == 0])
    sorted_order = []

    while queue:
        node = queue.popleft()
        sorted_order.append(node)

        for dependent in reverse_graph[node]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    # Optional: detect circular dependencies
    if len(sorted_order) != len(indegree):
        raise ValueError("Circular dependency detected in KPIs")

    return sorted_order


def build_dependency_graph(kpis):
    dependency_graph = {}

    for kpi_name, kpi_data in kpis.items():
        dependency_graph[kpi_name] = kpi_data.get("dependencies", [])

    return topological_sort(dependency_graph)


def calculate_kpis(df: pd.DataFrame, available_kpis: dict, dependency_order: list):
    """
    Safely calculates KPIs defined in available_kpis following the given dependency order.
    - Silently handles errors and returns structured results.
    - Suitable for LangGraph or pipeline integration (no console output).

    Returns:
        dict: {
            kpi_name: {
                "value": <calculated result or None>,
                "success": <bool>,
                "error": <error message or None>
            }
        }
    """
    kpi_results = {}

    for kpi_name in dependency_order:
        kpi_data = available_kpis.get(kpi_name, {})
        if not kpi_data.get("calculable", False):
            kpi_results[kpi_name] = {
                "value": None,
                "success": False,
                "error": "Not calculable (missing dependencies or columns)"
            }
            continue

        formula = kpi_data.get("kpi_info", {}).get("formula")
        matched_columns = kpi_data.get("matched_columns", {})
        dependencies = kpi_data.get("kpi_info", {}).get("dependencies", [])

        if not formula:
            kpi_results[kpi_name] = {
                "value": None,
                "success": False,
                "error": "Missing formula"
            }
            continue

        # Replace placeholders (columns)
        try:
            for placeholder, real_col in matched_columns.items():
                if not real_col:
                    continue

                # Replace df['placeholder'] anywhere
                pattern_df = re.compile(rf"df\[['\"]{placeholder}['\"]\]", flags=re.IGNORECASE)
                formula = pattern_df.sub(f"df['{real_col}']", formula)

                # Replace groupby/string references ('placeholder' or "placeholder")
                pattern_str = re.compile(rf"['\"]{placeholder}['\"]", flags=re.IGNORECASE)
                formula = pattern_str.sub(f"'{real_col}'", formula)
        except Exception as e:
            kpi_results[kpi_name] = {
                "value": None,
                "success": False,
                "error": f"Error processing placeholders: {e}"
            }
            continue

        # Replace KPI dependencies
        try:
            for dep in dependencies:
                if dep in kpi_results and kpi_results[dep]["success"]:
                    formula = formula.replace(
                        f"kpis['{dep}']", f"({kpi_results[dep]['value']})"
                    )
        except Exception as e:
            kpi_results[kpi_name] = {
                "value": None,
                "success": False,
                "error": f"Error replacing dependencies: {e}"
            }
            continue

        # Evaluate formula safely
        try:
            result = eval(formula, {"df": df, "kpis": kpi_results, "np": np, "pd": pd})

            if isinstance(result, (int, float, np.number)):
                result = round(float(result), 4)

            kpi_results[kpi_name] = {
                "value": result,
                "success": True,
                "error": None
            }

        except Exception as e:
            kpi_results[kpi_name] = {
                "value": None,
                "success": False,
                "error": str(e)
            }


    return kpi_results


def detect_date_column(df: pd.DataFrame) -> str | None:
    """Try to auto-detect a datetime-like column."""
    for col in df.columns:
        if any(k in col.lower() for k in ["date", "time", "timestamp"]):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                if df[col].notna().sum() > len(df) * 0.5:
                    return col
            except Exception:
                pass
    # fallback by dtype
    for col in df.columns:
        if np.issubdtype(df[col].dtype, np.datetime64):
            return col
    return None



def calculate_kpis_temporal(df: pd.DataFrame, available_kpis: dict, dependency_order: list):
    """
    Wrapper around `calculate_kpis` to calculate KPIs per period (WoW or MoM).
    - Automatically detects date/time column.
    - Reuses base KPI calculator.
    - Returns per-period KPI results + metadata.
    """
    detected_date_col = detect_date_column(df)
    if not detected_date_col:
        return {
            "error": "No valid date/time column found.",
            "meta": {"period_type": None, "date_col": None}
        }

    period_type = determine_period_type(df, detected_date_col)
    df = add_period_column(df, detected_date_col, period_type)
    periods = sorted(df["period"].unique())

    results = {}
    for period in periods:
        df_period = df[df["period"] == period]
        kpi_out = calculate_kpis(df_period, available_kpis, dependency_order)
        results[str(period)] = kpi_out

    results["meta"] = {"period_type": period_type, "date_col": detected_date_col}
    return results







