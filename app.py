"""
app.py - Main Flask application entry point.

This file wires together all the modules:
  - validation → checks user input with regex
  - processing → loads and analyses datasets
  - threading_tasks / multiprocessing_tasks → concurrent processing
  - serialization → JSON-based storage
  - decorators → applied to routes for logging + timing
"""

import os
import sys
import json
import datetime

# make sure our modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, render_template, send_from_directory

from modules.validation import FormValidator
from modules.serialization import (
    save_dataset_result, load_all_datasets,
    save_user_submission, load_all_users
)
from modules.processing import (
    get_processor_for_file,
    generate_bar_chart,
    generate_line_chart,
    generate_distribution_chart,
    DatasetResult
)
from modules.threading_tasks import process_chunks_with_threads
from modules.multiprocessing_tasks import compute_stats_multiprocess
from utils.decorators import log_execution, timer

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

LOGS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'app_logs.json')


# ── Helper Functions ───────────────────────────────────────────────────────────

def clean_nan_values(obj):
    """
    Recursively replace NaN and Inf values with None (null) for JSON serialization.
    NaN is not valid JSON, so we need to convert it before returning responses.
    """
    import math
    import numpy as np
    
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/chart_test')
def chart_test():
    """Test page for debugging chart display."""
    return render_template('chart_test.html')


