"""
serialization.py - JSON-based data storage and retrieval.
"""

import json
import os
import datetime
from utils.decorators import log_execution, timer

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DATASET_FILE = os.path.join(DATA_DIR, 'datasets.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


@log_execution
@timer
def save_dataset_result(dataset_name: str, stats: dict, chart_paths: list, user_id=None):
    """Save processed dataset stats and chart paths."""
    _ensure_dir()
    records = load_all_datasets()

    record = {
        "id": len(records) + 1,
        "name": dataset_name,
        "user_id": user_id,
        "stats": stats,
        "charts": chart_paths,
        "processed_at": datetime.datetime.now().isoformat()
    }
    records.append(record)

    with open(DATASET_FILE, 'w') as f:
        json.dump(records, f, indent=2, default=str)

    return record


def load_all_datasets():
    """Load all stored dataset results."""
    _ensure_dir()
    if not os.path.exists(DATASET_FILE):
        return []
    try:
        with open(DATASET_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_dataset_by_id(dataset_id: int):
    """Fetch a single dataset record by ID."""
    records = load_all_datasets()
    for r in records:
        if r.get("id") == dataset_id:
            return r
    return None


@log_execution
def save_user_submission(name, email, phone):
    """Save a validated user form submission."""
    _ensure_dir()
    users = load_all_users()

    entry = {
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "phone": phone,
        "status": "valid",
        "submitted_at": datetime.datetime.now().isoformat()
    }
    users.append(entry)

    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

    return entry


def load_all_users():
    """Load all stored user submissions."""
    _ensure_dir()
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def clear_all_data():
    """Clear all stored data."""
    for f in [DATASET_FILE, USERS_FILE]:
        if os.path.exists(f):
            os.remove(f)
