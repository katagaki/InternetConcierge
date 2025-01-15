from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult


class StreamOutputCallback(BaseCallbackHandler):
    generated_answer: str
    is_generating: bool

    def __init__(self):
        self.generated_answer = ""
        self.is_generating = False

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        self.generated_answer = ""
        self.is_generating = True
        print("\n[STREAM] Starting...\n")

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any
    ) -> Any:
        self.is_generating = False
        self.generated_answer = ""
        print("\n[STREAM] Finished\n")

    async def on_llm_new_token(
        self,
        token: str,
        **kwargs
    ):
        self.generated_answer += token
        print(f"{token}", end="")
