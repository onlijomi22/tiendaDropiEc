"""BaseAgent: Foundation for all Gemini ReAct agents.

Implements the ReAct (Reason + Act) pattern:
  1. THOUGHT: Agent reasons about the current state
  2. ACTION: Agent selects and calls a tool
  3. OBSERVATION: Agent processes tool output
  4. REPEAT: Until goal is achieved or max_iterations reached

All domain agents inherit this class and define:
  - system_prompt (str): Domain-specific agent instructions
  - tools (dict[str, Callable]): Available tools for this agent
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.shared.logger import get_agent_logger
from src.shared.exceptions import AgentExecutionError


class BaseAgent(ABC):
    """Abstract base for all TiendaDropiEc AI agents.

    Subclasses must define:
        - system_prompt (str): Instructions for this agent's domain
        - tools (dict): Mapping of tool_name -> callable

    The ReAct loop handles:
        - Tool call parsing and dispatch
        - Max iteration safety limit
        - Structured logging of each step
        - Error handling and agent-specific exceptions

    Args:
        max_iterations: Safety limit for the ReAct loop (default: 10)
    """

    _MAX_ITERATIONS: int = 10

    def __init__(self, max_iterations: int = 10) -> None:
        self.max_iterations = min(max_iterations, self._MAX_ITERATIONS)
        self._log = get_agent_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Domain-specific system prompt for this agent."""

    @property
    @abstractmethod
    def agent_tools(self) -> dict[str, Callable[..., Any]]:
        """Available tools: name -> callable mapping.

        Each callable should accept keyword arguments and return
        a JSON-serializable result.
        """

    async def run(self, task: str) -> str:
        """Execute the ReAct loop for a given task.

        This is the main entry point for any agent. The loop:
          1. Sends the task to Gemini with available tools
          2. If Gemini calls a tool -> executes it -> feeds result back
          3. If Gemini returns text -> that is the final response
          4. Stops after max_iterations for safety

        Args:
            task: Natural language task description.

        Returns:
            Agent's final text response.

        Raises:
            AgentExecutionError: If loop fails or exceeds max iterations.
        """
        self._log.info(f"Starting ReAct loop | task: {task[:100]}")

        adapter = GeminiAdapter()
        tool_callables = list(self.agent_tools.values())

        tools = None
        if tool_callables:
            tools = adapter.build_function_tool(tool_callables)

        chat = adapter.create_chat(
            tools=tools,
            system_instruction=self.system_prompt,
        )

        iteration = 0

        try:
            response = await chat.send(f"Tarea: {task}")

            while iteration < self.max_iterations:
                iteration += 1
                self._log.debug(f"ReAct iteration {iteration}/{self.max_iterations}")

                if response.has_tool_call:
                    tool_name, tool_args = response.tool_call

                    self._log.info(f"[ACTION] Calling tool: {tool_name}({tool_args})")
                    observation = await self._dispatch_tool(tool_name, tool_args)
                    self._log.info(f"[OBSERVATION] {str(observation)[:200]}")

                    response = await chat.send(
                        f"[Tool '{tool_name}' result]: {observation}"
                    )
                    continue

                # No tool call -> final text response
                final_response = response.text
                if final_response:
                    self._log.info(f"ReAct complete after {iteration} iterations")
                    return final_response

                raise AgentExecutionError(
                    self.__class__.__name__,
                    "Empty response from Gemini (no text and no tool call)"
                )

            raise AgentExecutionError(
                self.__class__.__name__,
                f"Exceeded max iterations ({self.max_iterations}) without final response"
            )

        except AgentExecutionError:
            raise
        except Exception as e:
            raise AgentExecutionError(self.__class__.__name__, str(e)) from e

    async def _dispatch_tool(
        self, tool_name: str, args: dict[str, Any]
    ) -> Any:
        """Dispatch a tool call to the appropriate callable.

        Args:
            tool_name: Name of the tool to call.
            args: Keyword arguments for the tool.

        Returns:
            Tool result (any JSON-serializable type).

        Raises:
            AgentExecutionError: If tool is not found or call fails.
        """
        tool_fn = self.agent_tools.get(tool_name)
        if not tool_fn:
            # Fallback: check if the model used the function's internal __name__
            for k, v in self.agent_tools.items():
                if getattr(v, '__name__', '') == tool_name or getattr(v, '__name__', '').endswith(tool_name):
                    tool_fn = v
                    break

        if not tool_fn:
            raise AgentExecutionError(
                self.__class__.__name__,
                f"Unknown tool: '{tool_name}'. Available: {list(self.agent_tools.keys())}"
            )
        try:
            import asyncio
            if asyncio.iscoroutinefunction(tool_fn):
                return await tool_fn(**args)
            return tool_fn(**args)
        except Exception as e:
            self._log.error(f"Tool '{tool_name}' failed: {e}")
            return f"ERROR: {e}"
