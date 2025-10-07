# Simplified MCP Tool Decorator for Azure Functions

A Python decorator that simplifies creating MCP tool triggers using Azure Functions. The decorator automatically infers the necessary tool and parameter definitions.

## Features

- **Automatic tool registration**: Converts regular Python functions into MCP tools
- **Supports basic parameter types**: `int`, `str`, `float`, `bool`
- **Flexible descriptions**: Supports custom parameter descriptions via `Annotated` types
- **Context access**: Functions can access the full MCP tool context via `MCPToolContext` parameter

## The `@mcp_tool` Decorator

The `@mcp_tool` decorator automatically creates MCP tool triggers from Python functions. It infers:

- **Tool name**: From the function name
- **Description**: From the function's docstring (first line)
- **Parameters**: From function signature with type hints
- **Parameter descriptions**: From `Annotated` type annotations

### Usage

```python
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
    A simple function to add two integers.
    """
    return str(number1 + number2)
```

### Type Mapping

The decorator maps Python types to MCP property types:

- `int` → `"integer"`
- `str` → `"string"`
- `float` → `"number"`
- `bool` → `"boolean"`
- Unknown types → `"string"` (fallback)

### Accessing Context with MCPToolContext

Functions can access the full MCP tool context by including a parameter of type `MCPToolContext`. This parameter provides access to the complete context passed to the tool, including arguments and any additional metadata.

```python
@mcp_tool()
def greet_user(
    name: Annotated[str, "The name of the user to greet"],
    context: MCPToolContext
) -> str:
    """
    Greet a user by name.
    """
    print(context["arguments"].keys())  # Access the full context
    return f"Hello, {name}!"
```

**Important notes about MCPToolContext:**
- Include a parameter with type `MCPToolContext` to access the full context
- The context is a dictionary containing the tool invocation data

### Parameter Descriptions

Use `Annotated` types to provide custom parameter descriptions:

```python
@mcp_tool()
def weather(
    city: Annotated[str, "The name of the city"],
    state: Annotated[str, "The abbreviation of the state"]
) -> str:
    """
    Get the weather for a city.
    """
    return f"The weather in {city}, {state} is sunny with a high of 21°C."
```

### Error Handling

The decorator provides comprehensive error handling:

- **JSON parsing errors**: Invalid context JSON format
- **Missing parameters**: Required function parameters not provided
- **Type errors**: Invalid parameter types
- **Runtime errors**: Exceptions during function execution

## Example Functions

Note: Examples assume the following imports:
```python
from mcp_tool_decorator import MCPToolContext, get_mcp_tool
from typing import Annotated
```

### Adding Numbers
```python
@mcp_tool()
def add_numbers(
    number1: Annotated[int, "The first integer to add"],
    number2: Annotated[int, "The second integer to add"]
) -> str:
    """
    Add two integers.
    """
    return str(number1 + number2)
```

### Greeting Users
```python
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
```

### Weather Information
```python
@mcp_tool()
def weather(city: str, state: str) -> str:
    """
    Get the weather for a city.
    """
    return f"The weather in {city}, {state} is sunny with a high of 21°C."
```
