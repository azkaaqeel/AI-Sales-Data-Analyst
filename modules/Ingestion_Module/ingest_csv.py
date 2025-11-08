"""Module for handling CSV file ingestion with validation and type inference."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Union, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVValidationError(Exception):
    """Custom exception for CSV validation errors."""
    pass

def validate_numerical_columns(df: pd.DataFrame) -> Tuple[bool, list]:
    """
    Check if numerical columns contain valid numbers.
    
    Returns:
        Tuple of (is_valid, list of problematic columns)
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    problems = []
    
    for col in numeric_cols:
        if df[col].isna().any():
            problems.append(f"{col} (contains missing values)")
        elif (df[col] < 0).any():
            problems.append(f"{col} (contains negative values)")
            
    return len(problems) == 0, problems

def infer_date_format(date_series: pd.Series) -> Optional[str]:
    """
    Attempt to infer the date format from a series.
    
    Returns:
        str: Inferred format string or None if no format detected
    """
    common_formats = [
        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
        '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y',
        '%Y%m%d', '%d%m%Y', '%m%d%Y'
    ]
    
    # Take a sample value
    sample = date_series.dropna().iloc[0] if not date_series.empty else None
    if not sample:
        return None
    
    # Try common formats
    for fmt in common_formats:
        try:
            datetime.strptime(str(sample), fmt)
            # Verify it works for the whole series
            pd.to_datetime(date_series, format=fmt, errors='raise')
            return fmt
        except (ValueError, TypeError):
            continue
    
    return None

def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detect and classify columns into types (date, numeric, categorical).
    
    Returns:
        Dict mapping column names to their detected types
    """
    column_types = {}
    
    for col in df.columns:
        # Check for date first
        try:
            pd.to_datetime(df[col], errors='raise')
            column_types[col] = 'date'
            continue
        except (ValueError, TypeError):
            pass
        
        # Check if numeric
        if np.issubdtype(df[col].dtype, np.number):
            column_types[col] = 'numeric'
        else:
            # Check if categorical (if few unique values relative to total)
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio < 0.2:  # Less than 20% unique values
                column_types[col] = 'categorical'
            else:
                column_types[col] = 'text'
    
    return column_types


def ingest_csv(
    file_path: Union[str, Path],
    date_column: str = None,
    encoding: str = 'utf-8',
    min_rows: int = 1,
    max_rows: int = 1000000,
    validate_numeric: bool = True,
) -> Tuple[pd.DataFrame, Dict]:
    """
    Ingest and validate a CSV file with smart type inference.
    
    Args:
        file_path: Path to the CSV file
        date_column: Name of the date column (will attempt to auto-detect if None)
        encoding: File encoding (default: utf-8)
        expected_columns: List of required columns (optional)
        min_rows: Minimum number of rows required (default: 1)
        max_rows: Maximum number of rows allowed (default: 1M)
        validate_numeric: Whether to validate numerical columns (default: True)
    
    Returns:
        Tuple of (DataFrame, metadata dict)
        
    Raises:
        CSVValidationError: If validation fails
        FileNotFoundError: If file doesn't exist
        pd.errors.EmptyDataError: If file is empty
        UnicodeDecodeError: If encoding is incorrect
    """
    try:
        # Convert to Path object
        file_path = Path(file_path)
        
        # Basic file checks
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.stat().st_size == 0:
            raise pd.errors.EmptyDataError("File is empty")
        
        # Read CSV with type inference
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            parse_dates=False,  # We'll handle date parsing ourselves
            low_memory=False  # More accurate type inference
        )
        
        # Validate row count
        if len(df) < min_rows:
            raise CSVValidationError(f"File contains fewer than {min_rows} rows")
        if len(df) > max_rows:
            raise CSVValidationError(f"File contains more than {max_rows} rows")
        
        
        # Detect column types
        column_types = detect_column_types(df)
        
        # Find date column if not specified
        if date_column is None:
            date_cols = [col for col, type_ in column_types.items() 
                        if type_ == 'date']
            if date_cols:
                date_column = date_cols[0]
                logger.info(f"Auto-detected date column: {date_column}")
        
        # Convert date column if specified
        if date_column:
            if date_column not in df.columns:
                raise CSVValidationError(f"Specified date column not found: {date_column}")
            
            # Try to infer date format
            date_format = infer_date_format(df[date_column])
            if date_format:
                df[date_column] = pd.to_datetime(
                    df[date_column],
                    format=date_format,
                    errors='coerce'
                )
            else:
                df[date_column] = pd.to_datetime(
                    df[date_column],
                    errors='coerce'
                )
            
            # Check for invalid dates
            if df[date_column].isna().any():
                invalid_dates = df[df[date_column].isna()][date_column].head()
                raise CSVValidationError(
                    f"Invalid dates found in {date_column}. Examples: {invalid_dates.tolist()}"
                )
        
        # Validate numerical columns if requested
        if validate_numeric:
            is_valid, problems = validate_numerical_columns(df)
            if not is_valid:
                raise CSVValidationError(
                    f"Validation failed for numerical columns: {', '.join(problems)}"
                )
        
        # Create metadata
        metadata = {
            'filename': file_path.name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'column_types': column_types,
            'date_column': date_column,
            'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
            'timestamp': datetime.now().isoformat(),
        }
        
        if date_column:
            metadata.update({
                'date_range': {
                    'start': df[date_column].min().isoformat(),
                    'end': df[date_column].max().isoformat()
                }
            })
        
        logger.info(f"Successfully ingested CSV with {len(df)} rows and {len(df.columns)} columns")
        return df, metadata
        
    except pd.errors.ParserError as e:
        raise CSVValidationError(f"Failed to parse CSV: {str(e)}")
    except UnicodeDecodeError:
        raise CSVValidationError(f"Failed to decode file with encoding {encoding}. Try a different encoding.")
    except Exception as e:
        raise CSVValidationError(f"Unexpected error during CSV ingestion: {str(e)}")

def suggest_encoding(file_path: Union[str, Path]) -> str:
    """
    Attempt to detect the correct encoding of a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        str: Suggested encoding
    """
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
                return encoding
        except UnicodeDecodeError:
            continue
    
    return 'utf-8'  # Default to UTF-8 if no encoding works