"""LLM-backed agents. Each wraps agent_framework.Agent with narrow
instructions and a specific skill toolset - agents decide *when* to call a
skill; skills do the deterministic math (see docs/ARCHITECTURE.md section 4).
"""
