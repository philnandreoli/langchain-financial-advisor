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

llm = RemoteRunnable(os.getenv("API_ENDPOINT"))

class ChatInputType(BaseModel):
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]]

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
                st.write(response["messages"][-1].content)
                st.session_state["messages"].append({"role": "assistant", "content": response["messages"][-1].content})
        else:
            st.write(response["messages"][-1].content)
            st.session_state["messages"].append({"role": "assistant", "content": response["messages"][-1].content})
