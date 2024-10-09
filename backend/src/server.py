import os
from dotenv import load_dotenv
from .tools.get_stock_quote import get_stock_quote
from .tools.get_stock_technical_indicators import get_stock_technical_indicators
from .tools.get_stock_news import get_stock_news
from .tools.get_stock_financials import get_stock_financials
from .tools.get_weather import get_weather
from .prompts import system_prompt
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate,PromptTemplate
from langchain_openai.chat_models import AzureChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from pydantic import BaseModel
from typing import Any, List, Union, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes


#Load environment variables from a .env file
load_dotenv()


# Initialize FastAPI app
app = FastAPI(
    title="LangChain Server",
    version="0.1.0",
    description="Spin up a simple api server using LangChain's Runnable interfaces",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Define the tools that the agent can use
tools = [
    get_stock_quote, 
    get_stock_technical_indicators, 
    get_stock_news, 
    get_stock_financials,
    get_weather
]

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=system_prompt.SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template="{input}")),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ]
)

model = AzureChatOpenAI(
    azure_deployment="gpt-4o",
    api_version="2023-03-15-preview",
    temperature=0,
    streaming=True
)

model_with_tools = model.bind_tools(tools=tools)

agent = create_tool_calling_agent(llm=model, tools=tools, prompt=prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)


class Input(BaseModel):
    input: str
    chat_history:List[Union[HumanMessage, AIMessage, SystemMessage]]


class Output(BaseModel):
    output: Any

add_routes(
    app,
    agent_executor.with_types(input_type=Input, output_type=Output).with_config({"run_name": "agent"}),
    path="/financials"
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=9500)