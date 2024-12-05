import os
from .tools.finances.get_stock_quote import get_stock_quote
from .tools.finances.get_stock_technical_indicators import get_stock_technical_indicators
from .tools.finances.get_stock_news import get_stock_news
from .tools.finances.get_stock_financials import get_stock_financials
from .tools.meteorologist.get_weather import get_weather
from .tools.meteorologist.get_weather_forecast import get_weather_forecast
from .tools.finances.get_options_chain import get_options_chain
from .prompts.system_prompt import SYSTEM_PROMPT

from langchain_azure_dynamic_sessions import SessionsPythonREPLTool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, RemoveMessage, trim_messages
from langchain_openai import AzureChatOpenAI

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import ToolNode

from typing import List, Union

from pydantic import BaseModel

# The format of the message that comes in from the client.  
class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return END
    return "action"

def get_tools() -> list:
     # Code Interpreter Tool that will be used to run python code in the context of the conversation
    repl = SessionsPythonREPLTool(
        pool_management_endpoint=os.getenv("POOL_MANAGEMENT_ENDPOINT"),
        description="A python shell that is used for running python code.   It can be used to chart technical statistics that are returned from the get_stock_technical_indicators tool."
    )
    # The tools that will be used to answer questions as part of the conversation
    tools = [
        get_stock_quote, 
        get_stock_technical_indicators, 
        get_stock_news, 
        get_stock_financials,
        get_options_chain,
        get_weather,
        get_weather_forecast,
        repl
    ]
    return tools

def call_model(state: MessagesState, config: RunnableConfig):
    model = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_MODEL"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        temperature=0,
        #streaming=True,
        max_retries=3
    )
    model_with_tools = model.bind_tools(tools=get_tools())
    system_prompt = SystemMessage(content=SYSTEM_PROMPT)

    #messages = trim_messages(state["messages"], strategy="last", token_counter=len, max_tokens=15, start_on="human", end_on=("human", "tool"), include_system=True)

    response = model_with_tools.invoke([system_prompt] + state["messages"], config=config)

    return { "messages": response }

def filter_messages(messages: list):
    return messages[-1:]

def create_graph() -> CompiledGraph:
    # Initialize the memory save that will be used to save the state of the conversation in memory for a specific thread/user
    memory = MemorySaver()
    tool_node = ToolNode(get_tools())
    workflow = StateGraph(MessagesState)

    workflow.add_node("agent", call_model)
    workflow.add_node("action", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        ["action", END]
    )
    
    workflow.add_edge("action", "agent")

    graph = workflow.compile(checkpointer=memory).with_types(input_type=ChatInputType, output_type=dict).with_config({"configurable": {"thread_id": "{thread_id}"}})
    return graph