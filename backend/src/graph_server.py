import os
import uvicorn

from .graph import create_graph

from langserve import APIHandler
from dotenv import load_dotenv
from typing import Annotated, AsyncGenerator

from fastapi import FastAPI, Depends, Request, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette import EventSourceResponse

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.identity import DefaultAzureCredential
from logging import getLogger, INFO

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from fastapi_azure_auth import MultiTenantAzureAuthorizationCodeBearer
from contextlib import asynccontextmanager

#Load environment variables from a .env file and make sure they are refreshed and not cached
load_dotenv(override=True)

logger = getLogger(__name__)

configure_azure_monitor(
    enable_live_metrics=True
)

exporter = AzureMonitorTraceExporter.from_connection_string(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
tracer_provider = TracerProvider(
    resource=Resource.create({SERVICE_NAME: "langchaing-api"})
)
trace_api.set_tracer_provider(tracer_provider)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(exporter, schedule_delay_millis=60000)
trace.get_tracer_provider().add_span_processor(span_processor)
LangChainInstrumentor().instrument()

class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = [os.getenv("CORS_URL")]
    OPENAPI_CLIENT_ID: str = ""
    APP_CLIENT_ID: str = ""

# Check the environment variable
ENVIRONMENT = os.getenv("ENVIRONMENT")

# FastAPI Application
if ENVIRONMENT != "DEVELOPMENT":
    swagger_ui_oauth2_redirect_url = "/oauth2-redirect"
    swagger_ui_init_oauth = {
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': os.getenv("OPENAPI_CLIENT_ID")
    }
else:
    swagger_ui_oauth2_redirect_url = None
    swagger_ui_init_oauth = None


settings = Settings()
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load OpenID config on startup
    """
    await azure_scheme.openid_config.load_config()
    yield

# FastAPI Application
app = FastAPI(
    title="Gen UI Backend",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
    swagger_ui_oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
    swagger_ui_init_oauth=swagger_ui_init_oauth
)

# Instrument the FastAPI application with OpenTelemetry and send the data to Application Insights
FastAPIInstrumentor.instrument_app(app)

# Set up the CORS middleware to allow for cross-origin requests
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

azure_scheme = MultiTenantAzureAuthorizationCodeBearer(
    app_client_id=os.getenv("APP_CLIENT_ID"),
    scopes={
        f"api://{settings.APP_CLIENT_ID}/user_impersonation": "user_impersonation",
    },
    validate_iss=False,
    allow_guest_users=True
)

# Create the credential that will be leveraged to access the Azure Container Apps Session Pools
# If you don't have AZURE_CLIENT_ID, AZURE_TENANT_ID and AZURE_CLIENT_SECRET as environmental variables, run az login and it will use
# your credentials
credential = DefaultAzureCredential()

runnable = create_graph()

async def _get_api_handler() -> APIHandler: 
    return APIHandler(runnable, path="/v2")

# Define dependencies conditionally
dependencies = [Security(azure_scheme)] if ENVIRONMENT != "DEVELOPMENT" else []

# Ability to invoke a signle question
@app.post("/v2/financials/invoke", dependencies=dependencies, include_in_schema=True)
async def v2_invoke(
    request: Request, 
    runnable: Annotated[APIHandler, Depends(_get_api_handler)]
) -> Response:
    """Handle invoke request"""
    return await runnable.invoke(request)

# Ability to invoke a single question and get a stream of responses
@app.post("/v2/financials/stream", dependencies=dependencies, include_in_schema=True)
async def v2_stream(
    request: Request,
    runnable: Annotated[APIHandler, Depends(_get_api_handler)]
) -> EventSourceResponse:
    """Handle stream request"""
    return await runnable.stream(request)


@app.get("/v2/liveness", status_code=200)
def v2_liveness():
    return { "status": "ok"}

# Run the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=os.getenv("PORT"))