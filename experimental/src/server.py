import os
import asyncio
from openai import AsyncAzureOpenAI

import chainlit as cl
from uuid import uuid4
from chainlit.logger import logger

from realtime import RealtimeClient
from realtime.tools import tools 
from dotenv import load_dotenv
from datetime import datetime, timedelta

from azure.monitor.opentelemetry import configure_azure_monitor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry import trace
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

load_dotenv(override=True)

client = AsyncAzureOpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"],
                          azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                          azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
                          api_version="2024-10-01-preview")    

configure_azure_monitor(
    enable_live_metrics=False
)

exporter = AzureMonitorTraceExporter.from_connection_string(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
tracer_provider = TracerProvider(
    resource=Resource.create({SERVICE_NAME: "chainlit-openai-realtimeapi"})
)
trace_api.set_tracer_provider(tracer_provider)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(exporter, schedule_delay_millis=60000)
trace.get_tracer_provider().add_span_processor(span_processor)


async def setup_openai_realtime(system_prompt: str):
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient(system_prompt = system_prompt)
    cl.user_session.set("track_id", str(uuid4()))
    
    async def handle_conversation_updated(event):
        item = event.get("item")
        delta = event.get("delta")
        """Currently used to stream audio back to the client."""
        if delta:
            # Only one of the following will be populated for any given event
            if 'audio' in delta:
                audio = delta['audio']  # Int16Array, audio added
                await cl.context.emitter.send_audio_chunk(cl.OutputAudioChunk(mimeType="pcm16", data=audio, track=cl.user_session.get("track_id")))
                
            if 'arguments' in delta:
                arguments = delta['arguments']  # string, function arguments added
                pass
            
    async def handle_item_completed(item):
        """Generate the transcript once an item is completed and populate the chat context."""
        try:
            transcript = item['item']['formatted']['transcript']
            if transcript != "":
                await cl.Message(content=transcript).send()
        except:
            pass
    
    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        await cl.context.emitter.send_audio_interrupt()
        
    async def handle_input_audio_transcription_completed(event):
        item = event.get("item")
        delta = event.get("delta")
        if 'transcript' in delta:
            transcript = delta['transcript']
            if transcript != "":
                await cl.Message(author="You", type="user_message", content=transcript).send()
        
    async def handle_error(event):
        logger.error(event)
        
    
    openai_realtime.on('conversation.updated', handle_conversation_updated)
    openai_realtime.on('conversation.item.completed', handle_item_completed)
    openai_realtime.on('conversation.interrupted', handle_conversation_interrupt)
    openai_realtime.on('conversation.item.input_audio_transcription.completed', handle_input_audio_transcription_completed)
    openai_realtime.on('error', handle_error)

    cl.user_session.set("openai_realtime", openai_realtime)
    coros = [openai_realtime.add_tool(tool_def, tool_handler) for tool_def, tool_handler in tools]
    await asyncio.gather(*coros)
    

system_prompt = f"""
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
- If a user asks for more than one chart, please notify the user that you can only provide one chart at a time and ask them to specify which chart they would like to see first. 

Your ultimate goal is to empower users with clear, actionable insights to navigate the financial landscape effectively.

Remember your goal is to answer the users query and provide a clear, actionable answer.  
"""

@cl.on_chat_start
async def start():
    #await cl.Message(
    #    content="Hi, I'm FinanceGPT, your personal financial advisor.  How can I help you today?. Press `P` to talk!"
    #).send()
    await setup_openai_realtime(system_prompt=system_prompt + "\n\n Get Microsoft's stock price for today?")

@cl.on_message
async def on_message(message: cl.Message):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.send_user_message_content([{ "type": 'input_text', "text": message.content}])
    else:
        await cl.Message(content="Please activate voice mode before sending messages!").send()

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Get a stock price for a publicly traded company",
            message="Get Microsoft's stock price for today?",
            icon="fas fa-chart-line"
        ),
        cl.Starter(
            label="Get the weather for a location",
            message="What is the weather in Chicago?"

        )
    ]


@cl.on_audio_start
async def on_audio_start():
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        # TODO: might want to recreate items to restore context
        # openai_realtime.create_conversation_item(item)
        await openai_realtime.connect()
        logger.info("Connected to OpenAI realtime")
        return True
    except Exception as e:
        await cl.ErrorMessage(content=f"Failed to connect to OpenAI realtime: {e}").send()
        return False

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime:            
        if openai_realtime.is_connected():
            await openai_realtime.append_input_audio(chunk.data)
        else:
            logger.info("RealtimeClient is not connected")

@cl.on_audio_end
@cl.on_chat_end
@cl.on_stop
async def on_end():
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.disconnect()