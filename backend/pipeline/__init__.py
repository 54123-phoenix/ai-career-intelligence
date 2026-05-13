"""Pipeline orchestration — the T005 multi-agent closed-loop system.

Modules:
  modes.py         — ExecutionMode, ExecutionPlan, PipelineContext types
  cache.py         — TTL-based RetrievalCache for fast mode
  architect.py     — ArchitectAgent: determines execution mode + plan
  orchestrator.py  — PipelineOrchestrator: wires all 6 agents together
  config.py        — PipelineConfig: tunable parameters
"""

from backend.pipeline.modes import ExecutionMode, ExecutionPlan, PipelineContext
from backend.pipeline.cache import RetrievalCache
from backend.pipeline.config import PipelineConfig, config as default_config
from backend.pipeline.modes import ExecutionMode, ExecutionPlan, PipelineContext
from backend.pipeline.architect import ArchitectAgent
from backend.pipeline.orchestrator import PipelineOrchestrator

__all__ = [
    "ArchitectAgent",
    "ExecutionMode",
    "ExecutionPlan",
    "PipelineConfig",
    "PipelineContext",
    "PipelineOrchestrator",
    "RetrievalCache",
    "default_config",
]
