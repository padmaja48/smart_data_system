"""
processing.py - Core data processing engine.
"""

import os
import io
import sys
import math
import json
import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from abc import ABC, abstractmethod
from utils.mixins import TimestampMixin, SerializableMixin, LoggableMixin
from utils.decorators import log_execution, timer
from utils.generators import statistics_generator

CHARTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'charts')


def _ensure_charts_dir():
    os.makedirs(CHARTS_DIR, exist_ok=True)


# ── Abstract base class ────────────────────────────────────────────────────────

class DataProcessor(ABC):
    """Abstract base class that defines the processor interface."""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.dataframe = None

    @abstractmethod
    def load(self, source) -> pd.DataFrame:
        """Load data from source and return a DataFrame."""
        pass

    @abstractmethod
    def process(self) -> dict:
        """Process loaded data and return stats dict."""
        pass

    def summary(self) -> str:
        if self.dataframe is None:
            return "No data loaded"
        return f"{self.source_name}: {len(self.dataframe)} rows x {len(self.dataframe.columns)} cols"


# ── DatasetResult with operator overloading ────────────────────────────────────

class DatasetResult(TimestampMixin, SerializableMixin):
    """
    Holds the result of one dataset processing run.
    Inherits from TWO mixins (multiple inheritance).
    MRO: DatasetResult -> TimestampMixin -> SerializableMixin -> object
    """

    def __init__(self, name: str, stats: dict, chart_paths: list = None):
        self._init_timestamps()
        self.name = name
        self.stats = stats
        self.chart_paths = chart_paths or []
        self.row_count = stats.get("row_count", 0)

    def __add__(self, other):
        """Merge two DatasetResult objects."""
        merged_stats = {**self.stats}
        merged_charts = self.chart_paths + other.chart_paths
        return DatasetResult(
            name=f"{self.name} + {other.name}",
            stats=merged_stats,
            chart_paths=merged_charts
        )

    def __repr__(self):
        return f"<DatasetResult name={self.name!r} rows={self.row_count}>"

    def __len__(self):
        return self.row_count


# ── CSV Processor ──────────────────────────────────────────────────────────────

class CSVProcessor(DataProcessor, LoggableMixin):
    """
    Processes CSV files.
    MRO: CSVProcessor -> DataProcessor -> LoggableMixin -> ABC -> object
    """

    def __init__(self, source_name="CSV"):
        super().__init__(source_name)
        self._init_log()

    @log_execution
    @timer
    def load(self, source) -> pd.DataFrame:
        """Load CSV from filepath or file-like object."""
        self.log_event("Loading CSV")
        if isinstance(source, str):
            self.dataframe = pd.read_csv(source)
        else:
            try:
                source.seek(0)
            except (AttributeError, OSError):
                pass
            
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='replace')
            self.dataframe = pd.read_csv(io.StringIO(content))
        self.log_event(f"Loaded {len(self.dataframe)} rows")
        return self.dataframe

    @log_execution
    @timer
    def process(self) -> dict:
        if self.dataframe is None:
            raise ValueError("Call load() before process()")
        stats = self._compute_stats()
        self.log_event("Processing complete")
        return stats

    def _compute_stats(self) -> dict:
        df = self.dataframe
        result = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "missing_values": int(df.isnull().sum().sum()),
            "column_stats": {}
        }
        for col_stat in statistics_generator(df):
            result["column_stats"][col_stat["column"]] = col_stat
        return result


# ── JSON Processor ─────────────────────────────────────────────────────────────

class JSONProcessor(DataProcessor, LoggableMixin):
    """Processes JSON data (array of objects -> DataFrame)."""

    def __init__(self, source_name="JSON"):
        super().__init__(source_name)
        self._init_log()

    @log_execution
    def load(self, source) -> pd.DataFrame:
        self.log_event("Loading JSON")
        if isinstance(source, str):
            with open(source, 'r') as f:
                data = json.load(f)
        else:
            try:
                source.seek(0)
            except (AttributeError, OSError):
                pass
            
            raw = source.read()
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')
            data = json.loads(raw)

        if isinstance(data, list):
            self.dataframe = pd.DataFrame(data)
        elif isinstance(data, dict):
            self.dataframe = pd.DataFrame([data])
        else:
            raise ValueError("JSON must be an array of objects or a single object")
        
        self.log_event(f"Loaded {len(self.dataframe)} rows")
        return self.dataframe

    @log_execution
    def process(self) -> dict:
        if self.dataframe is None:
            raise ValueError("Call load() before process()")
        stats = self._compute_stats()
        self.log_event("Processing complete")
        return stats

    def _compute_stats(self) -> dict:
        df = self.dataframe
        result = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "missing_values": int(df.isnull().sum().sum()),
            "column_stats": {}
        }
        for col_stat in statistics_generator(df):
            result["column_stats"][col_stat["column"]] = col_stat
        return result


