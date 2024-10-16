import os
from .tools.get_stock_quote import get_stock_quote
from .tools.get_stock_technical_indicators import get_stock_technical_indicators
from .tools.get_stock_news import get_stock_news
from .tools.get_stock_financials import get_stock_financials
from .tools.get_weather import get_weather
from .tools.get_options_chain import get_options_chain
from .prompts.system_prompt import SYSTEM_PROMPT

from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_azure_dynamic_sessions import SessionsPythonREPLTool
from langgraph.prebuilt import ToolNode
from langserve import APIHandler
from langchain_core.tools import Tool

from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List, Union, Annotated
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette import EventSourceResponse
import uvicorn

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from azure.identity import DefaultAzureCredential
from logging import getLogger, INFO

logger = getLogger(__name__)

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

# The format of the message that comes in from the client.  
class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

# FastAPI Application
app = FastAPI(
    title="Gen UI Backend",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
)

# Instrument the FastAPI application with OpenTelemetry and send the data to Application Insights
FastAPIInstrumentor.instrument_app(app)

# Set up the CORS middleware to allow for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize the memory save that will be used to save the state of the conversation in memory for a specific thread/user
memory = MemorySaver()

# Create the credential that will be leveraged to access the Azure Container Apps Session Pools
# If you don't have AZURE_CLIENT_ID, AZURE_TENANT_ID and AZURE_CLIENT_SECRET as environmental variables, run az login and it will use
# your credentials
credential = DefaultAzureCredential()

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
    repl
]
tool_node = ToolNode(tools)

# Define the Model that will be used to answer the questions and bind the tools to the model
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

async def _get_api_handerl() -> APIHandler: 
    return APIHandler(runnable, path="/v2")

# Ability to invoke a signle question
@app.post("/v2/financials/invoke")
async def v2_invoke(
    request: Request, 
    runnable: Annotated[APIHandler, Depends(_get_api_handerl)]
) -> Response:
    """Handle invoke request"""
    return await runnable.invoke(request)

# Ability to invoke a single question and get a stream of responses
@app.post("/v2/financials/stream")
async def v2_stream(
    request: Request,
    runnable: Annotated[APIHandler, Depends(_get_api_handerl)]
) -> EventSourceResponse:
    """Handle stream request"""
    return await runnable.stream(request)


# Run the API server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=os.getenv("PORT"))