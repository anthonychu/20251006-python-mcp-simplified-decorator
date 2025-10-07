import azure.functions as func
from mcp_tool_decorator import MCPToolContext, get_mcp_tool
from typing import Annotated


app = func.FunctionApp()
mcp_tool = get_mcp_tool(app)

@mcp_tool()
def add_numbers(
    number1: Annotated[int, "The first integer to add"],
    number2: Annotated[int, "The second integer to add"]
) -> str:
    """
    Add two integers.
    """
    return str(number1 + number2)


@mcp_tool()
def greet_user(
    name: Annotated[str, "The name of the user to greet"],
    context: MCPToolContext
) -> str:
    """
    Greet a user by name.
    """
    print(context["arguments"].keys())  # Just to show that context is passed
    return f"Hello, {name}!"


@mcp_tool()
def weather(city: str, state: str) -> str:
    """
    Get the weather for a city.
    """
    # For demonstration purposes, return a dummy weather string
    return f"The weather in {city}, {state} is sunny with a high of 21°C."
