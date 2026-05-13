"""Signal Layer — T006 Data & Signal infrastructure.

Provides unified trace linkage across all pipeline stages:
  InteractionTrace  — full execution record (query → candidates → sim → review → samples)
  TraceStore        — in-memory trace persistence
  DataSignalLayer   — thin wrapper enforcing trace_id on all outputs
"""

from backend.signal_layer.schemas import InteractionTrace
from backend.signal_layer.trace_store import TraceStore
from backend.signal_layer.data_signal_layer import DataSignalLayer

__all__ = [
    "DataSignalLayer",
    "InteractionTrace",
    "TraceStore",
]
