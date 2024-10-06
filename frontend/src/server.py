import os
from langserve import RemoteRunnable
from langchain.callbacks.streamlit import StreamlitCallbackHandler
from pydantic import BaseModel
import streamlit as st

llm = RemoteRunnable(os.getenv("API_ENDPOINT"))

class Input(BaseModel):
    input: str

with st.sidebar:
    "Coming Soon"

st.title("Financial Advisor")

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

for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])

if prompt := st.chat_input(placeholder="How many outstanding shares of stock did Microsoft have in their most recent report?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = llm.invoke(Input(input=prompt), {"callbacks": [st_callback]})
        st.session_state["messages"].append({"role": "assistant", "content": response})
        st.write(response["output"])
