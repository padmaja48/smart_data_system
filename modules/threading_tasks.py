"""
threading_tasks.py - Multithreaded dataset processing.

I use threading here for I/O-bound tasks like reading files and generating
charts.  Threading in Python is limited by the GIL for CPU work, but for
I/O it's genuinely faster because threads can overlap waiting time.
"""

import threading
import time
import queue


# shared results dict and a lock to protect it
_results_store = {}
_store_lock = threading.Lock()


class DatasetProcessingThread(threading.Thread):
    """
    A Thread subclass that processes one dataset chunk.
    By subclassing Thread and overriding run(), I can pass extra
    data to the thread without using global variables.
    """

    def __init__(self, thread_id, data_chunk, result_queue):
        super().__init__()
        self.thread_id = thread_id
        self.data_chunk = data_chunk
        self.result_queue = result_queue
        self.daemon = True  # so threads die when main process dies

    def run(self):
        """This is called when thread.start() is invoked."""
        try:
            import numpy as np
            # simulate some I/O wait time (like reading from disk)
            time.sleep(0.05)

            numeric_cols = self.data_chunk.select_dtypes(include=[np.number])
            chunk_stats = {}
            for col in numeric_cols.columns:
                series = numeric_cols[col].dropna()
                if len(series) == 0:
                    continue
                chunk_stats[col] = {
                    "mean": float(series.mean()),
                    "std": float(series.std()),
                    "count": int(series.count())
                }

            self.result_queue.put({
                "thread_id": self.thread_id,
                "stats": chunk_stats,
                "rows": len(self.data_chunk),
                "status": "done"
            })
        except Exception as e:
            self.result_queue.put({
                "thread_id": self.thread_id,
                "status": "error",
                "error": str(e)
            })


def process_chunks_with_threads(dataframe, num_threads=4):
    """
    Split a dataframe into chunks and process each in a separate thread.
    Results are collected via a thread-safe Queue.

    Returns list of per-chunk stats and total time taken.
    """
    import numpy as np

    start_time = time.perf_counter()
    result_queue = queue.Queue()
    threads = []

    # split dataframe into num_threads chunks
    chunk_size = max(1, len(dataframe) // num_threads)
    chunks = [dataframe.iloc[i:i + chunk_size] for i in range(0, len(dataframe), chunk_size)]

    # create and start threads
    for idx, chunk in enumerate(chunks):
        t = DatasetProcessingThread(
            thread_id=idx,
            data_chunk=chunk,
            result_queue=result_queue
        )
        threads.append(t)
        t.start()

    # wait for all threads to finish
    for t in threads:
        t.join(timeout=30)  # don't wait forever

    # collect results from queue
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    elapsed = round(time.perf_counter() - start_time, 4)

    # sort by thread_id so output is predictable
    results.sort(key=lambda x: x.get("thread_id", 0))

    return {
        "thread_results": results,
        "num_threads": len(threads),
        "total_time_seconds": elapsed
    }


class ChartGenerationThread(threading.Thread):
    """Thread to generate a single chart — useful when making multiple charts at once."""

    def __init__(self, chart_func, kwargs, name):
        super().__init__()
        self.chart_func = chart_func
        self.kwargs = kwargs
        self.chart_name = name
        self.result_path = None
        self.error = None
        self.daemon = True

    def run(self):
        try:
            self.result_path = self.chart_func(**self.kwargs)
        except Exception as e:
            self.error = str(e)


def generate_charts_concurrently(chart_tasks):
    """
    Generate multiple charts at the same time using threads.
    chart_tasks: list of dicts with keys 'func', 'kwargs', 'name'
    Returns list of result paths.
    """
    threads = []
    for task in chart_tasks:
        t = ChartGenerationThread(
            chart_func=task['func'],
            kwargs=task['kwargs'],
            name=task['name']
        )
        threads.append(t)
        t.start()

    paths = []
    for t in threads:
        t.join(timeout=60)
        if t.result_path:
            paths.append(t.result_path)

    return paths