@app.route('/api/validate', methods=['POST'])
def validate_form():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    validator = FormValidator()
    all_valid, results = validator.validate_form(
        name=data.get('name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        password=data.get('password', '')
    )

    user_id = None
    if all_valid:
        # save (without password)
        user_record = save_user_submission(data['name'], data['email'], data['phone'])
        user_id = user_record.get('id')

    return jsonify({
        "all_valid": all_valid,
        "fields": results,
        "user_id": user_id,
    })


@app.route('/api/process', methods=['POST'])
@timer
@log_execution
def process_dataset():
    """
    Upload and process a CSV or JSON dataset.
    Runs processing, generates charts, stores results.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        filename = file.filename
        processor, file_obj = get_processor_for_file(filename, file)
        processor.load(file_obj)
        stats = processor.process()
        df = processor.dataframe
        dataset_name = os.path.splitext(filename)[0]

        # run threading analysis on the dataframe (with error handling)
        thread_results = {"num_threads": 0, "status": "skipped"}
        try:
            thread_results = process_chunks_with_threads(df, num_threads=4)
        except Exception as thread_err:
            thread_results = {"num_threads": 0, "status": f"failed: {str(thread_err)}"}

        # run multiprocessing for deeper stats (with error handling)
        mp_stats = {}
        try:
            mp_stats = compute_stats_multiprocess(df)
        except Exception as mp_err:
            mp_stats = {"status": f"failed: {str(mp_err)}"}

        # generate charts sequentially
        chart_paths = []
        try:
            result_paths = []
            bar_path = generate_bar_chart(stats=stats, dataset_name=dataset_name)
            if bar_path:
                result_paths.append(bar_path)
            
            line_path = generate_line_chart(stats=stats, dataset_name=dataset_name)
            if line_path:
                result_paths.append(line_path)
            
            dist_path = generate_distribution_chart(dataframe=df, dataset_name=dataset_name)
            if dist_path:
                result_paths.append(dist_path)
            
            chart_paths = result_paths
        except Exception:
            chart_paths = []

        # build DatasetResult objects and merge
        result_basic = DatasetResult(name=dataset_name, stats=stats, chart_paths=chart_paths)
        mp_result = DatasetResult(name=f"{dataset_name}_mp", stats=mp_stats)
        merged = result_basic + mp_result

        # save to JSON store with user reference if provided
        user_id = request.form.get('user_id', type=int)
        saved = save_dataset_result(
            dataset_name=merged.name,
            stats={**stats, "multiprocess_stats": mp_stats},
            chart_paths=chart_paths,
            user_id=user_id
        )

        # collect sample rows
        sample_rows = df.head(5).to_dict('records')

        response_data = {
            "success": True,
            "dataset_id": saved.get("id"),
            "name": dataset_name,
            "stats": stats,
            "multiprocess_stats": mp_stats,
            "threading_info": thread_results,
            "charts": chart_paths,
            "sample_rows": sample_rows,
            "merged_name": merged.name,
            "user_id": user_id
        }
        response_data = clean_nan_values(response_data)
        return jsonify(response_data)

    except Exception as e:
        error_msg = str(e)
        return jsonify({"error": error_msg}), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """Return all stored user submissions."""
    users = load_all_users()
    return jsonify({"users": users, "count": len(users)})


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """
    Combine users and datasets data for dashboard display.
    Returns stats and collections needed for the dashboard page.
    """
    users = load_all_users()
    datasets = load_all_datasets()
    
    # calculate stats
    valid_users = len([u for u in users if u.get('status') == 'valid'])
    total_users = len(users)
    
    return jsonify({
        "stats": {
            "total_users": total_users,
            "valid_users": valid_users,
            "total_datasets": len(datasets)
        },
        "users": users,
        "datasets": datasets
    })


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_datasets(user_id):
    """Get datasets for a specific user."""
    users = load_all_users()
    datasets = load_all_datasets()
    
    # find user
    user = next((u for u in users if u.get('id') == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # filter datasets for this user
    user_datasets = [d for d in datasets if d.get('user_id') == user_id]
    
    return jsonify({
        "user": user,
        "datasets": user_datasets,
        "count": len(user_datasets)
    })


@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    """Return all stored dataset records."""
    datasets = load_all_datasets()
    return jsonify({"datasets": datasets, "count": len(datasets)})


@app.route('/static/charts/<path:filename>')
def serve_chart(filename):
    charts_dir = os.path.join(app.static_folder, 'charts')
    return send_from_directory(charts_dir, filename)


@app.route('/api/debug/charts', methods=['GET'])
def debug_charts():
    """
    Debug endpoint to list available chart files on the server.
    Helps track what charts have been generated.
    """
    charts_dir = os.path.join(app.static_folder, 'charts')
    chart_files = []
    
    if os.path.exists(charts_dir):
        chart_files = os.listdir(charts_dir)
    
    return jsonify({
        "total_charts": len(chart_files),
        "charts_dir": charts_dir,
        "charts": chart_files
    })


@app.route('/api/fibonacci', methods=['GET'])
def get_fibonacci():
    """Generate Fibonacci sequence up to n terms (query param: ?count=10)."""
    from utils.generators import fibonacci_generator
    
    count = request.args.get('count', 10, type=int)
    count = max(1, min(count, 100))  # clamp between 1 and 100
    
    fib_gen = fibonacci_generator(count)
    sequence = list(fib_gen)
    
    return jsonify({
        "sequence": sequence,
        "count": len(sequence),
        "description": "Fibonacci sequence generated lazily using generator"
    })


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Stream function execution logs from app_logs.json."""
    from utils.generators import log_stream_generator
    
    if not os.path.exists(LOGS_FILE):
        return jsonify({"logs": [], "count": 0})
    
    logs = list(log_stream_generator(LOGS_FILE))
    return jsonify({
        "logs": logs,
        "count": len(logs)
    })


@app.route('/api/live_log', methods=['GET'])
def get_live_log():
    """
    Get a circular buffer of recent user activity.
    Uses CircularBufferIterator from utils.iterators.
    """
    from utils.iterators import CircularBufferIterator
    
    users = load_all_users()
    datasets = load_all_datasets()
    
    # Create a circular buffer of recent activities
    activities = CircularBufferIterator(capacity=20)
    
    for user in users[-10:]:  # Last 10 users
        activities.append({
            "type": "user_registration",
            "name": user.get('name'),
            "email": user.get('email'),
            "timestamp": user.get('submitted_at')
        })
    
    for dataset in datasets[-10:]:  # Last 10 datasets
        activities.append({
            "type": "dataset_processed",
            "name": dataset.get('name'),
            "timestamp": dataset.get('processed_at')
        })
    
    return jsonify({
        "activities": list(activities),
        "buffer_size": len(activities),
        "capacity": activities.capacity,
        "description": "Recent activities using CircularBufferIterator"
    })


@app.route('/api/system_info', methods=['GET'])
def get_system_info():
    """Return Python and OS information."""
    import platform
    
    return jsonify({
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "os_name": os.name,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro
        }
    })


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('static/charts', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
