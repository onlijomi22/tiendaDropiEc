"""Agents layer: Gemini-powered AI agents with ReAct loop pattern.

All agents inherit BaseAgent and implement:
- tools: list of callable tools the agent can invoke
- system_prompt: domain-specific instructions
- run(): the main entry point for one agent execution cycle
"""
