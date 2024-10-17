import os
import uvicorn

from langserve import APIHandler

from dotenv import load_dotenv
from typing import Annotated

from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette import EventSourceResponse

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from azure.identity import DefaultAzureCredential
from logging import getLogger, INFO
from .graph import create_graph

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

# Create the credential that will be leveraged to access the Azure Container Apps Session Pools
# If you don't have AZURE_CLIENT_ID, AZURE_TENANT_ID and AZURE_CLIENT_SECRET as environmental variables, run az login and it will use
# your credentials
credential = DefaultAzureCredential()

runnable = create_graph()

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