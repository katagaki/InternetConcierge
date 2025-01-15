from langgraph.graph import END

from common.state import ConciergeState
from common.tools import all_tool_names


def tool_routing(state: ConciergeState):
    if messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError("No messages found in input state.")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        tool_to_be_called: dict = ai_message.tool_calls[0]
        tool_name: str = tool_to_be_called["name"]
        if tool_name in all_tool_names:
            return tool_name

    return END
