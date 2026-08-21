"""IncidentAI: explain operational incidents from logs."""

from .analyzer import analyze_all, analyze_text
from .models import IncidentAnalysis

__all__ = ["IncidentAnalysis", "analyze_all", "analyze_text"]
__version__ = "0.12.1"
