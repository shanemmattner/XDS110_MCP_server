"""
LLM Debugging Framework for Embedded Systems

This package provides a complete framework for AI-assisted debugging of embedded systems,
combining Large Language Models with real-time hardware debugging interfaces.
"""

from .debug_interface import GenericDebugInterface, DebugSession, VariableInfo, VariableType, TargetState
from .ti_dss_adapter import TIDSSAdapter
from .llm_agent import LLMDebugAgent, DebugHypothesis, DebugPlan

__version__ = "1.0.0"
__all__ = [
    "GenericDebugInterface",
    "DebugSession", 
    "VariableInfo",
    "VariableType",
    "TargetState",
    "TIDSSAdapter",
    "LLMDebugAgent",
    "DebugHypothesis", 
    "DebugPlan"
]