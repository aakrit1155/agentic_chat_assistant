import os
from typing import Any, Dict, List, Tuple, Union

from article_scraper import scrape_article
from langchain_core.messages import ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

system_msg = """
You are a helpful assistant specialized in assisting users with web content and general questions.

Listen carefully to the user's request.

* **If the user gives you a URL:** Your first step is always to retrieve the content from that URL using your scraping tool. After you have successfully scraped the page (you will see the text prefixed with `SCRAPED TEXT::` in our history), confirm this to the user and ask them what specific task or question they have about *that particular article*.
* **If the user asks a question:** Evaluate if you need to access external information (like a webpage) to answer it. If so, use your scraping tool. Once you have the required information (from scraping or your own knowledge), provide a clear and helpful answer.

**Important:** You will automatically use your tools when needed to gather information. If a tool returns an error message, inform the user about the error and suggest they provide a different URL or question. When a tool succeeds, use its output (especially `SCRAPED TEXT::`) to formulate your response or guide the user further.
"""


def load_llm(api_key: str):
    """
    Load the LLM object to communicate with the Open AI LLM.
    """
    model = ChatGoogleGenerativeAI(
        temperature=0.1, model="gemini-2.0-flash", google_api_key=api_key
    )
    return model


def get_tool_output(messages: List[Any]) -> Union[str, None]:
    """
    Get the tool output from the messages list returned by the agent executor if present else None.

    Parameters
    ----------
    messages : List[Any]
        list of UserMessage, AIMessage, and SystemMessage objects.

    Returns
    -------
    Union[str, None]
        Tool output if present else None.
    """
    return messages[-2].content if isinstance(messages[-2], ToolMessage) else None


def call_agent_executor(
    prompts: Dict[str, List[Dict[str, str]]], executor: Any
) -> Tuple[str, str | None]:
    """
    Call the agent executor with the given prompts.
    """
    response = executor.invoke(prompts)
    tool_output = get_tool_output(response["messages"])
    return response["messages"][-1].content, tool_output


def main_llm_call(
    msgs: List[Dict[str, str]], prompt: Dict[str, str], api_key: str
) -> Tuple[str, str | None]:

    model = load_llm(api_key)
    tools = [scrape_article]
    agent_executor_graph = create_react_agent(model, tools=tools, prompt=system_msg)
    messages = {"messages": msgs[:4] + [prompt]}
    ai_response_text, tool_output = call_agent_executor(messages, agent_executor_graph)
    return ai_response_text, tool_output
