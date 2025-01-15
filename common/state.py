from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class ConciergeState(TypedDict):
    messages: Annotated[list, add_messages]
