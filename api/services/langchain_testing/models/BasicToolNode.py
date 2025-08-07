import json
from langchain_core.messages import ToolMessage
from api.services.langchain.models.state import State  # Adjust import to your actual `State` class


class BasicToolNode:
    """A node that invokes tools based on the last AI message's tool_calls."""

    def __init__(self, tools: list):
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs):
        # Handle dict or State object
        if isinstance(inputs, dict):
            messages = inputs.get("messages")
        else:
            messages = getattr(inputs, "messages", None)

        if not messages:
            raise ValueError("No messages found in inputs.")

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        outputs = []

        print(f"DEBUG: BasicToolNode received message with {len(tool_calls)} tool calls")

        for tool_call in tool_calls:
            if hasattr(tool_call, "name"):
                tool_name = tool_call.name
                tool_args = tool_call.args
                tool_call_id = getattr(tool_call, "id", None)
            elif isinstance(tool_call, dict):
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id")
            else:
                continue

            print(f"DEBUG: Processing tool call: {tool_name} with args: {tool_args}")

            tool = self.tools_by_name.get(tool_name)
            if not tool:
                print(f"DEBUG: Tool '{tool_name}' not found.")
                continue

            result = tool.invoke(tool_args)
            print(f"DEBUG: Tool result: {result}")

            outputs.append(
                ToolMessage(
                    content=str(result),
                    name=tool_name,
                    tool_call_id=tool_call_id,
                )
            )

        print(f"DEBUG: BasicToolNode returning {len(outputs)} tool messages")

        # Always return a State instance
        return State(messages=messages + outputs)
