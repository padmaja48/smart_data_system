"""
multiprocessing_tasks.py - CPU-bound tasks offloaded to separate processes.

Unlike threads, processes have their own memory space and bypass the GIL.
I use multiprocessing for heavy numerical computation (sorting, correlation).
Note: On Windows you need the if __name__ == '__main__' guard; Flask on Linux
      doesn't need it but I import safely anyway.
"""

import multiprocessing
import time
import os
import math
from heapq import merge


def _compute_column_stats(args):
    """
    Module-level function (not a lambda!) because multiprocessing needs
    pickleable functions — lambdas can't be pickled.

    Computes extended stats for a single column's values.
    """
    col_name, values = args
    if not values:
        return col_name, {}

    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)

    sorted_vals = sorted(values)
    mid = n // 2
    median = sorted_vals[mid] if n % 2 else (sorted_vals[mid - 1] + sorted_vals[mid]) / 2

    # percentiles
    def percentile(p):
        idx = int(math.ceil(p / 100.0 * n)) - 1
        return sorted_vals[max(0, min(idx, n - 1))]

    return col_name, {
        "mean": round(mean, 4),
        "median": round(median, 4),
        "std": round(std, 4),
        "variance": round(variance, 4),
        "min": round(sorted_vals[0], 4),
        "max": round(sorted_vals[-1], 4),
        "p25": round(percentile(25), 4),
        "p75": round(percentile(75), 4),
        "count": n
    }


def compute_stats_multiprocess(dataframe):
    """
    Use a process pool to compute stats for each numeric column in parallel.
    Returns dict: {column_name: stats_dict}
    """
    import numpy as np

    numeric_cols = dataframe.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return {}

    # prepare args list (col_name, list_of_values)
    args_list = [
        (col, dataframe[col].dropna().tolist())
        for col in numeric_cols
    ]

    start = time.perf_counter()

    # use at most 4 processes or number of CPUs
    num_workers = min(4, os.cpu_count() or 2, len(args_list))

    try:
        # spawn context is safer than fork for Flask
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(processes=num_workers) as pool:
            results = pool.map(_compute_column_stats, args_list)
    except Exception:
        # fallback: run sequentially if multiprocessing fails (e.g. in some envs)
        results = [_compute_column_stats(a) for a in args_list]

    elapsed = round(time.perf_counter() - start, 4)

    stats_dict = {col: stat for col, stat in results if stat}
    stats_dict["_meta"] = {
        "workers_used": num_workers,
        "processing_time_seconds": elapsed,
        "columns_processed": len(numeric_cols)
    }
    return stats_dict


def _sort_worker(values):
    """Worker function for parallel sort — sorts one chunk. Must be module-level for pickling."""
    return sorted(values)


def parallel_merge_sort(data, num_workers=4):
    """
    Parallel merge sort using multiprocessing.
    Splits data into chunks, sorts each in a separate process, then merges.
    
    Returns:
        sorted_data (list), time_taken (float)
    """
    if len(data) <= 1:
        return data, 0.0
    
    start = time.perf_counter()
    
    # Split data into chunks
    chunk_size = max(1, len(data) // num_workers)
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    try:
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(processes=min(len(chunks), num_workers)) as pool:
            sorted_chunks = pool.map(_sort_worker, chunks)
    except Exception:
        # Fallback: sequential sort
        sorted_chunks = [_sort_worker(chunk) for chunk in chunks]
    
    # Merge sorted chunks
    merged = list(merge(*sorted_chunks))
    
    elapsed = time.perf_counter() - start
    return merged, elapsed



def parallel_sort_demo(large_list, num_splits=4):
    """
    Splits a list into chunks, sorts each chunk in a separate process,
    then merges using heapq.merge.

    This is basically a parallel merge sort — good for showing off
    multiprocessing for CPU-bound work.
    """
    import heapq

    chunk_size = len(large_list) // num_splits
    chunks = [large_list[i:i + chunk_size] for i in range(0, len(large_list), chunk_size)]

    start = time.perf_counter()
    try:
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(processes=num_splits) as pool:
            sorted_chunks = pool.map(_sort_worker, chunks)
    except Exception:
        sorted_chunks = [sorted(c) for c in chunks]

    merged = list(heapq.merge(*sorted_chunks))
    elapsed = round(time.perf_counter() - start, 4)

    return {
        "sorted_length": len(merged),
        "sort_time_seconds": elapsed,
        "num_processes": num_splits
    }