# ── Chart generation ───────────────────────────────────────────────────────────

CHART_COLORS = ['#6C63FF', '#FF6584', '#43D399', '#F5A623', '#50E3C2', '#B8860B']


def _make_filename(prefix, ext="png"):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{ts}.{ext}"


@timer
def generate_bar_chart(stats: dict, dataset_name: str) -> str:
    """Bar chart of column means."""
    _ensure_charts_dir()
    col_stats = stats.get("column_stats", {})
    if not col_stats:
        return None

    cols = list(col_stats.keys())
    values = [col_stats[c].get("mean", 0) for c in cols]

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    bars = ax.bar(cols, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#F06292'][:len(cols)], 
                  edgecolor='black', linewidth=1.2, width=0.6)
    ax.set_title(f'Column Means - {dataset_name}', fontsize=13, fontweight='bold')
    ax.set_ylabel('Mean', fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    fname = _make_filename("bar")
    fpath = os.path.join(CHARTS_DIR, fname)
    plt.savefig(fpath, dpi=80, format='png', bbox_inches='tight', facecolor='white')
    plt.close('all')
    return f"charts/{fname}"


@timer
def generate_line_chart(stats: dict, dataset_name: str) -> str:
    """Line chart comparing mean, median, and std for each column."""
    _ensure_charts_dir()
    col_stats = stats.get("column_stats", {})
    if not col_stats:
        return None

    cols = list(col_stats.keys())
    means = [col_stats[c].get("mean", 0) for c in cols]
    medians = [col_stats[c].get("median", 0) for c in cols]
    stds = [col_stats[c].get("std", 0) for c in cols]
    x = range(len(cols))

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    ax.plot(x, means, 'o-', color='#FF6B6B', label='Mean', linewidth=2, markersize=7)
    ax.plot(x, medians, 's--', color='#4ECDC4', label='Median', linewidth=2, markersize=7)
    ax.plot(x, stds, '^:', color='#45B7D1', label='Std Dev', linewidth=2, markersize=7)

    ax.set_xticks(list(x))
    ax.set_xticklabels(cols, rotation=45, ha='right')
    ax.set_title(f'Statistics Overview - {dataset_name}', fontsize=13, fontweight='bold')
    ax.set_ylabel('Value', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', framealpha=0.9)

    plt.tight_layout()
    fname = _make_filename("line")
    fpath = os.path.join(CHARTS_DIR, fname)
    plt.savefig(fpath, dpi=80, format='png', bbox_inches='tight', facecolor='white')
    plt.close('all')
    return f"charts/{fname}"


@timer
def generate_distribution_chart(dataframe: pd.DataFrame, dataset_name: str) -> str:
    """Histogram distributions for numeric columns (up to 4)."""
    _ensure_charts_dir()
    numeric_cols = dataframe.select_dtypes(include=[np.number]).columns.tolist()[:4]
    if not numeric_cols:
        return None

    n = len(numeric_cols)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    fig.patch.set_facecolor('white')
    if n == 1:
        axes = [axes]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    for i, (ax, col) in enumerate(zip(axes, numeric_cols)):
        data = dataframe[col].dropna()
        ax.set_facecolor('white')
        ax.hist(data, bins=15, color=colors[i % len(colors)], edgecolor='black', linewidth=0.8, alpha=0.7)
        ax.set_title(col, fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

    fig.suptitle(f'Distributions - {dataset_name}', fontsize=13, fontweight='bold')
    plt.tight_layout()
    
    fname = _make_filename("dist")
    fpath = os.path.join(CHARTS_DIR, fname)
    plt.savefig(fpath, dpi=80, format='png', bbox_inches='tight', facecolor='white')
    plt.close('all')
    return f"charts/{fname}"


def get_processor_for_file(filename: str, file_obj):
    """Factory function — picks the right processor based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        return CSVProcessor(source_name=filename), file_obj
    elif ext == '.json':
        return JSONProcessor(source_name=filename), file_obj
    else:
        raise ValueError(f"Unsupported file type: {ext} (only .csv and .json)")
