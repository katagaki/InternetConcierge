from dotenv import load_dotenv
from langchain_core.runnables import Runnable
from langchain_openai import AzureChatOpenAI

from common.callbacks import StreamOutputCallback
from common.tools import all_tools

load_dotenv()

is_verbose: bool = False

def llm(azure_deployment: str, temperature: float | None = None):
    llm: Runnable = AzureChatOpenAI(
        azure_deployment=azure_deployment,
        temperature=temperature,
        callbacks=[StreamOutputCallback()],
        streaming=True,
        verbose=is_verbose
    )
    llm = llm.bind_tools(all_tools)
    return llm

llm_o1 = llm("o1")
llm_gpt_4o = llm("gpt-4o", 0.9)
llm_gpt_4o_mini = llm("gpt-4o-mini", 0.9)
