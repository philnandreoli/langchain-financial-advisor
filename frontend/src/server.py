import os
import base64
import io
from uuid import uuid4
from typing import List, Union
from logging import getLogger, INFO

import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from pydantic import BaseModel
from streamlit_oauth import OAuth2Component
from langchain.callbacks.streamlit import StreamlitCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langserve import RemoteRunnable

from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Load environment variables from a .env file and make sure they are refreshed and not cached
load_dotenv(override=True)

configure_azure_monitor(
    enable_live_metrics=True
)

# Environment variables
AUTHORIZE_ENDPOINT = os.getenv("AUTHORIZE_ENDPOINT")
TOKEN_ENDPOINT = os.getenv("TOKEN_ENDPOINT")
CLIENT_ID = os.getenv("STREMLIT_APP_CLIENT_ID")
CLIENT_SECRET = os.getenv("APP_CLIENT_SECRET")
ICON_URL = os.getenv("ICON_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
API_CLIENT_ID = os.getenv("API_CLIENT_ID")
ENVIRONMENT = os.getenv("ENVIRONMENT")
APP_INSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

# Logger setup
logger = getLogger(__name__)

# Azure Monitor setup
exporter = AzureMonitorTraceExporter.from_connection_string(conn_str=APP_INSIGHTS_CONNECTION_STRING)
tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: "streamlit-chat-app"}))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(exporter, schedule_delay_millis=60000)
trace.get_tracer_provider().add_span_processor(span_processor)
LangChainInstrumentor().instrument()

# OAuth2 setup
oauth2 = OAuth2Component(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authorize_endpoint=AUTHORIZE_ENDPOINT,
    token_endpoint=TOKEN_ENDPOINT
)

class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

@tracer.start_as_current_span(name="streamlit-chat-app-authorize_user")
def authorize_user():
    result = oauth2.authorize_button(
        name="Login with Microsoft Entra",
        icon=ICON_URL,
        redirect_uri=REDIRECT_URI,
        scope=f"api://{API_CLIENT_ID}/user_impersonation",
        pkce="S256"
    )
    if result and "token" in result:
        st.session_state.token = result.get("token")
        st.rerun()
    else:
        token = st.session_state["token"]
        st.json(token)
        if st.button("Refresh Token"):
            token = oauth2.refresh_token(token)
            st.session_state.token = token
            st.rerun()

@tracer.start_as_current_span(name="streamlit-chat-app-setup_llm")
def setup_llm():
    if ENVIRONMENT != "DEVELOPMENT":
        return RemoteRunnable(os.getenv("API_ENDPOINT"), headers={"Authorization": "Bearer " + st.session_state["token"]["access_token"]})
    else:
        return RemoteRunnable(os.getenv("API_ENDPOINT"))

@tracer.start_as_current_span(name="streamlit-chat-app-initialize_session_state")
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": """
                    Hello!! I am your financial advisor. I can help you find information about publicly traded company, like: 
                    * Check the stock price of a publicly traded company
                    * Check the technical indicators (MACD, Stochastics, RSI and ADR) of a publicly traded company
                    * Check any news for a publicly traded company
                    * Check the financials (10-Q/10-K) of a publicly traded company
                    * Based on the two items, give short and long term recommendations of the stock
                    * Check the weather for a city
                """
            }
        ]
        st.session_state["thread_id"] = str(uuid4())

@tracer.start_as_current_span(name="streamlit-chat-app-display_messages")
def display_messages():
    for message in st.session_state["messages"]:
        st.chat_message(message["role"]).write(message["content"])

def handle_user_input(llm):
    if prompt := st.chat_input(placeholder="What is Microsoft's stock price today?"):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            response = llm.invoke(ChatInputType(messages=[HumanMessage(prompt)]), {"configurable": {"thread_id": st.session_state["thread_id"]}})
            process_response(response)

@tracer.start_as_current_span(name="streamlit-chat-app-process_response")
def process_response(response):
    if isinstance(response['messages'][-2], ToolMessage):
        if response['messages'][-2].artifact is not None:
            msg = base64.b64decode(response['messages'][-2].artifact['result']['base64_data'])
            buf = io.BytesIO(msg)
            img = Image.open(buf)
            st.markdown(st.image(image=img, output_format="PNG", caption=None), unsafe_allow_html=True)
        else:
            st.markdown(response["messages"][-1].content)
            st.session_state["messages"].append({"role": "assistant", "content": response["messages"][-1].content})
    else:
        st.markdown(response["messages"][-1].content)
        st.session_state["messages"].append({"role": "assistant", "content": response["messages"][-1].content})

try:
    if "token" not in st.session_state and ENVIRONMENT != "DEVELOPMENT":
        authorize_user()
    else:
        llm = setup_llm()
        with st.sidebar:
            "Coming Soon"
        st.title("Financial Advisor")
        initialize_session_state()
        display_messages()
        handle_user_input(llm)
except KeyError as ke:
    logger.warning(f"Key Error: {ke}")