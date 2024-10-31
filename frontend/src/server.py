import os
from uuid import uuid4
from langserve import RemoteRunnable
from langchain.callbacks.streamlit import StreamlitCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from pydantic import BaseModel
import streamlit as st
from typing import List, Union
import json
import base64
from PIL import Image
import io
from dotenv import load_dotenv
from streamlit_oauth import OAuth2Component

#Load environment variables from a .env file and make sure they are refreshed and not cached
load_dotenv(override=True)

AUTHORIZE_ENDPOINT=os.getenv("AUTHORIZE_ENDPOINT")
TOKEN_ENDPOINT=os.getenv("TOKEN_ENDPOINT")
CLIENT_ID=os.getenv("STREMLIT_APP_CLIENT_ID")
CLIENT_SECRET=os.getenv("APP_CLIENT_SECRET")
ICON_URL=os.getenv("ICON_URL")
REDIRECT_URI=os.getenv("REDIRECT_URI")
API_CLIENT_ID=os.getenv("API_CLIENT_ID")
ENVIRONMENT=os.getenv("ENVIRONMENT")

class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

oauth2 = OAuth2Component(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, authorize_endpoint=AUTHORIZE_ENDPOINT, token_endpoint=TOKEN_ENDPOINT)

try:
    if "token" not in st.session_state and ENVIRONMENT != "DEVELOPMENT":
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
    else:
        if ENVIRONMENT != "DEVELOPMENT":
            llm = RemoteRunnable(os.getenv("API_ENDPOINT"), headers={"Authorization": "Bearer " + st.session_state["token"]["access_token"]})
        else:
            llm = RemoteRunnable(os.getenv("API_ENDPOINT"))
        
        with st.sidebar:
            "Coming Soon"

        st.title("Financial Advisor")
        conversation_history = []

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

        for message in st.session_state["messages"]:
            st.chat_message(message["role"]).write(message["content"])

        if prompt := st.chat_input(placeholder="How many outstanding shares of stock did Microsoft have in their most recent report?"):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            #st.markdown(st.image(base64.b64decode(IMAGE), output_format="PNG"), unsafe_allow_html=True)

            with st.chat_message("assistant"):
                #st_callback = StreamlitCallbackHandler(st.container())
                #response = llm.invoke(ChatInputType(messages=[HumanMessage(prompt)]), {"callbacks": [st_callback], "configurable": {"thread_id":  st.session_state["thread_id"]}})
                response = llm.invoke(ChatInputType(messages=[HumanMessage(prompt)]), {"configurable": {"thread_id":  st.session_state["thread_id"]}})
                
                if isinstance(response['messages'][len(response['messages'])-2], ToolMessage):
                    if response['messages'][len(response['messages'])-2].artifact is not None:
                        msg = base64.b64decode(response['messages'][len(response['messages'])-2].artifact['result']['base64_data'])
                        buf = io.BytesIO(msg)
                        img = Image.open(buf)
                
                        st.markdown(st.image(image=img, output_format="PNG", caption=None), unsafe_allow_html=True)
                    else:
                        st.markdown(response["messages"][-1].content)
                        st.session_state["messages"].append({"role": "assistant", "content": response["messages"][-1].content})
                else:
                    st.markdown(response["messages"][-1].content)
                    st.session_state["messages"].append({"role": "assistant", "content": response["messages"][-1].content})
except KeyError as ke:
    print(f"Key Error: {ke}")