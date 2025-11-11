"""
Statistical Rule-Based Data Cleaning for Retail Sales Data
No ML, pure statistical methods and business logic
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import re
from datetime import datetime
from collections import Counter


class StatisticalCleaner:
    """
    Statistical rule-based cleaner for retail sales data.
    Handles varying schemas and column names.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cleaning_report = {
            'original_shape': None,
            'final_shape': None,
            'column_types': {},
            'issues_found': [],
            'actions_taken': [],
            'quality_scores': {},
            'statistics': {}
        }
        self.column_profiles = {}
    
    def clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Main cleaning method"""
        print("=" * 80)
        print("STATISTICAL DATA CLEANING - Fashion Retail")
        print("=" * 80)
        
        self.cleaning_report['original_shape'] = df.shape
        df_clean = df.copy()
        
        # Phase 1: Profile columns
        print("\n📊 PHASE 1: Statistical Profiling")
        print("-" * 80)
        self._profile_columns(df_clean)
        
        # Phase 2: Detect and fix format issues
        print("\n🔧 PHASE 2: Format Standardization")
        print("-" * 80)
        df_clean = self._standardize_formats(df_clean)
        
        # Phase 3: Handle duplicates
        print("\n🔍 PHASE 3: Duplicate Detection")
        print("-" * 80)
        df_clean = self._handle_duplicates(df_clean)
        
        # Phase 4: Handle invalid values
        print("\n⚠️  PHASE 4: Invalid Value Correction")
        print("-" * 80)
        df_clean = self._correct_invalid_values(df_clean)
        
        # Phase 5: Handle outliers
        print("\n📈 PHASE 5: Outlier Detection & Handling")
        print("-" * 80)
        df_clean = self._handle_outliers(df_clean)
        
        # Phase 6: Handle missing values
        print("\n🔢 PHASE 6: Missing Value Imputation")
        print("-" * 80)
        df_clean = self._handle_missing_values(df_clean)
        
        # Phase 7: Cross-column validation
        print("\n🔗 PHASE 7: Cross-Column Validation")
        print("-" * 80)
        df_clean = self._cross_validate(df_clean)
        
        # Phase 8: Calculate quality scores
        print("\n✅ PHASE 8: Quality Assessment")
        print("-" * 80)
        self._calculate_quality_scores(df_clean)
        
        self.cleaning_report['final_shape'] = df_clean.shape
        
        return df_clean, self.cleaning_report
    
    def _profile_columns(self, df: pd.DataFrame):
        """Profile each column statistically"""
        for col in df.columns:
            profile = {
                'name': col,
                'dtype': str(df[col].dtype),
                'null_count': int(df[col].isnull().sum()),
                'null_pct': round(df[col].isnull().sum() / len(df) * 100, 2),
                'unique_count': int(df[col].nunique()),
                'unique_pct': round(df[col].nunique() / len(df) * 100, 2),
            }
            
            # Detect semantic type
            profile['semantic_type'] = self._detect_column_type(col, df[col])
            
            # Type-specific stats
            if pd.api.types.is_numeric_dtype(df[col]):
                profile.update({
                    'min': float(df[col].min()) if not df[col].isnull().all() else None,
                    'max': float(df[col].max()) if not df[col].isnull().all() else None,
                    'mean': float(df[col].mean()) if not df[col].isnull().all() else None,
                    'median': float(df[col].median()) if not df[col].isnull().all() else None,
                    'std': float(df[col].std()) if not df[col].isnull().all() else None,
                })
            elif profile['semantic_type'] == 'categorical':
                top_values = df[col].value_counts().head(5).to_dict()
                profile['top_values'] = {str(k): int(v) for k, v in top_values.items()}
            
            self.column_profiles[col] = profile
            self.cleaning_report['column_types'][col] = profile['semantic_type']
            
            print(f"  {col:30s} → {profile['semantic_type']:15s} "
                  f"(null: {profile['null_pct']:5.1f}%, unique: {profile['unique_pct']:5.1f}%)")
    
    def _detect_column_type(self, col_name: str, series: pd.Series) -> str:
        """Detect semantic type using statistical signatures"""
        col_lower = col_name.lower()
        
        # Check for date columns
        if any(kw in col_lower for kw in ['date', 'time', 'day', 'month', 'year']):
            return 'date'
        
        # Check for identifier columns
        if any(kw in col_lower for kw in ['id', 'reference', 'code']):
            return 'identifier'
        
        # Check for rating/score columns
        if any(kw in col_lower for kw in ['rating', 'review', 'score', 'stars']):
            return 'rating'
        
        # Check for amount/price columns
        if any(kw in col_lower for kw in ['amount', 'price', 'revenue', 'sales', 'value', 'cost']):
            return 'revenue'
        
        # Check for quantity columns
        if any(kw in col_lower for kw in ['quantity', 'qty', 'count', 'units', 'volume']):
            return 'quantity'
        
        # Check for product/item columns
        if any(kw in col_lower for kw in ['item', 'product', 'category', 'type']):
            return 'product'
        
        # Check for payment/method columns
        if any(kw in col_lower for kw in ['payment', 'method', 'channel']):
            return 'payment_method'
        
        # Infer from data characteristics
        uniqueness = series.nunique() / len(series) if len(series) > 0 else 0
        
        if uniqueness > 0.95:
            return 'identifier'
        elif uniqueness < 0.05:
            return 'categorical'
        elif pd.api.types.is_numeric_dtype(series):
            return 'numeric'
        else:
            return 'categorical'
    
    def _standardize_formats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize formats (dates, text, etc.)"""
        for col, profile in self.column_profiles.items():
            if profile['semantic_type'] == 'date':
                df[col] = self._parse_dates(df[col], col)
            elif profile['semantic_type'] in ['categorical', 'product', 'payment_method']:
                df[col] = self._standardize_text(df[col], col)
        
        return df
    
    def _parse_dates(self, series: pd.Series, col_name: str) -> pd.Series:
        """Parse dates with multiple format support"""
        if pd.api.types.is_datetime64_any_dtype(series):
            return series
        
        parsed = pd.Series([None] * len(series), index=series.index)
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%m-%d-%Y',
        ]
        
        success_count = 0
        error_count = 0
        
        for idx, val in series.items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            parsed_date = None
            
            # Try each format
            for fmt in formats:
                try:
                    parsed_date = pd.to_datetime(val_str, format=fmt)
                    break
                except:
                    continue
            
            # Fallback to pandas flexible parser
            if parsed_date is None:
                try:
                    parsed_date = pd.to_datetime(val_str, errors='coerce')
                except:
                    pass
            
            if parsed_date is not None and not pd.isna(parsed_date):
                # Validate date is reasonable (2020-2025)
                if 2020 <= parsed_date.year <= 2025:
                    parsed[idx] = parsed_date
                    success_count += 1
                else:
                    error_count += 1
                    self.cleaning_report['issues_found'].append({
                        'column': col_name,
                        'issue': 'invalid_date_range',
                        'value': str(val),
                        'index': int(idx)
                    })
            else:
                error_count += 1
                self.cleaning_report['issues_found'].append({
                    'column': col_name,
                    'issue': 'unparseable_date',
                    'value': str(val),
                    'index': int(idx)
                })
        
        action = f"Parsed {success_count} dates, {error_count} errors in '{col_name}'"
        self.cleaning_report['actions_taken'].append(action)
        print(f"  ✓ {action}")
        
        return parsed
    
    def _standardize_text(self, series: pd.Series, col_name: str) -> pd.Series:
        """Standardize text: trim, title case"""
        cleaned = series.copy()
        changes = 0
        
        for idx, val in series.items():
            if pd.isna(val):
                continue
            
            original = str(val)
            # Strip whitespace
            standardized = original.strip()
            # Title case
            standardized = standardized.title()
            # Collapse multiple spaces
            standardized = re.sub(r'\s+', ' ', standardized)
            
            if standardized != original:
                cleaned[idx] = standardized
                changes += 1
        
        if changes > 0:
            action = f"Standardized {changes} text values in '{col_name}'"
            self.cleaning_report['actions_taken'].append(action)
            print(f"  ✓ {action}")
        
        return cleaned
    
    def _handle_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and remove duplicates"""
        before = len(df)
        
        # Find exact duplicates
        duplicates = df.duplicated()
        dup_count = duplicates.sum()
        
        if dup_count > 0:
            # Log duplicate indices
            dup_indices = df[duplicates].index.tolist()
            self.cleaning_report['issues_found'].append({
                'issue': 'exact_duplicates',
                'count': int(dup_count),
                'indices': [int(i) for i in dup_indices[:10]]  # First 10
            })
            
            # Remove duplicates
            df = df[~duplicates].copy()
            
            action = f"Removed {dup_count} exact duplicate rows"
            self.cleaning_report['actions_taken'].append(action)
            print(f"  ✓ {action}")
        else:
            print(f"  ✓ No duplicates found")
        
        return df
    
    def _correct_invalid_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Correct invalid values using business logic"""
        
        for col, profile in self.column_profiles.items():
            if col not in df.columns:
                continue
            
            # Revenue/amount columns
            if profile['semantic_type'] == 'revenue':
                df = self._correct_revenue_values(df, col)
            
            # Rating columns
            elif profile['semantic_type'] == 'rating':
                df = self._correct_rating_values(df, col)
            
            # Date columns (already handled in parsing)
            elif profile['semantic_type'] == 'date':
                pass  # Already handled
        
        return df
    
    def _correct_revenue_values(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Correct invalid revenue values"""
        changes = 0
        
        # Handle negative values
        negative_mask = df[col] < 0
        negative_count = negative_mask.sum()
        
        if negative_count > 0:
            # Take absolute value (assuming data entry error, not refund)
            df.loc[negative_mask, col] = df.loc[negative_mask, col].abs()
            changes += negative_count
            
            self.cleaning_report['issues_found'].append({
                'column': col,
                'issue': 'negative_values',
                'count': int(negative_count),
                'action': 'converted_to_absolute'
            })
        
        # Handle zero values
        zero_mask = df[col] == 0
        zero_count = zero_mask.sum()
        
        if zero_count > 0:
            zero_pct = zero_count / len(df) * 100
            self.cleaning_report['issues_found'].append({
                'column': col,
                'issue': 'zero_values',
                'count': int(zero_count),
                'percentage': round(zero_pct, 2),
                'action': 'kept_as_is' if zero_pct < 5 else 'flagged_for_review'
            })
        
        if changes > 0:
            action = f"Corrected {changes} invalid values in '{col}'"
            self.cleaning_report['actions_taken'].append(action)
            print(f"  ✓ {action}")
        
        return df
    
    def _correct_rating_values(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Correct invalid rating values (should be 1-5)"""
        changes = 0
        
        # Clip to valid range
        invalid_mask = (df[col] < 1.0) | (df[col] > 5.0)
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            df.loc[df[col] < 1.0, col] = 1.0
            df.loc[df[col] > 5.0, col] = 5.0
            changes += invalid_count
            
            self.cleaning_report['issues_found'].append({
                'column': col,
                'issue': 'out_of_range_ratings',
                'count': int(invalid_count),
                'action': 'clipped_to_1_5'
            })
            
            action = f"Clipped {changes} out-of-range ratings in '{col}'"
            self.cleaning_report['actions_taken'].append(action)
            print(f"  ✓ {action}")
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and handle outliers using IQR method"""
        
        # Find product/category column for group-wise outlier detection
        product_col = None
        for col, profile in self.column_profiles.items():
            if profile['semantic_type'] == 'product':
                product_col = col
                break
        
        for col, profile in self.column_profiles.items():
            if col not in df.columns:
                continue
            
            if profile['semantic_type'] in ['revenue', 'quantity']:
                if product_col and product_col in df.columns:
                    # Group-wise outlier detection
                    df = self._detect_outliers_by_group(df, col, product_col)
                else:
                    # Global outlier detection
                    df = self._detect_outliers_global(df, col)
        
        return df
    
    def _detect_outliers_by_group(self, df: pd.DataFrame, col: str, group_col: str) -> pd.DataFrame:
        """Detect outliers per product category"""
        outlier_count = 0
        
        for group_val in df[group_col].unique():
            if pd.isna(group_val):
                continue
            
            mask = df[group_col] == group_val
            group_data = df.loc[mask, col].dropna()
            
            if len(group_data) < 4:  # Need at least 4 points for IQR
                continue
            
            Q1 = group_data.quantile(0.25)
            Q3 = group_data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            outliers = mask & ((df[col] < lower_bound) | (df[col] > upper_bound))
            outlier_count += outliers.sum()
            
            # Clip outliers
            df.loc[outliers & (df[col] < lower_bound), col] = lower_bound
            df.loc[outliers & (df[col] > upper_bound), col] = upper_bound
        
        if outlier_count > 0:
            action = f"Handled {outlier_count} outliers in '{col}' (by {group_col})"
            self.cleaning_report['actions_taken'].append(action)
            print(f"  ✓ {action}")
        
        return df
    
    def _detect_outliers_global(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Detect outliers globally"""
        data = df[col].dropna()
        
        if len(data) < 4:
            return df
        
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 3 * IQR
        upper_bound = Q3 + 3 * IQR
        
        outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_count = outliers.sum()
        
        if outlier_count > 0:
            # Clip outliers
            df.loc[df[col] < lower_bound, col] = lower_bound
            df.loc[df[col] > upper_bound, col] = upper_bound
            
            action = f"Handled {outlier_count} outliers in '{col}'"
            self.cleaning_report['actions_taken'].append(action)
            print(f"  ✓ {action}")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values using statistical methods"""
        
        # Find product column for group-wise imputation
        product_col = None
        for col, profile in self.column_profiles.items():
            if profile['semantic_type'] == 'product':
                product_col = col
                break
        
        for col, profile in self.column_profiles.items():
            if col not in df.columns:
                continue
            
            missing_count = df[col].isnull().sum()
            if missing_count == 0:
                continue
            
            if profile['semantic_type'] == 'revenue':
                if product_col and product_col in df.columns:
                    df = self._impute_by_group(df, col, product_col, method='median')
                else:
                    df[col].fillna(df[col].median(), inplace=True)
                    action = f"Filled {missing_count} missing in '{col}' with median"
                    self.cleaning_report['actions_taken'].append(action)
                    print(f"  ✓ {action}")
            
            elif profile['semantic_type'] == 'rating':
                # Use mode for ratings
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col].fillna(mode_val[0], inplace=True)
                    action = f"Filled {missing_count} missing in '{col}' with mode ({mode_val[0]})"
                    self.cleaning_report['actions_taken'].append(action)
                    print(f"  ✓ {action}")
            
            elif profile['semantic_type'] in ['categorical', 'payment_method']:
                # Use mode for categorical
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col].fillna(mode_val[0], inplace=True)
                    action = f"Filled {missing_count} missing in '{col}' with mode ({mode_val[0]})"
                    self.cleaning_report['actions_taken'].append(action)
                    print(f"  ✓ {action}")
            
            elif profile['semantic_type'] == 'date':
                # Forward fill dates
                df[col].fillna(method='ffill', inplace=True)
                df[col].fillna(method='bfill', inplace=True)
                action = f"Filled {missing_count} missing dates in '{col}' with forward fill"
                self.cleaning_report['actions_taken'].append(action)
                print(f"  ✓ {action}")
        
        return df
    
    def _impute_by_group(self, df: pd.DataFrame, col: str, group_col: str, method: str = 'median') -> pd.DataFrame:
        """Impute missing values by group"""
        missing_before = df[col].isnull().sum()
        
        for group_val in df[group_col].unique():
            if pd.isna(group_val):
                continue
            
            mask = df[group_col] == group_val
            group_data = df.loc[mask, col]
            
            if method == 'median':
                fill_value = group_data.median()
            elif method == 'mean':
                fill_value = group_data.mean()
            else:
                fill_value = group_data.mode()[0] if len(group_data.mode()) > 0 else None
            
            if pd.notna(fill_value):
                df.loc[mask & df[col].isnull(), col] = fill_value
        
        # Fallback: fill any remaining with global median
        if df[col].isnull().sum() > 0:
            df[col].fillna(df[col].median(), inplace=True)
        
        missing_after = df[col].isnull().sum()
        filled = missing_before - missing_after
        
        if filled > 0:
            action = f"Filled {filled} missing in '{col}' with group-wise {method} (by {group_col})"
            self.cleaning_report['actions_taken'].append(action)
            print(f"  ✓ {action}")
        
        return df
    
    def _cross_validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-column validation using business logic"""
        
        # Find relevant columns
        product_col = None
        revenue_col = None
        rating_col = None
        
        for col, profile in self.column_profiles.items():
            if profile['semantic_type'] == 'product':
                product_col = col
            elif profile['semantic_type'] == 'revenue':
                revenue_col = col
            elif profile['semantic_type'] == 'rating':
                rating_col = col
        
        # Validate revenue vs product type
        if product_col and revenue_col and both_exist(df, [product_col, revenue_col]):
            unusual_count = 0
            for product in df[product_col].unique():
                if pd.isna(product):
                    continue
                
                mask = df[product_col] == product
                product_prices = df.loc[mask, revenue_col]
                
                if len(product_prices) < 2:
                    continue
                
                median_price = product_prices.median()
                std_price = product_prices.std()
                
                # Flag if price deviates > 3 std from median for that product
                outliers = mask & (abs(df[revenue_col] - median_price) > 3 * std_price)
                unusual_count += outliers.sum()
            
            if unusual_count > 0:
                self.cleaning_report['issues_found'].append({
                    'issue': 'unusual_price_for_product',
                    'count': int(unusual_count),
                    'description': 'Prices significantly differ from typical price for product'
                })
                print(f"  ℹ️  Found {unusual_count} unusual price-product combinations")
        
        print(f"  ✓ Cross-validation complete")
        
        return df
    
    def _calculate_quality_scores(self, df: pd.DataFrame):
        """Calculate data quality scores"""
        
        # Completeness
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.count().sum()
        completeness = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
        
        # Validity (% of values that passed validation)
        total_issues = len([i for i in self.cleaning_report['issues_found'] 
                           if i.get('issue') not in ['exact_duplicates']])
        validity = max(0, 100 - (total_issues / df.shape[0] * 100)) if df.shape[0] > 0 else 0
        
        # Consistency (based on cross-validation)
        consistency = 95.0  # Default, adjust based on cross-validation results
        
        # Overall score
        overall = (completeness * 0.4 + validity * 0.4 + consistency * 0.2)
        
        self.cleaning_report['quality_scores'] = {
            'completeness': round(completeness, 2),
            'validity': round(validity, 2),
            'consistency': round(consistency, 2),
            'overall': round(overall, 2)
        }
        
        print(f"\n  📊 Completeness: {completeness:.1f}%")
        print(f"  📊 Validity: {validity:.1f}%")
        print(f"  📊 Consistency: {consistency:.1f}%")
        print(f"  📊 Overall Quality Score: {overall:.1f}/100")


def both_exist(df: pd.DataFrame, cols: List[str]) -> bool:
    """Check if all columns exist in dataframe"""
    return all(col in df.columns for col in cols)


def clean_retail_data(df: pd.DataFrame, config: Optional[Dict] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Main entry point for statistical cleaning.
    
    Args:
        df: Input DataFrame
        config: Optional configuration
    
    Returns:
        Tuple of (cleaned_df, cleaning_report)
    """
    cleaner = StatisticalCleaner(config=config)
    return cleaner.clean(df)

