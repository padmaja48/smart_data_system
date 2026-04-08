#!/usr/bin/env python
"""
Run Flask app - Production ready with environment variable support.
"""
import os

# Disable bytecode caching
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

if __name__ == '__main__':
    print("[RUN] Starting Flask", flush=True)
    from smart_data_system.app import app
    
    # Get port from environment, default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False, threaded=True)
