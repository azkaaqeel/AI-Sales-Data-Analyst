"""
Safe Custom KPI Calculator
Allows users to define custom KPIs with formulas using available columns.
"""
import pandas as pd
import re
from typing import Dict, Any, List, Optional
import numpy as np

class CustomKPICalculator:
    """
    Safely evaluates custom KPI formulas.
    Supports basic arithmetic and pandas aggregations.
    """
    
    ALLOWED_AGGREGATIONS = ['sum', 'avg', 'mean', 'count', 'nunique', 'min', 'max', 'median']
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        self.all_columns = df.columns.tolist()
        
        # Identify date columns (exclude from KPI builder)
        date_keywords = ['date', 'time', 'timestamp', 'day', 'month', 'year']
        self.date_columns = [
            col for col in df.columns 
            if any(keyword in col.lower() for keyword in date_keywords)
            or pd.api.types.is_datetime64_any_dtype(df[col])
        ]
        
        # Countable columns (all except dates - for unique counts)
        self.countable_columns = [col for col in self.all_columns if col not in self.date_columns]
    
    def get_available_columns(self) -> Dict[str, List[str]]:
        """Return available columns categorized by type."""
        return {
            'numeric': self.numeric_columns,  # For sum, avg, min, max
            'countable': self.countable_columns,  # For count (includes IDs, categories)
            'all': self.countable_columns  # Exclude dates
        }
    
    def validate_formula(self, formula: str) -> Dict[str, Any]:
        """
        Validate a formula before execution.
        
        Returns:
            {
                'valid': bool,
                'error': str (if invalid),
                'columns_used': list of column names,
                'aggregations_used': list of aggregation functions
            }
        """
        try:
            # Extract column names (inside quotes or brackets)
            column_pattern = r"['\"]([^'\"]+)['\"]|\[([^\]]+)\]"
            columns_found = re.findall(column_pattern, formula)
            columns_used = [col for group in columns_found for col in group if col]
            
            # Check if columns exist
            invalid_cols = [col for col in columns_used if col not in self.all_columns]
            if invalid_cols:
                return {
                    'valid': False,
                    'error': f"Columns not found: {', '.join(invalid_cols)}",
                    'columns_used': columns_used,
                    'aggregations_used': []
                }
            
            # Extract aggregation functions
            agg_pattern = r'\b(' + '|'.join(self.ALLOWED_AGGREGATIONS) + r')\s*\('
            aggregations_used = re.findall(agg_pattern, formula.lower())
            
            # Check for dangerous operations
            dangerous_keywords = ['import', 'exec', 'eval', 'compile', '__', 'open', 'file']
            if any(keyword in formula.lower() for keyword in dangerous_keywords):
                return {
                    'valid': False,
                    'error': 'Formula contains disallowed operations',
                    'columns_used': columns_used,
                    'aggregations_used': aggregations_used
                }
            
            return {
                'valid': True,
                'error': None,
                'columns_used': columns_used,
                'aggregations_used': aggregations_used
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Formula validation error: {str(e)}',
                'columns_used': [],
                'aggregations_used': []
            }
    
    def calculate_kpi(self, formula: str, kpi_name: str = "Custom KPI") -> Dict[str, Any]:
        """
        Calculate a custom KPI using the provided formula.
        
        Formula syntax:
            - Column names in quotes: "revenue" or 'revenue'
            - Aggregations: sum("revenue"), avg("price"), count("order_id")
            - Arithmetic: +, -, *, /, ()
            - Example: sum("revenue") / count("order_id")
        
        Returns:
            {
                'success': bool,
                'value': float or dict,
                'error': str (if failed),
                'formula': str,
                'description': str
            }
        """
        # Validate first
        validation = self.validate_formula(formula)
        if not validation['valid']:
            return {
                'success': False,
                'value': None,
                'error': validation['error'],
                'formula': formula,
                'description': ''
            }
        
        try:
            # Replace column references with actual pandas operations
            working_formula = formula
            
            # First, replace aggregations with proper pandas syntax
            for agg in self.ALLOWED_AGGREGATIONS:
                # Find all aggregation patterns: agg("column_name") or agg('column_name')
                pattern = f"{agg}\\s*\\(['\"]([^'\"]+)['\"]\\)"
                matches = re.findall(pattern, working_formula, flags=re.IGNORECASE)
                
                for col_name in matches:
                    if col_name in self.df.columns:
                        # Validate aggregation is appropriate for column type
                        is_numeric = col_name in self.numeric_columns
                        numeric_only_aggs = ['sum', 'avg', 'mean', 'median', 'min', 'max']
                        
                        if agg in numeric_only_aggs and not is_numeric:
                            raise ValueError(f"Cannot use {agg}() on non-numeric column '{col_name}'. Use count() or nunique() instead.")
                        
                        # Create the full pattern to replace
                        full_pattern = f"{agg}\\s*\\(['\"]?{re.escape(col_name)}['\"]?\\)"
                        
                        # Create the replacement based on aggregation type
                        if agg == 'avg':
                            replacement = f"self.df['{col_name}'].mean()"
                        elif agg == 'count':
                            replacement = f"self.df['{col_name}'].count()"
                        elif agg == 'nunique':
                            replacement = f"self.df['{col_name}'].nunique()"
                        else:
                            replacement = f"self.df['{col_name}'].{agg}()"
                        
                        # Replace in formula
                        working_formula = re.sub(full_pattern, replacement, working_formula, flags=re.IGNORECASE)
            
            # Safe evaluation in restricted namespace
            namespace = {
                'self': self,
                'np': np,
                'sum': np.sum,
                'mean': np.mean,
                'avg': np.mean,
                'count': lambda x: len(x),
                'nunique': lambda x: len(set(x)),
                'min': np.min,
                'max': np.max,
                'median': np.median,
                '__builtins__': {}
            }
            
            # Execute formula
            result = eval(working_formula, namespace, {})
            
            # Handle pandas Series (if formula returns a series)
            if isinstance(result, pd.Series):
                # If it's an aggregation result, get the scalar
                if len(result) == 1:
                    result = result.iloc[0]
                else:
                    # Return top values as dict
                    result = result.head(10).to_dict()
            
            # Handle divide by zero / infinity
            if isinstance(result, (int, float)):
                if np.isnan(result) or np.isinf(result):
                    return {
                        'success': False,
                        'value': None,
                        'error': 'Calculation resulted in invalid value (NaN/Inf). Check for division by zero.',
                        'formula': formula,
                        'description': ''
                    }
            
            # Generate description
            description = self._generate_description(formula, validation['columns_used'], validation['aggregations_used'])
            
            return {
                'success': True,
                'value': float(result) if isinstance(result, (int, float, np.number)) else result,
                'error': None,
                'formula': formula,
                'description': description
            }
            
        except ZeroDivisionError:
            return {
                'success': False,
                'value': None,
                'error': 'Division by zero error in formula',
                'formula': formula,
                'description': ''
            }
        except Exception as e:
            return {
                'success': False,
                'value': None,
                'error': f'Calculation error: {str(e)}',
                'formula': formula,
                'description': ''
            }
    
    def _generate_description(self, formula: str, columns: List[str], aggregations: List[str]) -> str:
        """Generate a human-readable description of the KPI."""
        desc_parts = []
        
        if aggregations:
            agg_str = ', '.join(set(aggregations))
            desc_parts.append(f"Calculates {agg_str}")
        
        if columns:
            col_str = ', '.join(columns)
            desc_parts.append(f"using columns: {col_str}")
        
        return ' '.join(desc_parts) if desc_parts else "Custom calculated metric"
    
    def get_formula_templates(self) -> List[Dict[str, str]]:
        """Return pre-built formula templates for common KPIs."""
        templates = [
            {
                'name': 'Average Order Value',
                'formula': 'sum("revenue") / count("order_id")',
                'description': 'Total revenue divided by number of orders',
                'requires': ['revenue column (numeric)', 'order_id column']
            },
            {
                'name': 'Conversion Rate',
                'formula': '(count("conversions") / count("visitors")) * 100',
                'description': 'Percentage of visitors who converted',
                'requires': ['conversions column', 'visitors column']
            },
            {
                'name': 'Average Revenue Per Customer',
                'formula': 'sum("revenue") / count("customer_id")',
                'description': 'Total revenue divided by unique customers',
                'requires': ['revenue column (numeric)', 'customer_id column']
            },
            {
                'name': 'Profit Margin',
                'formula': '((sum("revenue") - sum("cost")) / sum("revenue")) * 100',
                'description': 'Profit as percentage of revenue',
                'requires': ['revenue column (numeric)', 'cost column (numeric)']
            },
            {
                'name': 'Average Transaction Size',
                'formula': 'sum("quantity") / count("order_id")',
                'description': 'Average items per order',
                'requires': ['quantity column (numeric)', 'order_id column']
            }
        ]
        
        return templates

