import os
from langchain_azure_dynamic_sessions import SessionsPythonREPLTool
from langchain_core.tools import tool
from typing import Annotated


repl = SessionsPythonREPLTool(
        pool_management_endpoint=os.getenv("POOL_MANAGEMENT_ENDPOINT"),
        description="A python shell that is used for running python code.   It can be used to chart technical statistics that are returned from the get_stock_technical_indicators tool."
    )

@tool("python_repl_tool")
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."]
):
    """
    A tool that is used to execute python code to generate a chart
    """
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    
    return result