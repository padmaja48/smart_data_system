#!/usr/bin/env python
"""
Run Flask app WITHOUT the debugger reloader (which causes issues with multiprocessing)
"""

from app import app

if __name__ == '__main__':
    # Run WITHOUT use_reloader to prevent watchdog issues with Flask + multiprocessing
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
