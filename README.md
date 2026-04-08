# Smart Data Processing & Validation Dashboard

**Advanced Python Project — Full Stack Web Application**

---

## Overview

This project is a Flask-based web application that validates user inputs using Regular Expressions, processes CSV/JSON datasets using Pandas and NumPy, generates charts with Matplotlib, and runs concurrent processing using Python's `threading` and `multiprocessing` modules. All processed results are stored using JSON serialization.

---

## Project Structure

```
smart_data_system/
├── app.py                        # Flask entry point, all API routes
├── requirements.txt
├── README.md
├── templates/
│   ├── index.html                # Registration & upload page
│   └── dashboard.html            # Analytics dashboard
├── static/
│   ├── style.css
│   ├── script.js
│   └── charts/                   # Generated chart images saved here
├── data/
│   ├── datasets.json             # Serialized dataset results
│   ├── users.json                # Registered users
│   └── app_logs.json             # Function execution logs
├── modules/
│   ├── validation.py             # Regex validators + abstract class
│   ├── processing.py             # OOP processors + chart generation
│   ├── threading_tasks.py        # Multithreaded chunk processing
│   ├── multiprocessing_tasks.py  # Process pool stats computation
│   └── serialization.py         # JSON read/write helpers
└── utils/
    ├── decorators.py             # @log_execution, @timer, @retry, @validate_input
    ├── iterators.py              # DatasetRowIterator, CircularBufferIterator
    ├── generators.py             # csv_chunk_generator, statistics_generator, fibonacci_generator
    └── mixins.py                 # TimestampMixin, SerializableMixin, ValidationMixin, LoggableMixin
```

---

## Setup Instructions

### 1. Create a virtual environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```

Open your browser at `http://localhost:5000`

---

## Python Concepts Implemented

### Iterators and Generators
- **`DatasetRowIterator`** (iterators.py) — Custom iterator implementing `__iter__` and `__next__` that walks through dataset rows one at a time
- **`CircularBufferIterator`** (iterators.py) — Fixed-capacity circular buffer with iterator protocol, used for the live activity log
- **`RangeStepIterator`** (iterators.py) — Float-step range iterator
- **`statistics_generator`** (generators.py) — Generator that yields per-column stats one at a time (lazy evaluation, memory-efficient)
- **`csv_chunk_generator`** (generators.py) — Yields CSV rows in chunks using pandas `chunksize`
- **`fibonacci_generator`** (generators.py) — Classic generator demo exposed via `/api/fibonacci`
- **`log_stream_generator`** (generators.py) — Streams log entries from JSON without loading all into memory

### Decorators and Closures
- **`@log_execution`** — Logs function name, timestamp, and success/failure to `app_logs.json`
- **`@timer`** — Measures execution time using `time.perf_counter()`, stores result in `wrapper.last_execution_time`
- **`@retry(max_attempts, delay)`** — Decorator factory / closure that wraps functions with retry logic (closes over `max_attempts` and `delay`)
- **`@validate_input`** — Guards against None/empty arguments
- Multiple decorators are stacked on the same function (e.g., `@log_execution @timer` on route handlers)

### Advanced OOP
- **`DataProcessor`** (processing.py) — Abstract Base Class with `@abstractmethod` `load()` and `process()`
- **`CSVProcessor`** and **`JSONProcessor`** — Concrete subclasses of `DataProcessor`, also inherit from `LoggableMixin` (multiple inheritance)
- **`DatasetResult`** — Inherits from both `TimestampMixin` and `SerializableMixin`; implements `__add__` (operator overloading), `__repr__`, and `__len__`
- **`FormValidator`** — Inherits from both `ValidationMixin` and `LoggableMixin`; demonstrates Python MRO
- **MRO Example**: `CSVProcessor → DataProcessor → LoggableMixin → ABC → object`
- **Four Mixin classes**: `TimestampMixin`, `SerializableMixin`, `ValidationMixin`, `LoggableMixin`

