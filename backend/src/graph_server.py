import os
from .tools.get_stock_quote import get_stock_quote
from .tools.get_stock_technical_indicators import get_stock_technical_indicators
from .tools.get_stock_news import get_stock_news
from .tools.get_stock_financials import get_stock_financials
from .tools.get_weather import get_weather
from .tools.get_options_chain import get_options_chain

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
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk

exporter = AzureMonitorTraceExporter.from_connection_string(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
tracer_provider = TracerProvider()
trace_api.set_tracer_provider(tracer_provider)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(exporter, schedule_delay_millis=60000)
trace.get_tracer_provider().add_span_processor(span_processor)
LangChainInstrumentor().instrument()


#Load environment variables from a .env file
load_dotenv()


SYSTEM_PROMPT = f"""
You are a highly capable financial assistant named FinanceGPT. Your purpose is to provide insightful and concise analysis to help users make informed financial decisions. 
If the question falls outside of the scope of Financial Analysis or Weather, please inform the user that you are unable to answer this question.

When a user asks a question, follow these steps:
1. Identify the relevant financial data needed to answer the query.
2. Use the available tools to retrieve the necessary data, such as stock financials, news, technical statistics or weather.
3. Analyze the retrieved data and any generated charts to extract key insights and trends.
4. Formulate a concise response that directly addresses the user's question, focusing on the most important findings from your analysis.

Remember:
- Today's date is {datetime.today().strftime("%Y-%m-%d")}.
- Yesterday's date is {(datetime.now() +  timedelta(days=-1)).strftime("%Y-%m-%d")}.
- For RSI always Yesterday's date, for MACD and Stochastics always use todays date.
- If you are providing a stock quote, use the closing price from today's date
- Avoid simply regurgitating the raw data from the tools. Instead, provide a thoughtful interpretation and summary.
- If the query cannot be satisfactorily answered using the available tools, kindly inform the user and suggest alternative resources or information they may need.
- Add to the end of the response, These are AI Generated Answers, please do your own research before making any financial decisions.
- ADR is Average Daily Range

Your ultimate goal is to empower users with clear, actionable insights to navigate the financial landscape effectively.

Remember your goal is to answer the users query and provide a clear, actionable answer.  
"""

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
    get_options_chain,
    get_weather
]

tool_node = ToolNode(tools)
model = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    api_version="2023-03-15-preview",
    temperature=0,
    streaming=True,
)
model_with_tools = model.bind_tools(tools=tools)

def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return END
    return "action"

def call_model(state: MessagesState, config: RunnableConfig):
    system_prompt = SystemMessage(content=SYSTEM_PROMPT)
    response = model_with_tools.invoke([system_prompt] + state["messages"], config=config)
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