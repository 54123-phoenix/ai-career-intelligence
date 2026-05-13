"""Shared module-level singletons for career route sub-files.

All 4 sub-route files import from here. One-way dependency — no circular imports.
"""

from backend.career.career_parser import CareerParser
from backend.career.career_retriever import CareerRetriever
from backend.career.career_reviewer import CareerReviewer
from backend.career.career_architect import CareerArchitect
from backend.career.career_simulator import CareerSimulator
from backend.career.career_frontend import CareerFrontend
from backend.career.t010_pipeline import T010Pipeline

_parser = CareerParser()
_retriever = CareerRetriever()
_reviewer = CareerReviewer()
_architect = CareerArchitect()
_simulator = CareerSimulator()
_frontend = CareerFrontend()
_t010 = T010Pipeline()
