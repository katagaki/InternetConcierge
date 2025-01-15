import json

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from common.llms import llm_gpt_4o_mini
from common.state import ConciergeState

IC_CHAT_NODE_ID: str = "GeneralChat"

# 一般チャット用 Node
class ConciergeChatNode:
    def __init__(self) -> None:
        pass

    def __call__(self, state: ConciergeState):
        return {
            "messages": [
                llm_gpt_4o_mini.invoke(
                    state["messages"]
                )
            ]
        }

# Tool を呼び出す Node
class ConciergeToolNode:
    def __init__(self, tools: list[BaseTool]) -> None:
        self.tools_by_name = {
            tool.name: tool for tool in tools
        }

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input.")
        outputs: list = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                )
            )
        return {
            "messages": outputs
        }
