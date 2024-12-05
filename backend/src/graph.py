import os
from langgraph.graph import MessagesState
from typing import Literal, List, Union
from typing_extensions import TypedDict
from langchain_openai import AzureChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph

from .tools.finances.get_stock_quote import get_stock_quote
from .tools.finances.get_stock_technical_indicators import get_stock_technical_indicators
from .tools.finances.get_stock_news import get_stock_news
from .tools.finances.get_stock_financials import get_stock_financials
from .tools.meteorologist.get_weather import get_weather
from .tools.meteorologist.get_weather_forecast import get_weather_forecast
from .tools.finances.get_options_chain import get_options_chain
from .tools.code.python_repl_tool import python_repl_tool
from pydantic import BaseModel
from .prompts.system_prompt import SYSTEM_PROMPT
class AgentState(MessagesState):
    # The 'next' field indicates where to rout to next
    next: str

class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

members = ["financialadvisor", "coder", "meteorologist"]

options = members + ["FINISH"]

system_prompt = (
    "  You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]

llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_MODEL"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        temperature=0,
        #streaming=True,
        max_retries=3
    )

def supervisor_node(state: AgentState) -> AgentState:
    messages = [
        {
            "role": "system", "content":  system_prompt
        }
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    next_ = response["next"]
    if next_ == "FINISH":
        next_ = END

    return {"next": next_}

# Financial Advisor Agent who can only answer financial questions
financialadvisor_agent = create_react_agent(llm, tools=[get_stock_quote, get_stock_technical_indicators, get_stock_news, get_stock_financials, get_options_chain], state_modifier=SYSTEM_PROMPT)
def financialadvisor_node(state: AgentState) -> AgentState:
    result = financialadvisor_agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name="financialadvisor")
        ]
    }

# Code Agent who can run and execute python code
code_agent = create_react_agent(llm, tools=[python_repl_tool])
def code_node(state: AgentState) -> AgentState:
    result = code_agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name="coder")
        ]
    }

# Meteorologist Agent who can only answer weather questions
meteorologist_agent = create_react_agent(llm, tools=[get_weather, get_weather_forecast], state_modifier="You are a meteorologist. You can answer question about the weather for given a location.  All temperatures are in Farenheit.")
def meteorologist_node(state: AgentState) -> AgentState:
    result = meteorologist_agent.invoke(state)
    return {
        "messages": [
            HumanMessage(content=result["messages"][-1].content, name="meteorologist")
        ]
    }


def create_graph() -> CompiledGraph:
    # Initialize the memory save that will be used to save the state of the conversation in memory for a specific thread/user
    memory = MemorySaver()
    
    workflow = StateGraph(AgentState)
    workflow.add_edge(START, "supervisor")
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("financialadvisor", financialadvisor_node)
    workflow.add_node("coder", code_node)
    workflow.add_node("meteorologist", meteorologist_node)

    for member in members:
        workflow.add_edge(member, "supervisor")
    
    workflow.add_conditional_edges("supervisor", lambda state: state["next"])
    workflow.add_edge(START, "supervisor")

    graph = workflow.compile(checkpointer=memory).with_types(input_type=ChatInputType, output_type=dict).with_config({"configurable": {"thread_id": "{thread_id}"}})
    return graph
