# gui/worker.py

import sys
import traceback
from PySide6.QtCore import QObject, Signal, QRunnable

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    - finished: No data
    - error:    tuple (exctype, value, traceback.format_exc())
    - result:   object data returned from processing, anything
    - progress: object (typically a tuple of (status, message))
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(object)

class Worker(QRunnable):
    """
    Generic Worker thread.
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the progress callback to our kwargs to pass to the function
        self.kwargs['progress_callback'] = self.signals.progress.emit

    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()