"""
generators.py - Generator functions for memory-efficient data processing.

Demonstrates:
- Generator functions with yield
- Lazy evaluation and memory efficiency
- Processing large datasets without loading everything into memory
- Generator as a way to implement coroutines
"""

import json
import os


def csv_chunk_generator(filepath, chunk_size=100):
    """
    Generator that yields chunks of rows from a CSV file.
    Useful for processing large files without loading everything into memory.
    """
    import pandas as pd
    try:
        reader = pd.read_csv(filepath, chunksize=chunk_size)
        for chunk in reader:
            yield chunk
    except Exception as e:
        yield None


def statistics_generator(dataframe):
    """
    Generator that yields one column's statistics at a time.
    Memory-efficient: processes one column at a time without collecting all stats.
    """
    import numpy as np
    import math
    numeric_cols = dataframe.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        series = dataframe[col].dropna()
        if len(series) == 0:
            continue
        
        mean_val = series.mean()
        median_val = series.median()
        std_val = series.std()
        min_val = series.min()
        max_val = series.max()
        
        def safe_float(val):
            if isinstance(val, (float, np.floating)):
                if math.isnan(val) or math.isinf(val):
                    return None
            return round(float(val), 4) if val is not None else None
        
        yield {
            "column": col,
            "mean": safe_float(mean_val),
            "median": safe_float(median_val),
            "std": safe_float(std_val),
            "min": safe_float(min_val),
            "max": safe_float(max_val),
            "count": int(series.count())
        }


def fibonacci_generator(n=None):
    """
    Generator that yields Fibonacci numbers indefinitely (if n is None)
    or up to n numbers if n is specified.
    
    Example:
        fib = fibonacci_generator(5)
        list(fib) -> [0, 1, 1, 2, 3]
    """
    a, b = 0, 1
    count = 0
    while n is None or count < n:
        yield a
        a, b = b, a + b
        count += 1


def log_stream_generator(log_file):
    """
    Generator that streams log entries from a JSON log file one at a time
    without loading all into memory. Useful for large log files.
    """
    if not os.path.exists(log_file):
        return
    
    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
        for log_entry in logs:
            yield log_entry
    except (json.JSONDecodeError, IOError):
        return


def infinite_sequence_generator():
    """
    Generator that yields an infinite sequence of integers.
    Demonstrates unbounded generator.
    """
    count = 0
    while True:
        yield count
        count += 1