### Python Core Libraries
- `os` — file paths, directory creation (`os.makedirs`, `os.path.join`)
- `sys` — path manipulation (`sys.path.insert`), version info
- `datetime` — timestamps, ISO format conversion
- `math` — manual standard deviation, percentile, square root in multiprocessing worker
- `json` — data serialization/deserialization throughout
- `re` — compiled regex patterns for name, email, phone, password validation
- `io` — `StringIO` for reading uploaded file content as a stream
- `abc` — `ABC`, `abstractmethod` for abstract base class

### External Libraries
- **NumPy** — `select_dtypes`, numerical operations
- **Pandas** — `read_csv`, `read_csv(chunksize=...)`, `DataFrame`, `.dropna()`, `.describe()`
- **Matplotlib** — bar charts, line charts, distribution histograms with custom dark theme

### Multithreading
- **`DatasetProcessingThread`** — Subclasses `threading.Thread`, overrides `run()`
- **`ChartGenerationThread`** — Another Thread subclass for concurrent chart generation
- **`queue.Queue`** — Thread-safe communication between worker threads and main thread
- `process_chunks_with_threads()` — Splits DataFrame and processes chunks in parallel
- `generate_charts_concurrently()` — Generates bar, line, and distribution charts simultaneously

### Multiprocessing
- `compute_stats_multiprocess()` — Uses `multiprocessing.Pool` with `spawn` context (safe for Flask)
- Module-level `_compute_column_stats()` — Pickle-safe worker function (lambdas can't be pickled!)
- `parallel_sort_demo()` — Parallel merge sort using process pool + `heapq.merge`

### Data Serialization
- All dataset results saved to `data/datasets.json`
- All user registrations saved to `data/users.json`
- All function logs saved to `data/app_logs.json`
- `SerializableMixin` provides `to_dict()`, `to_json()`, and `from_dict()` on any model class

### Regular Expressions
| Field | Pattern |
|-------|---------|
| Name | `^[A-Za-z][A-Za-z\s\-']{1,49}$` |
| Email | `^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$` |
| Phone | `^(\+?[0-9]{1,3}[\s\-]?)?(\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}$` |
| Password | `^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&\-_#^])[A-Za-z\d@$!%*?&\-_#^]{8,}$` |

### Virtual Environments
- Project uses a `venv` virtual environment (see setup instructions)
- All dependencies pinned in `requirements.txt`

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Registration & upload page |
| `/dashboard` | GET | Analytics dashboard |
| `/api/validate` | POST | Validate form fields (JSON body) |
| `/api/process` | POST | Upload and process a dataset |
| `/api/datasets` | GET | List all processed datasets |
| `/api/users` | GET | List all registered users |
| `/api/logs` | GET | Stream recent function logs |
| `/api/fibonacci` | GET | Fibonacci sequence via generator |
| `/api/live_log` | GET | Live activity log via circular buffer |
| `/api/system_info` | GET | Python/OS info |

---

## Implementation Checklist

- [x] 5+ Python modules (`validation`, `processing`, `threading_tasks`, `multiprocessing_tasks`, `serialization`)
- [x] 2+ decorators (`@log_execution`, `@timer`, `@retry`, `@validate_input`)
- [x] 1+ generators (`statistics_generator`, `fibonacci_generator`, `csv_chunk_generator`, `log_stream_generator`)
- [x] 1+ custom iterators (`DatasetRowIterator`, `CircularBufferIterator`, `RangeStepIterator`)
- [x] 2+ mixin classes (`TimestampMixin`, `SerializableMixin`, `ValidationMixin`, `LoggableMixin`)
- [x] 1+ abstract class (`DataProcessor`)
- [x] Threading (`DatasetProcessingThread`, `ChartGenerationThread`, `queue.Queue`)
- [x] Multiprocessing (`Pool`, `spawn` context, module-level worker)
- [x] Regex validation (name, email, phone, password)
- [x] JSON data storage (datasets, users, logs)
- [x] Operator overloading (`DatasetResult.__add__`)
- [x] Multiple inheritance + MRO
- [x] Modular project structure

---

## Notes

- The `spawn` multiprocessing context is used instead of `fork` to avoid issues with Flask's internal state being copied to child processes
- Chart images are saved to `static/charts/` with timestamp-based filenames to avoid caching conflicts
- The circular buffer iterator automatically drops old entries when capacity (50) is reached
- Passwords are never stored — only name, email, and phone are saved to `users.json`
