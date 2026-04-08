"""
decorators.py - Custom decorators for logging, timing, validation, and retries.

Demonstrates:
- Function decorators with functools.wraps
- Decorator factories (closures over decorator parameters)
- Stacking multiple decorators
- Using wrapper.attribute to store state
"""

import time
import functools
import datetime
import os
import json

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'app_logs.json')


def log_execution(func):
    """Decorator that logs function execution with status."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        log_entry = {
            "function": func.__name__,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "started"
        }
        try:
            result = func(*args, **kwargs)
            log_entry["status"] = "success"
            return result
        except Exception as e:
            log_entry["status"] = "failed"
            log_entry["error"] = str(e)
            raise
        finally:
            _save_log(log_entry)
    return wrapper


def timer(func):
    """Decorator that measures function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = round(end - start, 4)
        wrapper.last_execution_time = elapsed
        print(f"[TIMER] {func.__name__} took {elapsed}s")
        return result
    wrapper.last_execution_time = None
    return wrapper


def retry(max_attempts=3, delay=1.0):
    """
    Decorator factory that retries a function if it fails.
    Demonstrates closure: the decorator closes over max_attempts and delay.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise e
                    time.sleep(delay)
        return wrapper
    return decorator


def validate_input(*param_names):
    """
    Decorator that validates that specified parameters are not None or empty.
    
    Usage:
        @validate_input('name', 'email')
        def process_user(name, email):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature to map args to param names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            for param_name in param_names:
                value = bound_args.arguments.get(param_name)
                if value is None or (isinstance(value, str) and not value.strip()):
                    raise ValueError(f"Parameter '{param_name}' cannot be None or empty")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cache_result(ttl_seconds=60):
    """
    Decorator factory that caches function results for ttl_seconds.
    Demonstrates closure and stateful wrapper.
    """
    def decorator(func):
        cache = {}
        cache_time = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            
            if cache_key in cache_time:
                if now - cache_time[cache_key] < ttl_seconds:
                    return cache[cache_key]
            
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_time[cache_key] = now
            return result
        
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    return decorator


def _save_log(entry):
    """Helper to append a log entry to the JSON log file."""
    logs = []
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
    except Exception:
        logs = []
    logs.append(entry)
    logs = logs[-200:]
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception:
        pass
