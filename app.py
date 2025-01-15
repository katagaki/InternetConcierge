import os
import traceback
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import StateSnapshot
from langgraph.utils.config import RunnableConfig

from common.constants import NDTL_GOOGLE_SEARCH, NDTL_WEB_BROWSER
from common.memory import memory
from common.nodes import IC_CHAT_NODE_ID, ConciergeChatNode
from common.routes import tool_routing
from common.state import ConciergeState
from common.tools import all_tools_dict

load_dotenv()

# Graph をビルドするために、フローを定義
graph_builder: StateGraph = StateGraph(ConciergeState)
graph_builder.add_node(IC_CHAT_NODE_ID, ConciergeChatNode())
for tool_name, tool in all_tools_dict.items():
    graph_builder.add_node(tool_name, ToolNode(tools=[tool]))

# はじめにチャットに遷移
graph_builder.add_edge(START, IC_CHAT_NODE_ID)

# チャットから Tool を呼び出す場合の条件分岐
graph_builder.add_conditional_edges(
    source=IC_CHAT_NODE_ID,
    path=tool_routing,
    path_map={
        **{
            tool_name: tool_name for tool_name in all_tools_dict.keys()
        },
        END: END
    }
)

# ツールからチャットに戻る遷移
for tool_name in all_tools_dict.keys():
    graph_builder.add_edge(tool_name, IC_CHAT_NODE_ID)

# Google 検索したページの内容を取得する場合の条件分岐
graph_builder.add_conditional_edges(
    source=NDTL_GOOGLE_SEARCH,
    path=tool_routing,
    path_map={
        NDTL_WEB_BROWSER: NDTL_WEB_BROWSER,
        END: END
    }
)

# Graph をビルド
graph: CompiledStateGraph = graph_builder.compile(
    checkpointer=memory,
    interrupt_before=[NDTL_GOOGLE_SEARCH]
)

# Graph の画像を出力
try:
    graph_image: bytes = graph.get_graph().draw_mermaid_png()
    os.makedirs("./output", exist_ok=True)
    with open("./output/graph.png", "wb") as graph_image_file:
        graph_image_file.write(graph_image)
except Exception:
    pass

if __name__ == "__main__":
    thread_id: str = str(uuid4())

    system_message: str = """
You are an Internet concierge.
You have various tools at your disposal to scour the web for the information the user seeks.
Where necessary, dive into webpages and obtain additional content to improve the accuracy of your answer.
Remember: Your goal is to be helpful and informative. If you are unsure, ask for clarification, or provide a general response.
""".strip()

    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    is_first_run: bool = True
    while True:
        try:
            snapshot: StateSnapshot = graph.get_state(config)
            if snapshot.next:
                if snapshot.values:
                    last_message: AIMessage = snapshot.values["messages"][-1]
                    tool_call: ToolCall = last_message.tool_calls[0]
                    tool_name: str = tool_call["name"]

                    if tool_name == NDTL_GOOGLE_SEARCH:
                        is_valid_response_received: bool = False
                        while not is_valid_response_received:
                            user_input = input(f"Search Google for '{tool_call['args']['query']}'? [Y/N] ")
                            if user_input.lower() == "y":
                                for event in graph.stream(None, config, stream_mode="values"):
                                    pass
                                is_valid_response_received = True
                            elif user_input.lower() == "n":
                                graph.update_state(
                                    config,
                                    {
                                        "messages": [
                                            ToolMessage(
                                                content="Search cancelled.",
                                                tool_call_id=last_message.tool_calls[0]["id"]
                                            ),
                                            AIMessage(
                                                content="Search cancelled."
                                            )
                                        ]
                                    },
                                    as_node=IC_CHAT_NODE_ID
                                )
                                print("Search cancelled.")
                                is_valid_response_received = True
                    else:
                        for event in graph.stream(None, config, stream_mode="values"):
                            pass
            else:
                user_input = input("Message: ")
                if user_input.lower() == "exit":
                    print("Goodbye!")
                    break

                for event in graph.stream(
                    {
                        "messages": [
                            ("system", system_message),
                            ("user", user_input)
                        ] if is_first_run else [
                            ("user", user_input)
                        ]
                    },
                    config,
                    stream_mode="values"
                ):
                    pass
                    # print(event["messages"][-1].pretty_print())

            is_first_run = False
        except Exception as e:
            print(f"!!! Error: {e}\nStack trace:\n{traceback.format_exc()}")
            break
