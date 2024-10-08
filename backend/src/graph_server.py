from .tools.get_stock_quote import get_stock_quote
from .tools.get_stock_technical_indicators import get_stock_technical_indicators
from .tools.get_stock_news import get_stock_news
from .tools.get_stock_financials import get_stock_financials
from .tools.get_weather import get_weather
from .prompts import system_prompt

from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from langserve import add_routes

from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional

#Load environment variables from a .env file
load_dotenv()

app = FastAPI(
    title="Gen UI Backend",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

memory = MemorySaver()

class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

tools = [
    get_stock_quote, 
    get_stock_technical_indicators, 
    get_stock_news, 
    get_stock_financials,
    get_weather
]

tool_node = ToolNode(tools)
model = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    api_version="2023-03-15-preview",
    temperature=0,
    streaming=True
)
model_with_tools = model.bind_tools(tools=tools)

def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return END
    return "action"

def call_model(state: MessagesState, config: RunnableConfig):
    messages = filter_messages(state["messages"])
    response = model_with_tools.invoke(state["messages"], config=config)
    return {
        "messages": response
    }

def filter_messages(messages: list):
    return messages[-1:]

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

runnable = workflow.compile(checkpointer=memory).with_types(input_type=ChatInputType, output_type=dict).with_config({"configurable": {"thread_id": "{thread_id}"}})

add_routes(app, runnable, path="/financials", playground_type="chat")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=9500)